# Stage 1: Foundation + TextTiling Analyzer
## Detailed Build Plan

---

## Objective

Build the engine package skeleton and the first (and most critical) analyzer: TextTiling with MATTR and readability metrics. After this stage, we can run the TextTiling analyzer against a manuscript and get `analysis.json` + `manifest.json` as output — the foundation that every subsequent analyzer and the entire frontend depend on.

---

## 1. Package Structure

Create the full `engine/` directory tree:

```
engine/
├── pyproject.toml
├── requirements.txt
├── src/
│   └── lit_engine/
│       ├── __init__.py          ← version string, public API
│       ├── cli.py               ← skeleton only (full CLI is Stage 4)
│       ├── config.py            ← defaults, stop verbs, parameters
│       ├── analyzers/
│       │   ├── __init__.py      ← analyzer registry + base class
│       │   └── texttiling.py    ← TextTiling + MATTR + readability
│       ├── nlp/
│       │   ├── __init__.py
│       │   └── loader.py        ← lazy spaCy model loading
│       └── output/
│           ├── __init__.py
│           └── json_export.py   ← canonical JSON schema writer
└── tests/
    ├── __init__.py
    ├── conftest.py              ← shared fixtures
    ├── test_texttiling.py
    ├── test_mattr.py
    ├── test_json_export.py
    └── fixtures/
        └── sample_text.txt      ← short excerpt for fast testing
```

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

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
```

### requirements.txt

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

## 2. Base Analyzer Interface

In `analyzers/__init__.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class AnalyzerResult:
    """Standard wrapper for analyzer output."""
    analyzer_name: str
    data: dict                    # JSON-serializable payload
    warnings: list[str] = field(default_factory=list)

class Analyzer(ABC):
    """Base interface for all analyzers."""

    name: str
    description: str
    requires_spacy: bool = False
    requires_nltk: bool = False

    @abstractmethod
    def analyze(self, text: str, config: dict) -> AnalyzerResult:
        """
        Accept raw text + config, return structured result.
        The `data` dict becomes this analyzer's section of the output JSON.
        """
        ...

    def requires(self) -> list[str]:
        """List other analyzer names this depends on (for ordering)."""
        return []
```

**Design decisions:**
- `AnalyzerResult` wrapper gives us a consistent return type with room for warnings (e.g., "TextTiling fell back to smaller window")
- `requires()` enables dependency ordering in Stage 4
- `config: dict` keeps the interface simple — each analyzer picks what it needs from the config

---

## 3. Config Module

`config.py` holds all tunable defaults:

```python
DEFAULT_CONFIG = {
    # TextTiling
    "texttiling_w": 40,
    "texttiling_k": 20,
    "texttiling_min_words": 30,
    "texttiling_min_alpha": 20,

    # MATTR
    "mattr_window": 50,

    # spaCy
    "spacy_model": "en_core_web_lg",

    # Coreference
    "coref_enabled": True,

    # Characters (empty = auto-detect)
    "characters": [],
    "character_genders": {},
    "max_auto_characters": 8,
    "min_character_mentions": 10,

    # Stop verbs (excluded from agency analysis)
    "stop_verbs": frozenset({
        "be", "have", "do", "say", "go", "get", "seem", "make", "let",
        "come", "take", "give", "keep", "put", "set", "find", "tell",
        "become", "leave", "show", "try", "call", "ask", "use", "may",
        "will", "would", "could", "should", "might", "shall", "must", "can",
    }),
}
```

**Note:** `stop_verbs` lives in config (not in the agency analyzer) because it's a shared concern — other analyzers (like chapters) may also need to filter verbs.

---

## 4. NLP Loader

`nlp/loader.py` — lazy spaCy loading, since it's expensive (~500MB model):

```python
import spacy
from functools import lru_cache

@lru_cache(maxsize=1)
def load_spacy(model_name: str = "en_core_web_lg") -> spacy.Language:
    """Load spaCy model once, cache for reuse across analyzers."""
    try:
        nlp = spacy.load(model_name)
    except OSError:
        fallback = "en_core_web_sm"
        # Could log a warning here
        nlp = spacy.load(fallback)
    return nlp

def parse_document(text: str, model_name: str = "en_core_web_lg") -> spacy.tokens.Doc:
    """Parse text into a spaCy Doc, handling max_length."""
    nlp = load_spacy(model_name)
    nlp.max_length = max(nlp.max_length, len(text) + 100_000)
    return nlp(text)
```

**Design decision:** Single `lru_cache` ensures the model loads only once even if multiple analyzers need spaCy. The `parse_document` helper handles the `max_length` issue that always bites with novel-length text.

---

## 5. TextTiling Analyzer

`analyzers/texttiling.py` — refactored from `analyze_psychology()`:

### Core logic (preserving the working algorithm):

1. Read raw text
2. Format for TextTiling (double newlines for paragraph detection)
3. Run `TextTilingTokenizer(w=config.w, k=config.k)` with fallback
4. For each tile:
   - Skip if < `min_words` or < `min_alpha` words
   - Compute MATTR over alpha-only tokens
   - Count sentences, compute lengths
   - Run textstat: `flesch_reading_ease`, `flesch_kincaid_grade`, `gunning_fog`
   - Record character offsets in original text (for block reader)
5. Compute notable blocks (top 5 by various metrics)
6. Return `AnalyzerResult` with data matching `analysis.json` schema

### Changes from existing code:

| Existing | New | Why |
|----------|-----|-----|
| Stores `raw_text` in block dict | Store `start_char` / `end_char` offsets | Frontend reads from `manuscript.txt` by offset — no need to duplicate full text in JSON |
| Returns list of dicts | Returns `AnalyzerResult` | Consistent interface |
| Prints summary table | Emits structured data (CLI can print if verbose) | Separation of concerns |
| Saves charts | Dropped | Explorer handles visualization |
| No chapter assignment | Each block gets a `chapter` field | Filled by chapters analyzer later, defaults to `null` |

### Character offset tracking:

The existing code doesn't track where each tile sits in the original text. We need this for the block reader feature (click chart → see passage). Strategy:

```python
# After TextTiling tokenization, map tiles back to original text
offset = 0
for tile in tiles:
    # Find this tile's content in the original text
    clean = tile.strip()
    # Search from current offset forward
    start = text.find(clean[:50], offset)  # match on first 50 chars
    if start == -1:
        start = offset  # fallback: use sequential offset
    end = start + len(clean)
    block["start_char"] = start
    block["end_char"] = end
    offset = end
```

**Risk:** TextTiling reformats text (double newlines), so the tile content won't be an exact substring of the original. We need a more robust approach — possibly tracking character positions through the formatting step, or doing a fuzzy search. This is the trickiest part of Stage 1.

**Proposed solution:** Instead of trying to map back after the fact, maintain a character offset map during the formatting step:

```python
# Before TextTiling: record original positions
original_text = text
formatted = text.replace('\n', '\n\n')

# After tiling: use cumulative word count to estimate position
# Each block's word_count lets us walk through the original text
# and assign approximate byte ranges.
```

We may need to iterate on this. The tests should verify that `manuscript.txt[start_char:end_char]` produces readable text that matches the block's preview.

---

## 6. JSON Export

`output/json_export.py` — writes the canonical schema:

```python
import json
import os
from datetime import datetime, timezone

def write_manifest(output_dir: str, manifest: dict) -> None:
    """Write manifest.json."""
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

def write_analysis(output_dir: str, data: dict) -> None:
    """Write analysis.json (TextTiling blocks)."""
    path = os.path.join(output_dir, "analysis.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
) -> dict:
    """Build a manifest dict matching the canonical schema."""
    return {
        "title": title,
        "slug": slug,
        "source_file": source_file,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "engine_version": "0.1.0",
        "word_count": word_count,
        "char_count": char_count,
        "chapter_count": chapter_count,
        "character_list": character_list,
        "analyzers_run": analyzers_run,
        "parameters": parameters,
    }

def copy_manuscript(source_path: str, output_dir: str) -> None:
    """Copy manuscript to output dir for block reading."""
    import shutil
    dest = os.path.join(output_dir, "manuscript.txt")
    shutil.copy2(source_path, dest)
```

---

## 7. CLI Skeleton

`cli.py` — minimal for Stage 1, full implementation in Stage 4:

```python
import click
import os

@click.group()
def main():
    """lit-engine: computational stylistics for literary manuscripts."""
    pass

@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Output directory")
@click.option("--only", default=None, help="Comma-separated analyzer names")
@click.option("--tt-window", default=40, type=int, help="TextTiling window size")
@click.option("--tt-smoothing", default=20, type=int, help="TextTiling smoothing")
def analyze(file_path, output, only, tt_window, tt_smoothing):
    """Analyze a manuscript."""
    # Stage 1: only texttiling runs
    # Stage 4: full orchestration
    click.echo(f"Analyzing {file_path}...")

if __name__ == "__main__":
    main()
```

---

## 8. Test Fixture

`tests/fixtures/sample_text.txt` — a short literary excerpt (~2000 words) with:
- Multiple paragraphs (for TextTiling to segment)
- Varied sentence lengths (for readability metrics)
- At least 2-3 natural topic shifts (for meaningful tile boundaries)
- Some dialogue and character names (for later stages)

We'll craft this from public domain text or write a synthetic sample that exercises all the edge cases.

---

## 9. Test Plan (Red-Green)

### test_mattr.py
```
test_mattr_basic               — known input/output for a small token list
test_mattr_short_text           — text shorter than window returns naive TTR
test_mattr_empty                — empty list returns 0
test_mattr_uniform              — all same token returns low score
test_mattr_varied               — all unique tokens returns ~1.0
test_mattr_window_larger_than_text — graceful degradation
```

### test_texttiling.py
```
test_tiles_produced             — fixture text produces > 1 block
test_block_schema               — each block has all required fields
test_block_ids_sequential       — block IDs are 1-indexed and sequential
test_block_offsets_valid        — start_char < end_char, non-overlapping
test_block_preview_matches      — preview matches text at offset
test_metrics_in_range           — MATTR in [0,1], Flesch in [-50, 120], Fog > 0
test_notable_blocks_exist       — notable dict has all expected keys
test_notable_ids_valid          — IDs in notable lists exist in blocks
test_fallback_window            — if default window fails, falls back gracefully
test_min_word_filter            — blocks below threshold are excluded
test_result_type                — returns AnalyzerResult with correct name
```

### test_json_export.py
```
test_manifest_schema            — manifest has all required fields
test_manifest_timestamp         — analyzed_at is valid ISO 8601
test_analysis_roundtrip         — write then read produces identical data
test_output_dir_created         — creates directory if it doesn't exist
test_manuscript_copied          — manuscript.txt exists in output dir
```

---

## 10. Known Risks & Open Questions

1. **Character offset mapping** (described in section 5) — the trickiest part. TextTiling reformats text, so tile content != original text substring. Need a robust mapping strategy.

2. **NLTK data dependency** — TextTiling needs `punkt_tab` tokenizer data. Tests need this too. Should `conftest.py` ensure NLTK data is downloaded?

3. **TextTiling empty result** — very short texts or texts without paragraph breaks can make TextTiling return 0 or 1 tile. The analyzer should handle this gracefully (warning, not crash).

4. **Fixture text authorship** — need a sample that's genuinely literary (varied sentence structure) but short enough for fast tests. Could use a public domain excerpt or craft one.

5. **`textstat` edge cases** — `textstat.flesch_reading_ease()` can return negative numbers for extremely complex prose. Our schema should allow this (it's valid, just unusual).

---

## Definition of Done

- [ ] `pip install -e ./engine` works
- [ ] `from lit_engine.analyzers.texttiling import TextTilingAnalyzer` imports cleanly
- [ ] `TextTilingAnalyzer().analyze(text, config)` returns valid `AnalyzerResult`
- [ ] Output matches `analysis.json` schema from spec
- [ ] `manifest.json` generated with correct metadata
- [ ] `manuscript.txt` copied to output directory
- [ ] All tests pass: `pytest engine/tests/ -v`
- [ ] Can analyze `the_specimen_v2.txt` and produce valid JSON
