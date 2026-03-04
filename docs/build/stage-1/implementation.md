# Stage 1: Implementation Document
## Foundation + TextTiling Analyzer

**Status:** Approved for implementation (rev 2 — final review patches applied)
**Incorporates:** Gemini review, Codex review, verification findings, final review pass

---

## Review Resolutions

Changes from original plan based on triage:

| # | Finding | Resolution |
|---|---------|------------|
| 1 | `analyze()` signature too narrow for cross-analyzer aggregation | Add `context: dict \| None = None` third parameter |
| 2 | Character offset mapping unreliable (`find()` approach) | Use deterministic formatted→original index map |
| 3 | Skipped blocks create gaps in character offsets | Merge skipped tile content into preceding block |
| 4 | JSON export missing `os.makedirs` | Add `makedirs(exist_ok=True)` to all write functions |
| 5 | NLTK `stopwords` missing from dependencies | Add to conftest + document in setup |
| 6 | `setuptools.backends._legacy` wrong | Use `setuptools.build_meta` |
| 7 | BOM characters in manuscript | Strip BOM (`\uFEFF`) during text loading |
| 8 | `chapter` field default `0` vs `null` | Use `null` (filled by chapters analyzer in Stage 3) |
| 9 | Warnings have no persistence path | Add `"warnings": []` to `manifest.json` |
| 10 | Overview says Stage 1 includes coref/verb_categories | Fix overview: those are Stage 2. Stage 1 NLP = loader only |
| 11 | `notable.longest_sentences` ambiguous | Define as block IDs ranked by `max_sentence_length` |
| 12 | Slug normalization undefined | Derive from `--title` or filename; kebab-case, lowercase |
| 13 | Unicode handling untested | Add `test_unicode_handling` — smart quotes, BOM, accented chars |
| 14 | Missing failure-mode tests | Add: 0-block output, config overrides, missing NLTK data |
| 15 | `_ensure_dir()` logic broken for non-existent output dirs | Drop helper; use `os.makedirs(output_dir, exist_ok=True)` directly |
| 16 | Analyzer registry empty without explicit module import | Add `from lit_engine.analyzers import texttiling` in `__init__.py` |
| 17 | Offset mapping fallbacks contradict "exact" claim | Emit warnings on fallback; add test for degraded behavior |
| 18 | Preview normalization vs raw offset text mismatch | Note in test plan: normalize both sides when comparing |
| 19 | DoD path mismatch (`tests/` vs `engine/tests/`) | Fix to `engine/tests/fixtures/sample_text.txt` |
| 20 | Single short tile edge case untested | Add `test_single_short_tile` |

---

## File-by-File Implementation

### 1. `engine/pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "lit-engine"
version = "0.1.0"
description = "Computational stylistics engine for literary manuscripts"
requires-python = ">=3.10"
dependencies = [
    "spacy>=3.7",
    "nltk>=3.8",
    "textstat>=0.7",
    "vaderSentiment>=3.3",
    "click>=8.0",
]

[project.optional-dependencies]
charts = ["matplotlib>=3.7", "seaborn>=0.13"]
dev = ["pytest>=7.0", "pytest-cov"]

[project.scripts]
lit-engine = "lit_engine.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### 2. `engine/requirements.txt`

```
spacy>=3.7
nltk>=3.8
textstat>=0.7
vaderSentiment>=3.3
click>=8.0
pytest>=7.0
pytest-cov
```

---

### 3. `engine/src/lit_engine/__init__.py`

```python
"""lit-engine: computational stylistics for literary manuscripts."""

__version__ = "0.1.0"
```

---

### 4. `engine/src/lit_engine/config.py`

Central configuration with all tunable defaults.

```python
"""Default configuration for lit-engine analyzers."""

DEFAULT_CONFIG: dict = {
    # TextTiling
    "texttiling_w": 40,
    "texttiling_k": 20,
    "texttiling_fallback_w": 20,
    "texttiling_fallback_k": 10,
    "texttiling_min_words": 30,
    "texttiling_min_alpha": 20,

    # MATTR
    "mattr_window": 50,

    # spaCy
    "spacy_model": "en_core_web_lg",

    # Coreference (used in Stage 2)
    "coref_enabled": True,

    # Characters (used in Stage 2)
    "characters": [],
    "character_genders": {},
    "max_auto_characters": 8,
    "min_character_mentions": 10,

    # Stop verbs (shared concern — used by agency and chapter analyzers)
    "stop_verbs": frozenset({
        "be", "have", "do", "say", "go", "get", "seem", "make", "let",
        "come", "take", "give", "keep", "put", "set", "find", "tell",
        "become", "leave", "show", "try", "call", "ask", "use", "may",
        "will", "would", "could", "should", "might", "shall", "must", "can",
    }),
}


def merge_config(overrides: dict | None = None) -> dict:
    """Merge user overrides into default config. Returns a new dict."""
    config = dict(DEFAULT_CONFIG)
    if overrides:
        config.update(overrides)
    return config
```

---

### 5. `engine/src/lit_engine/analyzers/__init__.py`

Base analyzer interface. This is the contract all 8 analyzers implement.

```python
"""Base analyzer interface and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AnalyzerResult:
    """Standard wrapper for analyzer output."""
    analyzer_name: str
    data: dict                              # JSON-serializable payload
    warnings: list[str] = field(default_factory=list)


class Analyzer(ABC):
    """Base interface for all analyzers."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        """
        Accept raw text + config, return structured result.

        Args:
            text: Raw manuscript text (BOM-stripped, ready to process).
            config: Merged configuration dict (see config.py).
            context: Results from previously-run analyzers, keyed by
                     analyzer name. None for analyzers with no dependencies.
                     Example: {"texttiling": <AnalyzerResult>, ...}

        Returns:
            AnalyzerResult with JSON-serializable `data` dict.
        """
        ...

    def requires(self) -> list[str]:
        """List analyzer names this depends on (for execution ordering)."""
        return []


# Analyzer registry — populated by each analyzer module on import
_REGISTRY: dict[str, type[Analyzer]] = {}


def register(cls: type[Analyzer]) -> type[Analyzer]:
    """Decorator to register an analyzer class."""
    _REGISTRY[cls.name] = cls
    return cls


def get_analyzer(name: str) -> Analyzer:
    """Instantiate a registered analyzer by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Unknown analyzer: {name!r}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]()


def list_analyzers() -> list[str]:
    """Return names of all registered analyzers."""
    return sorted(_REGISTRY.keys())


# Import analyzer modules so their @register decorators execute.
# Each new analyzer module added in later stages gets a line here.
from lit_engine.analyzers import texttiling  # noqa: F401
```

**Key design decisions:**
- `context: dict | None = None` — resolves Codex's blocker. Stage 1 analyzers ignore it; Stage 3 analyzers (`chapters`, `silence`) use it to read prior results without re-computation or fragile file reads.
- `register()` decorator — analyzers self-register on import, keeping the registry decoupled.
- `AnalyzerResult` wraps a dict — improves on spec's raw `-> dict` by giving us a place for warnings. Spec will be updated to match.

---

### 6. `engine/src/lit_engine/nlp/__init__.py`

Empty init.

```python
"""NLP utilities for lit-engine."""
```

---

### 7. `engine/src/lit_engine/nlp/loader.py`

Lazy spaCy model loading. Not invoked in Stage 1 (TextTiling uses NLTK), but the scaffolding is ready for Stage 2.

```python
"""Lazy spaCy model loading with caching."""

from functools import lru_cache
import spacy


@lru_cache(maxsize=1)
def load_spacy(model_name: str = "en_core_web_lg") -> spacy.Language:
    """
    Load a spaCy model, caching the result.

    Falls back to en_core_web_sm if the requested model isn't installed.
    Raises RuntimeError if no model can be loaded.
    """
    try:
        return spacy.load(model_name)
    except OSError:
        pass

    fallback = "en_core_web_sm"
    try:
        return spacy.load(fallback)
    except OSError:
        raise RuntimeError(
            f"No spaCy model available. Install one with: "
            f"python -m spacy download {model_name}"
        )


def parse_document(
    text: str,
    model_name: str = "en_core_web_lg",
) -> "spacy.tokens.Doc":
    """Parse text into a spaCy Doc, handling max_length for long manuscripts."""
    nlp = load_spacy(model_name)
    nlp.max_length = max(nlp.max_length, len(text) + 100_000)
    return nlp(text)
```

---

### 8. `engine/src/lit_engine/analyzers/texttiling.py`

The core analyzer. Refactored from `analyze_psychology()` in `specimen_analysis_v2.py`.

#### 8a. MATTR function

```python
def mattr(tokens: list[str], window_length: int = 50) -> float:
    """
    Moving Average Type-Token Ratio.

    Slides a window across the token list and averages the TTR
    at each position. Length-independent unlike naive TTR.
    """
    if not tokens:
        return 0.0

    if len(tokens) < window_length:
        return len(set(tokens)) / len(tokens)

    ttrs = []
    for i in range(len(tokens) - window_length + 1):
        window = tokens[i : i + window_length]
        ttrs.append(len(set(window)) / window_length)

    return sum(ttrs) / len(ttrs)
```

Preserved exactly from `specimen_analysis_v2.py` lines 35–49. No changes needed.

#### 8b. Text preparation and offset mapping

This is the trickiest part of Stage 1. TextTiling requires double-newline paragraph breaks, but we need to map tile positions back to the original text.

**Strategy: Build a character index map during formatting.**

```python
def prepare_text(raw_text: str) -> tuple[str, str, list[int]]:
    """
    Prepare text for TextTiling and build an offset map.

    Returns:
        clean_text: BOM-stripped original text (for offset references).
        formatted_text: Double-newlined text for TextTiling.
        offset_map: Maps each index in formatted_text to its index
                     in clean_text. offset_map[formatted_idx] = clean_idx.
                     Inserted characters map to the preceding clean index.
    """
    # Strip BOM
    clean = raw_text.lstrip("\uFEFF")
    bom_offset = len(raw_text) - len(clean)

    # Build formatted text + index map
    formatted_chars: list[str] = []
    offset_map: list[int] = []

    for i, ch in enumerate(clean):
        formatted_chars.append(ch)
        offset_map.append(i)

        if ch == "\n":
            # Insert an extra newline (TextTiling needs paragraph breaks)
            formatted_chars.append("\n")
            offset_map.append(i)  # inserted char maps to same original position

    formatted = "".join(formatted_chars)
    return clean, formatted, offset_map
```

After TextTiling tokenizes the formatted text, we map tile boundaries back:

```python
def map_tile_offsets(
    formatted_text: str,
    tiles: list[str],
    offset_map: list[int],
    clean_text: str,
) -> tuple[list[tuple[int, int]], list[str]]:
    """
    Map TextTiling tile boundaries back to clean_text character offsets.

    Returns:
        offsets: list of (start_char, end_char) tuples in clean_text coordinates.
        warnings: list of warnings if fallback paths were used.
    """
    offsets = []
    warnings: list[str] = []
    search_from = 0

    for i, tile in enumerate(tiles):
        # Find this tile in the formatted text
        # Tiles are substrings of formatted_text (TextTiling splits it)
        tile_start_formatted = formatted_text.find(tile, search_from)

        if tile_start_formatted == -1:
            # Fallback 1: stripped tile might differ slightly
            stripped = tile.strip()
            tile_start_formatted = formatted_text.find(stripped, search_from)
            if tile_start_formatted != -1:
                warnings.append(
                    f"Tile {i}: exact match failed, matched after stripping whitespace. "
                    f"Offset may be approximate."
                )

        if tile_start_formatted == -1:
            # Fallback 2: use sequential position (degraded — offsets are approximate)
            if offsets:
                tile_start_formatted = search_from
            else:
                tile_start_formatted = 0
            warnings.append(
                f"Tile {i}: could not locate in formatted text. "
                f"Using sequential offset (approximate)."
            )

        tile_end_formatted = tile_start_formatted + len(tile)

        # Clamp to offset_map bounds
        start_idx = min(tile_start_formatted, len(offset_map) - 1)
        end_idx = min(tile_end_formatted - 1, len(offset_map) - 1)

        start_char = offset_map[start_idx]
        end_char = offset_map[end_idx] + 1  # exclusive end

        offsets.append((start_char, end_char))
        search_from = tile_end_formatted

    return offsets, warnings
```

**Why this works:** TextTiling's `tokenize()` returns substrings of the input text. Since we only inserted extra `\n` characters (never removed or altered existing characters), every tile is findable in `formatted_text` via `find()` with a forward-only search position. The `offset_map` then deterministically translates each formatted-text index back to the clean-text index. The primary path should always succeed; fallbacks exist as safety nets and emit warnings if hit.

**Why this is better than the original plan:** No fuzzy matching on first-50-chars. No approximate sequential estimation. The index map is exact. Fallback paths are explicitly degraded behavior, warned about, and testable.

#### 8c. Block building with merged skipped tiles

When tiles are too short (< `min_words`), their content is merged into the preceding block rather than dropped. This ensures contiguous coverage of the manuscript text.

```python
def build_blocks(
    tiles: list[str],
    tile_offsets: list[tuple[int, int]],
    clean_text: str,
    config: dict,
) -> tuple[list[dict], list[str]]:
    """
    Process tiles into blocks with metrics.

    Short tiles are merged into the preceding block to ensure
    contiguous character coverage (no gaps for the block explorer).

    Returns:
        blocks: List of block dicts matching analysis.json schema.
        warnings: List of warning messages.
    """
    min_words = config.get("texttiling_min_words", 30)
    min_alpha = config.get("texttiling_min_alpha", 20)
    mattr_window = config.get("mattr_window", 50)
    warnings: list[str] = []

    raw_blocks: list[dict] = []  # before merging

    for i, (tile, (start_char, end_char)) in enumerate(zip(tiles, tile_offsets)):
        text_content = tile.replace("\n", " ").strip()
        words = word_tokenize(text_content)
        alpha_words = [w.lower() for w in words if w.isalpha()]

        raw_blocks.append({
            "tile_index": i,
            "start_char": start_char,
            "end_char": end_char,
            "text_content": text_content,
            "words": words,
            "alpha_words": alpha_words,
        })

    # Merge pass: fold short blocks into their predecessor
    merged: list[dict] = []
    for block in raw_blocks:
        is_short = (
            len(block["words"]) < min_words
            or len(block["alpha_words"]) < min_alpha
        )

        if is_short and merged:
            # Merge into preceding block
            prev = merged[-1]
            prev["end_char"] = block["end_char"]
            prev["text_content"] += " " + block["text_content"]
            prev["words"].extend(block["words"])
            prev["alpha_words"].extend(block["alpha_words"])
        elif is_short and not merged:
            # First block is short — keep it, it will be merged forward
            # when the next valid block arrives, or kept if all blocks are short
            merged.append(block)
        else:
            # Check if previous block was a kept-short first block
            if merged and len(merged[-1].get("alpha_words", [])) < min_alpha:
                # Merge the short first block into this one
                prev = merged[-1]
                block["start_char"] = prev["start_char"]
                block["text_content"] = prev["text_content"] + " " + block["text_content"]
                block["words"] = prev["words"] + block["words"]
                block["alpha_words"] = prev["alpha_words"] + block["alpha_words"]
                merged[-1] = block
            else:
                merged.append(block)

    # Compute metrics for each merged block
    blocks: list[dict] = []
    for block_data in merged:
        alpha_words = block_data["alpha_words"]
        text_content = block_data["text_content"]
        sentences = sent_tokenize(text_content)

        if not sentences or not alpha_words:
            warnings.append(
                f"Tile {block_data['tile_index']}: empty after processing, skipped"
            )
            continue

        sent_lengths = [
            len([w for w in word_tokenize(s) if w.isalpha()])
            for s in sentences
        ]

        mattr_score = mattr(alpha_words, window_length=min(mattr_window, len(alpha_words)))

        # Readability metrics (textstat wants raw text)
        flesch_ease = textstat.flesch_reading_ease(text_content)
        flesch_grade = textstat.flesch_kincaid_grade(text_content)
        fog = textstat.gunning_fog(text_content)

        block_id = len(blocks) + 1  # 1-indexed, sequential

        blocks.append({
            "id": block_id,
            "tile_index": block_data["tile_index"],
            "start_char": block_data["start_char"],
            "end_char": block_data["end_char"],
            "word_count": len(alpha_words),
            "sentence_count": len(sentences),
            "metrics": {
                "mattr": round(mattr_score, 4),
                "avg_sentence_length": round(len(alpha_words) / len(sentences), 1),
                "max_sentence_length": max(sent_lengths) if sent_lengths else 0,
                "flesch_ease": round(flesch_ease, 1),
                "flesch_grade": round(flesch_grade, 1),
                "gunning_fog": round(fog, 1),
            },
            "sentence_lengths": sent_lengths,
            "preview": text_content[:120] + ("..." if len(text_content) > 120 else ""),
            "chapter": None,  # filled by chapters analyzer in Stage 3
        })

    return blocks, warnings
```

#### 8d. Notable blocks computation

**Definition lock (resolves Codex concern):**
- `longest_sentences` = block IDs ranked by `max_sentence_length` (the single longest sentence in the block)
- `highest_mattr` = block IDs ranked by `metrics.mattr`
- `highest_fog` = block IDs ranked by `metrics.gunning_fog`
- `shortest_sentences` = block IDs ranked by `avg_sentence_length` ascending (most staccato prose)

```python
def compute_notable(blocks: list[dict], top_n: int = 5) -> dict:
    """Compute notable block rankings."""
    by_max_sent = sorted(blocks, key=lambda b: b["metrics"]["max_sentence_length"], reverse=True)
    by_mattr = sorted(blocks, key=lambda b: b["metrics"]["mattr"], reverse=True)
    by_fog = sorted(blocks, key=lambda b: b["metrics"]["gunning_fog"], reverse=True)
    by_avg_sent_asc = sorted(blocks, key=lambda b: b["metrics"]["avg_sentence_length"])

    return {
        "longest_sentences": [b["id"] for b in by_max_sent[:top_n]],
        "highest_mattr": [b["id"] for b in by_mattr[:top_n]],
        "highest_fog": [b["id"] for b in by_fog[:top_n]],
        "shortest_sentences": [b["id"] for b in by_avg_sent_asc[:top_n]],
    }
```

#### 8e. The analyzer class

```python
import textstat
from nltk.tokenize import TextTilingTokenizer, sent_tokenize, word_tokenize

from lit_engine.analyzers import Analyzer, AnalyzerResult, register


@register
class TextTilingAnalyzer(Analyzer):
    name = "texttiling"
    description = "Semantic segmentation via TextTiling with MATTR and readability metrics"

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # Prepare text with offset mapping
        clean_text, formatted_text, offset_map = prepare_text(text)

        # TextTiling with fallback
        w = config.get("texttiling_w", 40)
        k = config.get("texttiling_k", 20)
        fallback_w = config.get("texttiling_fallback_w", 20)
        fallback_k = config.get("texttiling_fallback_k", 10)

        tt = TextTilingTokenizer(w=w, k=k)
        try:
            tiles = tt.tokenize(formatted_text)
        except ValueError as e:
            warnings.append(
                f"TextTiling failed with w={w}, k={k}: {e}. "
                f"Falling back to w={fallback_w}, k={fallback_k}."
            )
            tt = TextTilingTokenizer(w=fallback_w, k=fallback_k)
            tiles = tt.tokenize(formatted_text)

        if not tiles:
            return AnalyzerResult(
                analyzer_name=self.name,
                data={
                    "parameters": {"w": w, "k": k, "mattr_window": config.get("mattr_window", 50)},
                    "total_blocks": 0,
                    "blocks": [],
                    "notable": {
                        "longest_sentences": [],
                        "highest_mattr": [],
                        "highest_fog": [],
                        "shortest_sentences": [],
                    },
                },
                warnings=warnings + ["TextTiling produced 0 tiles."],
            )

        # Map tile offsets back to clean text
        tile_offsets, offset_warnings = map_tile_offsets(formatted_text, tiles, offset_map, clean_text)
        warnings.extend(offset_warnings)

        # Build blocks with metrics (merging short tiles)
        blocks, block_warnings = build_blocks(tiles, tile_offsets, clean_text, config)
        warnings.extend(block_warnings)

        # Notable rankings
        notable = compute_notable(blocks)

        return AnalyzerResult(
            analyzer_name=self.name,
            data={
                "parameters": {
                    "w": w,
                    "k": k,
                    "mattr_window": config.get("mattr_window", 50),
                },
                "total_blocks": len(blocks),
                "blocks": blocks,
                "notable": notable,
            },
            warnings=warnings,
        )
```

---

### 9. `engine/src/lit_engine/output/__init__.py`

```python
"""Output utilities for lit-engine."""
```

---

### 10. `engine/src/lit_engine/output/json_export.py`

All write functions create directories as needed.

```python
"""Canonical JSON schema writer for lit-engine output."""

import json
import os
import shutil
from datetime import datetime, timezone

from lit_engine import __version__


def write_json(output_dir: str, filename: str, data: dict) -> str:
    """Write a JSON file to the output directory. Returns the path written."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def write_manifest(output_dir: str, manifest: dict) -> str:
    """Write manifest.json."""
    return write_json(output_dir, "manifest.json", manifest)


def write_analysis(output_dir: str, data: dict) -> str:
    """Write analysis.json (TextTiling blocks)."""
    return write_json(output_dir, "analysis.json", data)


def copy_manuscript(source_path: str, output_dir: str) -> str:
    """Copy manuscript to output dir for block reading. Returns dest path."""
    os.makedirs(output_dir, exist_ok=True)
    dest = os.path.join(output_dir, "manuscript.txt")
    shutil.copy2(source_path, dest)
    return dest


def slugify(title: str) -> str:
    """
    Convert a title to a URL-safe slug.

    Rules:
    - Lowercase
    - Replace spaces and underscores with hyphens
    - Strip non-alphanumeric characters (except hyphens)
    - Collapse multiple hyphens
    - Strip leading/trailing hyphens
    """
    import re
    slug = title.lower()
    slug = re.sub(r"[_ ]+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def build_manifest(
    title: str,
    slug: str,
    source_file: str,
    word_count: int,
    char_count: int,
    character_list: list[str],
    analyzers_run: list[str],
    parameters: dict,
    chapter_count: int = 0,
    warnings: list[str] | None = None,
) -> dict:
    """Build a manifest dict matching the canonical schema."""
    return {
        "title": title,
        "slug": slug,
        "source_file": os.path.basename(source_file),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "engine_version": __version__,
        "word_count": word_count,
        "char_count": char_count,
        "chapter_count": chapter_count,
        "character_list": character_list,
        "analyzers_run": analyzers_run,
        "parameters": parameters,
        "warnings": warnings or [],
    }
```

---

### 11. `engine/src/lit_engine/cli.py`

Skeleton CLI for Stage 1. Enough to run the TextTiling analyzer and produce output. Full orchestration in Stage 4.

```python
"""CLI entry point for lit-engine."""

import os
import click

from lit_engine import __version__
from lit_engine.config import merge_config
from lit_engine.analyzers import list_analyzers, get_analyzer
from lit_engine.output.json_export import (
    build_manifest, write_manifest, write_analysis, copy_manuscript, slugify,
)


@click.group()
@click.version_option(__version__)
def main():
    """lit-engine: computational stylistics for literary manuscripts."""
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--title", "-t", default=None, help="Manuscript title (for slug)")
@click.option("--only", default=None, help="Comma-separated analyzer names")
@click.option("--tt-window", default=40, type=int, help="TextTiling window size (w)")
@click.option("--tt-smoothing", default=20, type=int, help="TextTiling smoothing (k)")
def analyze(file_path, output, title, only, tt_window, tt_smoothing):
    """Analyze a manuscript file."""
    # Read manuscript
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Strip BOM
    text = text.lstrip("\uFEFF")

    # Derive title and slug
    if title is None:
        title = os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").title()
    slug = slugify(title)

    # Output directory
    if output is None:
        output = os.path.join("shared", "analyses", slug)

    # Build config
    config = merge_config({
        "texttiling_w": tt_window,
        "texttiling_k": tt_smoothing,
    })

    # Determine which analyzers to run
    if only:
        analyzer_names = [n.strip() for n in only.split(",")]
    else:
        analyzer_names = list_analyzers()

    # Run analyzers
    click.echo(f"Analyzing: {file_path}")
    click.echo(f"Output:    {output}")
    click.echo(f"Title:     {title} (slug: {slug})")
    click.echo(f"Analyzers: {', '.join(analyzer_names)}")
    click.echo()

    all_warnings: list[str] = []
    results = {}

    for name in analyzer_names:
        try:
            analyzer = get_analyzer(name)
        except KeyError:
            click.echo(f"  WARNING: Unknown analyzer '{name}', skipping.")
            all_warnings.append(f"Unknown analyzer: {name}")
            continue

        click.echo(f"  Running {name}...")
        result = analyzer.analyze(text, config, context=results)
        results[name] = result

        if result.warnings:
            for w in result.warnings:
                click.echo(f"    WARNING: {w}")
            all_warnings.extend(result.warnings)

    # Write output
    click.echo()
    click.echo("Writing output...")

    # analysis.json (from texttiling)
    if "texttiling" in results:
        path = write_analysis(output, results["texttiling"].data)
        click.echo(f"  {path}")

    # Copy manuscript
    ms_path = copy_manuscript(file_path, output)
    click.echo(f"  {ms_path}")

    # Word/char count from clean text
    word_count = len(text.split())
    char_count = len(text)

    # Manifest
    manifest = build_manifest(
        title=title,
        slug=slug,
        source_file=file_path,
        word_count=word_count,
        char_count=char_count,
        character_list=config["characters"],
        analyzers_run=list(results.keys()),
        parameters={
            "texttiling_w": tt_window,
            "texttiling_k": tt_smoothing,
            "spacy_model": config["spacy_model"],
            "coref_enabled": config["coref_enabled"],
            "mattr_window": config["mattr_window"],
        },
        warnings=all_warnings,
    )
    path = write_manifest(output, manifest)
    click.echo(f"  {path}")

    click.echo()
    click.echo("Done.")


@main.command("list-analyzers")
def list_analyzers_cmd():
    """List available analyzers."""
    for name in list_analyzers():
        analyzer = get_analyzer(name)
        click.echo(f"  {name:20s} {analyzer.description}")


if __name__ == "__main__":
    main()
```

---

### 12. Test Fixture: `engine/tests/fixtures/sample_text.txt`

Craft a ~2000-word synthetic literary excerpt that exercises:
- Multiple paragraphs with clear topic shifts (for TextTiling)
- Varied sentence lengths (3-word staccato to 80+ word flowing)
- Smart quotes (`\u201c` `\u201d`), smart apostrophes (`\u2019`), em dashes (`\u2014`), accented characters (`é`)
- BOM at start (`\uFEFF`)
- Dialogue mixed with narration
- At least two named characters
- At least 3 natural topic boundaries

**We will write this fixture as the first step of implementation.** It should be original (not copied from the manuscript) to keep tests independent.

---

### 13. Test Conftest: `engine/tests/conftest.py`

```python
"""Shared test fixtures and NLTK data setup."""

import os
import pytest
import nltk


def pytest_configure(config):
    """Ensure NLTK data is available before any tests run."""
    for resource in ("punkt_tab", "stopwords"):
        try:
            nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}")
        except LookupError:
            nltk.download(resource, quiet=True)


@pytest.fixture
def sample_text():
    """Load the test fixture text."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_text.txt")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def default_config():
    """Return default config for testing."""
    from lit_engine.config import DEFAULT_CONFIG
    return dict(DEFAULT_CONFIG)
```

---

### 14. Test Plan (Red-Green)

All tests are written **before** implementation. They should fail, then pass one by one as code is written.

#### `engine/tests/test_mattr.py`

```
test_mattr_basic                — [0.5, 0.5, 0.8, 0.8] with window=2 → known value
test_mattr_empty                — [] → 0.0
test_mattr_uniform              — ["the"] * 100 → low value (close to 1/window)
test_mattr_all_unique           — 100 unique tokens → close to 1.0
test_mattr_short_text           — 10 tokens, window=50 → returns naive TTR
test_mattr_window_equals_length — len(tokens) == window → single TTR value
```

#### `engine/tests/test_texttiling.py`

```
test_tiles_produced             — fixture text produces > 1 block
test_block_schema               — each block has all required keys: id, tile_index,
                                  start_char, end_char, word_count, sentence_count,
                                  metrics, sentence_lengths, preview, chapter
test_block_ids_sequential       — IDs are 1, 2, 3, ... with no gaps
test_block_offsets_contiguous   — block N end_char >= block N+1 start_char (no gaps)
test_block_offsets_valid        — start_char < end_char for every block
test_block_preview_matches_text — preview content matches clean_text[start_char:start_char+120]
                                  after normalizing whitespace on both sides (\n → space)
test_metrics_in_range           — MATTR in [0,1], Fog > 0, sentence_count > 0
test_notable_blocks_exist       — notable dict has all 4 keys
test_notable_ids_valid          — all IDs in notable lists exist in blocks
test_fallback_window            — with w=999, k=999 on short text → falls back, warns
test_zero_blocks                — very short text → returns valid empty-blocks structure
test_config_overrides           — different w/k values produce different block counts
test_unicode_handling           — text with smart quotes, BOM, accented chars →
                                  offsets don't drift, preview is readable
test_single_short_tile          — manuscript that produces exactly 1 short tile →
                                  still returns 1 block (not 0), valid schema
test_offset_no_fallback_on_fixture — fixture text maps all tiles without fallback warnings
test_result_type                — returns AnalyzerResult with analyzer_name="texttiling"
```

#### `engine/tests/test_json_export.py`

```
test_manifest_schema            — all required fields present in built manifest
test_manifest_timestamp         — analyzed_at is valid ISO 8601 with timezone
test_manifest_warnings          — warnings list persisted in manifest
test_analysis_roundtrip         — write then read produces identical data
test_output_dir_created         — write_analysis creates directory if missing
test_manuscript_copied          — copy_manuscript creates manuscript.txt
test_slugify                    — "The Specimen V2" → "the-specimen-v2"
test_slugify_special_chars      — "Café Union" → "caf-union" (or "cafe-union")
test_slugify_underscores        — "the_specimen" → "the-specimen"
```

#### `engine/tests/test_prepare_text.py`

```
test_bom_stripped               — BOM at start removed, offset map correct
test_double_bom                 — two BOMs stripped (matches real manuscript)
test_newlines_doubled           — single \n becomes \n\n in formatted
test_offset_map_length          — offset_map length == len(formatted_text)
test_offset_map_identity_no_newlines — text without \n: map is identity [0,1,2,...]
test_roundtrip_via_map          — for each i in formatted, clean[offset_map[i]] makes sense
```

---

### 15. Implementation Order

Execute in this order (each step: write failing tests → implement → tests pass):

1. **Fixture text** — write `sample_text.txt`
2. **Config** — `config.py` (trivial, no tests needed)
3. **Base analyzer** — `analyzers/__init__.py` (test: import, instantiate)
4. **MATTR** — the pure function, tested in isolation
5. **Text preparation** — `prepare_text()` + `map_tile_offsets()`, tested with offset assertions
6. **Block building** — `build_blocks()` + `compute_notable()`, tested with schema checks
7. **TextTiling analyzer** — the full `TextTilingAnalyzer.analyze()`, integration tested
8. **JSON export** — `json_export.py`, tested with roundtrip + directory creation
9. **NLP loader** — `nlp/loader.py` (tested minimally — full test in Stage 2)
10. **CLI** — `cli.py`, tested via `click.testing.CliRunner`
11. **End-to-end** — run against fixture, verify complete output directory

---

### 16. Definition of Done

- [ ] `pip install -e ./engine` succeeds
- [ ] `pytest engine/tests/ -v` — all tests green
- [ ] `lit-engine analyze engine/tests/fixtures/sample_text.txt -o /tmp/test-analysis` produces:
  - `manifest.json` with all required fields
  - `analysis.json` matching schema
  - `manuscript.txt` copy
- [ ] `lit-engine analyze ~/Documents/lit-analysis/the_specimen_v2.txt` produces valid output with ~200+ blocks
- [ ] Block offsets verified: `manuscript.txt[start_char:end_char]` produces readable text for every block
- [ ] No warnings on the primary manuscript (fallback not triggered)
- [ ] `lit-engine list-analyzers` shows `texttiling`

---

### 17. Spec Updates Required

After Stage 1 implementation, update `spec.md`:
1. `Analyzer.analyze()` returns `AnalyzerResult` (not raw dict)
2. `analyze()` signature includes `context: dict | None = None`
3. `manifest.json` schema: add `"warnings": []` field
4. `analysis.json` schema: `"chapter"` field is `null` (not `0`) until chapters analyzer runs
5. `notable.longest_sentences`: defined as ranked by `max_sentence_length`
