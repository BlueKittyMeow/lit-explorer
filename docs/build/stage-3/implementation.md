# Stage 3: Supporting Analyzers — Implementation Document
## Rev 2

---

## 1. Review Resolution Summary

### Blockers Fixed

**B1: Readability/pacing output contracts resolved (Codex blocker, Gemini concern)**
- Decision: **Option B** — readability analyzer returns per-block extended metrics. CLI merges them into texttiling blocks before writing analysis.json. All block-level metrics live in one canonical place.
- Readability adds `coleman_liau`, `smog`, `ari` to each block's `metrics` dict.
- Pacing returns standalone staccato/flowing passage lists (not per-block enrichment). These go into a `"pacing"` top-level key in analysis.json.

**B2: CLI topological ordering (Codex blocker)**
- Add `resolve_execution_order()` to `analyzers/__init__.py` that performs a basic topological sort using each analyzer's `requires()`. The CLI calls this instead of iterating `list_analyzers()` or raw `--only` names.
- Simple Kahn's algorithm — no external dependency needed.
- **Rev 2 (B5):** Fail-fast on missing dependencies. If an analyzer requires another that isn't in the requested set, raise a clear error (e.g., `--only chapters` without texttiling/dialogue/etc. fails immediately). No silent skipping.

**B3: Chapters `requires()` missing silence (Codex blocker)**
- Add `"silence"` to chapters' `requires()` list: `["texttiling", "agency", "dialogue", "sentiment", "silence"]`.
- Chapters aggregator includes per-chapter silence stats (avg gap words, longest gap).

**B4: Context mutation eliminated (both reviewers)**
- Chapters analyzer does NOT mutate texttiling blocks. Instead, it returns a `block_to_chapter` mapping in its `data`:
  ```json
  {
      "chapters": [...],
      "block_to_chapter": { "1": 1, "2": 1, ..., "17": 2, ... }
  }
  ```
- CLI applies the mapping to texttiling blocks before writing analysis.json:
  ```python
  if "chapters" in results:
      mapping = results["chapters"].data.get("block_to_chapter", {})
      for block in results["texttiling"].data["blocks"]:
          block["chapter"] = mapping.get(str(block["id"]))
  ```

### Concerns Addressed

**C1: Sentiment `neu` field (Codex)** — Controlled addition. VADER always returns `neu`. Including it is additive and useful for visualization. Frontend types can include it as optional. Documented as deviation.

**C2: `manifest.chapter_count` (Codex)** — `build_manifest()` already accepts `chapter_count` (default 0). CLI passes `len(results["chapters"].data["chapters"])` when chapters analyzer ran.

**C3: Chapter regex too broad (both)** — The target manuscript uses `Chapter N - Title` exclusively. Updated default pattern to require an explicit marker word. Added `min_chapter_words` config (default 200) to filter false positives where detected "chapters" are too short.

**C4: Title-capture absorbs first sentence (Codex)** — Title is extracted from the heading line itself (`Chapter 1 - Café Union` → title = `Café Union`), not from a separate following line. This eliminates the false-capture risk entirely.

**C5: German/curly quote ambiguity (Codex)** — The target manuscript uses only curly double quotes (U+201C/U+201D). Default quote pairs are processed in priority order: German `„..."` first (more specific opener U+201E), then English curly `"..."`, then straight `"..."`. Since openers are distinct, no ambiguity arises.

**C6: Unclosed quote at EOF (Codex)** — If no closing quote and no paragraph break before EOF, span extends to EOF. Explicit test case.

**C7: Sentiment chapter averaging coordinate mismatch (Codex)** — Sentiment tracks `(sentence_index, start_char, end_char, scores)` tuples internally. Chapter averages computed by filtering sentences whose char ranges overlap with chapter char ranges. Position in arc remains `sentence_index / total_sentences`.

**C8: Pacing thresholds (Codex)** — Documented as heuristic limitation. Thresholds are configurable. Block-level averages are a pragmatic granularity; sub-block rhythm analysis deferred to Stage 7.

**C9: Zero-dialogue silence (Codex)** — Return empty `gaps` list, `total_gaps: 0`, `avg_gap_words: 0`, `longest_silence: null`. Add warning: "No dialogue spans found."

**C10: Adjacent quotes = 0-word gap (Gemini)** — Filter out gaps where `word_count == 0`.

**C11: Arc density (Gemini)** — Add `smoothed_arc` field (~200 points, linear interpolation) alongside full `arc`. Frontend uses smoothed for overview chart, full arc for deep-dive.

**C13: Test matrix gaps (Codex)** — Add explicit tests for: toposort execution order, analysis.json rewrite with chapter assignments, manifest chapter_count populated, sentiment arc schema keys, CLI integration with all 4 JSON files.

**C14: Multi-paragraph dialogue (Gemini)** — Handle the literary convention: opening quote without closing on same paragraph = continued dialogue. Scan next paragraph — if it starts with an opening quote, the previous span continues. If not, terminate at paragraph end.

### Rev 2 Fixes (from implementation review)

**B5: Fail-fast on missing dependencies (Codex blocker)**
- `resolve_execution_order()` raises `ValueError` if a required dependency is not in the requested analyzer set. For example, `--only chapters` fails with: "Analyzer 'chapters' requires 'texttiling' which is not in the requested set."
- This prevents silent partial runs where chapters runs without context.
- Test added: `test_toposort.py::test_missing_dependency_raises`.

**C15: `block["chapter"]` may remain None (Codex concern)**
- After applying `block_to_chapter` mapping, CLI validates that every block has a non-None chapter assignment. If any block is unmapped, emit a warning but don't fail (blocks before the first chapter heading legitimately have no chapter — assign them to chapter 0 or the first chapter).
- Decision: blocks before the first chapter heading are assigned to chapter 1 (the first detected chapter). The `block_to_chapter` mapping produced by chapters analyzer covers ALL blocks.

**C16: `min_chapter_words` default lowered (Codex concern)**
- Default changed from 200 to 100 to accommodate short prologues/interludes.
- Configurable — manuscripts with very short chapters can set to 0.

**C17: Sentence char-range mapping robustness (Codex concern)**
- `text.find(sentence, search_from)` is fragile when sentences repeat or whitespace is normalized by the tokenizer.
- Fix: compute sentence char offsets by walking the text cumulatively. After `sent_tokenize()`, iterate sentences and find each one in the text starting from `search_from`. Track `search_from` as `match_position + len(sentence)`. If `text.find()` returns -1 (tokenizer normalized whitespace), use `search_from` as fallback position and emit a warning.
- This is the same pattern used in TextTiling's `map_tile_offsets()` with fallback (already battle-tested in Stage 1).

**C18: File inventory corrected (Codex editorial)**
- Section 14 updated: "New source files (8)" for nlp + analyzer files, "New test files (10)" for test files. Total new files: 18.

**S1: CLI test for dependency failure (Codex suggestion)**
- Added to `test_cli_stage3.py`: test that `--only chapters` without its dependencies produces a clear error, not a silent partial run.

**S2: Post-enrichment integrity check (Codex suggestion)**
- After enrichment pipeline (readability merge + chapter assignment + pacing), CLI validates:
  1. Every block has all required metrics keys (the 3 original + 3 extended if readability ran).
  2. Every block has a non-None `chapter` value if chapters ran.
  3. `pacing` key exists in analysis data only if pacing ran.
- Validation failures emit warnings but don't prevent write (graceful degradation).

**S3: `smoothed_arc` deterministic semantics (Codex suggestion)**
- If `len(arc) <= smoothed_arc_points`: `smoothed_arc = arc` (no downsampling needed).
- If `len(arc) > smoothed_arc_points`: select `smoothed_arc_points` evenly-spaced indices from the arc using `numpy.linspace(0, len(arc)-1, smoothed_arc_points)` rounded to nearest integer. Each selected entry is copied directly (no interpolation between neighbors — just decimation).
- Deterministic: same input always produces same output. No floating-point interpolation ambiguity.
- Test: `test_sentiment.py::test_smoothed_arc_length` asserts `len(smoothed_arc) == min(200, len(arc))`.

---

## 2. Shared Utility: `nlp/chapter_detect.py`

```python
"""Chapter boundary detection for literary manuscripts."""

import re
from dataclasses import dataclass

@dataclass
class ChapterBoundary:
    number: int          # 1-indexed
    title: str           # chapter title (may be empty)
    start_char: int      # inclusive
    end_char: int        # exclusive


# Default pattern: "Chapter N", "Chapter N - Title", "Kapitel N", "Teil N"
# Does NOT match bare numerals (too many false positives).
DEFAULT_CHAPTER_PATTERN = r"""(?ix)
    ^[ \t]*
    (?:chapter|kapitel|teil)
    \s+
    (\d+)                        # capture group 1: chapter number
    (?:\s*[-–—]\s*(.+))?         # capture group 2: optional title after dash
    \s*$
"""


def detect_chapters(
    text: str,
    pattern: str | None = None,
    min_chapter_words: int = 100,
) -> list[ChapterBoundary]:
    """
    Detect chapter boundaries in a manuscript.

    Strategy:
    1. Split text into lines, tracking char offsets.
    2. Match lines against chapter heading pattern.
    3. Require at least one blank line before heading (except at text start).
    4. Extract chapter number and optional title from the heading itself.
    5. Each chapter spans from heading to next heading (or end of text).
    6. Filter out "chapters" shorter than min_chapter_words.

    Returns list of ChapterBoundary sorted by start_char.
    Returns empty list if no chapters detected.
    """
```

**Key design decisions:**
- Pattern requires explicit marker word (`chapter`, `kapitel`, `teil`) — no bare numerals (resolves C3).
- Title extracted from heading line via dash separator (resolves C4): `Chapter 1 - Café Union` → number=1, title="Café Union".
- Supports en-dash `–` and em-dash `—` in addition to hyphen `-`.
- `min_chapter_words` filter rejects false positives.
- Returns empty list for texts with no chapter markers (single-chapter mode).

---

## 3. Shared Utility: `nlp/dialogue_extract.py`

```python
"""Curly-quote-aware dialogue extraction."""

from dataclasses import dataclass

@dataclass
class DialogueSpan:
    start_char: int      # inclusive (at opening quote)
    end_char: int        # exclusive (after closing quote)
    text: str            # dialogue content (without quotes)


# Quote pairs: (open_char, close_char) — processed in order (first match wins)
QUOTE_PAIRS = [
    ("\u201e", "\u201c"),   # „ " German low-high (most specific opener)
    ("\u201c", "\u201d"),   # " " English curly double
    ('"', '"'),             # " " straight double (fallback)
]


def extract_dialogue(
    text: str,
    quote_pairs: list[tuple[str, str]] | None = None,
) -> list[DialogueSpan]:
    """
    Extract dialogue spans using paired quote matching.

    Algorithm:
    1. Scan character by character.
    2. When an opening quote is found, record position and which pair it belongs to.
    3. Scan for matching closing quote of the same pair.
    4. If closing quote not found in same paragraph:
       a. Check if next paragraph starts with opening quote (multi-paragraph dialogue).
       b. If yes: continue scanning (the dialogue continues).
       c. If no: terminate span at paragraph end.
    5. If no closing quote before EOF: terminate span at EOF.
    6. Filter out spans with empty text.

    Returns list of DialogueSpan sorted by start_char.
    """
```

**Key design decisions:**
- Priority ordering resolves ambiguity (C5): German `„` (U+201E) is checked before English `"` (U+201C), since they have distinct openers.
- Multi-paragraph dialogue handled (C14): opening quote without closing → check if next paragraph opens with a quote.
- EOF termination (C6): unclosed quote at end of text terminates at EOF.
- The target manuscript uses only English curly quotes (U+201C/U+201D), so German pair will simply never match.

---

## 4. `analyzers/dialogue.py` — DialogueAnalyzer

```python
@register
class DialogueAnalyzer(Analyzer):
    name = "dialogue"
    description = "Curly-quote-aware dialogue extraction and ratio analysis"

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Extract dialogue spans via extract_dialogue().
        2. Compute total dialogue words, total narrative words, overall ratio.
        3. Return spans with char offsets + word counts.
        """
```

**Output schema:**
```json
{
    "total_dialogue_words": 28450,
    "total_narrative_words": 19780,
    "overall_dialogue_ratio": 0.590,
    "span_count": 1847,
    "spans": [
        { "start_char": 1234, "end_char": 1356, "word_count": 24 }
    ]
}
```

- No dependencies.
- Speaker identification deferred to Stage 7 (spec says "where possible" — non-trivial).
- `spans` stores all dialogue spans. Chapters aggregator uses these to compute per-chapter `dialogue_ratio`.

---

## 5. `analyzers/readability.py` — ReadabilityAnalyzer

```python
@register
class ReadabilityAnalyzer(Analyzer):
    name = "readability"
    description = "Extended readability metrics (Coleman-Liau, SMOG, ARI) per block"

    def requires(self) -> list[str]:
        return ["texttiling"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Read texttiling blocks from context.
        2. For each block, extract text from clean_text using char offsets.
        3. Compute coleman_liau, smog, ari via textstat.
        4. Also compute whole-text readability summary.
        """
```

**Output schema:**
```json
{
    "per_block": [
        { "block_id": 1, "coleman_liau": 12.3, "smog": 10.1, "ari": 11.5 }
    ],
    "whole_text": {
        "flesch_ease": 65.2,
        "flesch_grade": 8.1,
        "gunning_fog": 10.3,
        "coleman_liau": 11.8,
        "smog": 9.4,
        "ari": 10.9
    }
}
```

**CLI enrichment (Option B):** After readability runs, CLI merges `per_block` data into texttiling blocks:
```python
if "readability" in results:
    readability_blocks = {
        b["block_id"]: b for b in results["readability"].data["per_block"]
    }
    for block in results["texttiling"].data["blocks"]:
        extra = readability_blocks.get(block["id"], {})
        for key in ("coleman_liau", "smog", "ari"):
            if key in extra:
                block["metrics"][key] = extra[key]
```

This keeps all block metrics in `analysis.json` (resolves B1, Gemini's "Option B is superior").

---

## 6. `analyzers/pacing.py` — PacingAnalyzer

```python
@register
class PacingAnalyzer(Analyzer):
    name = "pacing"
    description = "Sentence length distribution and rhythm pattern detection"

    def requires(self) -> list[str]:
        return ["texttiling"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Collect all sentence_lengths from texttiling blocks.
        2. Compute distribution stats (mean, median, std_dev, percentiles).
        3. Identify staccato passages (avg_sentence_length < threshold).
        4. Identify flowing passages (avg_sentence_length > threshold).
        """
```

**Output schema:**
```json
{
    "sentence_count": 4821,
    "distribution": {
        "mean": 14.3,
        "median": 12.0,
        "std_dev": 8.7,
        "min": 1,
        "max": 122,
        "percentiles": { "10": 4, "25": 8, "50": 12, "75": 19, "90": 27 }
    },
    "staccato_passages": [
        { "block_id": 51, "avg_sentence_length": 5.2, "sentence_count": 12, "preview": "..." }
    ],
    "flowing_passages": [
        { "block_id": 98, "avg_sentence_length": 32.1, "sentence_count": 8, "preview": "..." }
    ]
}
```

- Reuses texttiling's `sentence_lengths` — does NOT reparse text.
- Thresholds configurable: `pacing_staccato_threshold` (default 8), `pacing_flowing_threshold` (default 25).
- Documented as block-level heuristic (C8).
- CLI writes this as a `"pacing"` top-level key in analysis.json (spec says pacing "contributes to analysis.json").

---

## 7. `analyzers/sentiment.py` — SentimentAnalyzer

```python
@register
class SentimentAnalyzer(Analyzer):
    name = "sentiment"
    description = "VADER sentence-level sentiment analysis with emotional arc"

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Sentence-tokenize with NLTK sent_tokenize().
        2. Track (sentence_index, start_char, end_char) for each sentence.
        3. Score each with VADER polarity_scores().
        4. Build arc: position = sentence_index / total_sentences.
        5. Detect chapter boundaries via chapter_detect.
        6. Compute chapter_averages by filtering sentences whose
           char ranges overlap each chapter's char range.
        7. Find extremes (most positive, most negative compound).
        8. Build smoothed_arc (~200 points, linear interpolation).
        """
```

**Output schema (sentiment.json):**
```json
{
    "method": "vader",
    "granularity": "sentence",
    "arc": [
        { "position": 0.0, "compound": 0.15, "pos": 0.08, "neg": 0.02, "neu": 0.90 }
    ],
    "smoothed_arc": [
        { "position": 0.0, "compound": 0.12 }
    ],
    "chapter_averages": [
        { "chapter": 1, "compound": 0.12 }
    ],
    "extremes": {
        "most_positive": { "position": 0.45, "text_preview": "...", "score": 0.89 },
        "most_negative": { "position": 0.78, "text_preview": "...", "score": -0.92 }
    }
}
```

**Key design decisions:**
- `neu` included in arc entries (C1 — controlled addition, VADER provides it).
- `smoothed_arc` added with ~200 evenly-spaced points (C11 — frontend overview chart).
- Chapter averages use char-range mapping (C7): during sentence tokenization, track `start_char` of each sentence. Compute cumulative char offset by walking `text.find(sentence, search_from)` with `search_from` advancing after each match. If `find()` returns -1 (tokenizer normalized whitespace), use `search_from` as fallback position (same pattern as TextTiling's `map_tile_offsets()`). Filter sentences by chapter char ranges.
- `text_preview` in extremes truncated to 120 chars.
- No dependencies on other analyzers — uses `chapter_detect` utility directly.

---

## 8. `analyzers/chapters.py` — ChaptersAnalyzer

The aggregator. Runs last.

```python
@register
class ChaptersAnalyzer(Analyzer):
    name = "chapters"
    description = "Chapter boundary detection and per-chapter metric aggregation"

    def requires(self) -> list[str]:
        return ["texttiling", "agency", "dialogue", "sentiment", "silence"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Detect chapter boundaries via chapter_detect.detect_chapters().
        2. Build block_to_chapter mapping from texttiling blocks.
        3. For each chapter:
           a. Slice text by char range → compute word_count, sentence_count,
              avg_sentence_length, mattr, flesch_ease, fog.
           b. Intersect dialogue spans → compute dialogue_ratio.
           c. Filter sentiment arc entries → compute chapter sentiment averages.
           d. Count character mentions (token-level, case-insensitive).
           e. Determine dominant_character.
           f. Find block_range from block_to_chapter mapping.
           g. Compute silence stats from silence gaps in chapter range.
        4. Return chapters list + block_to_chapter mapping.
        """
```

**Output schema (chapters.json — spec-compliant):**
```json
{
    "chapters": [
        {
            "number": 1,
            "title": "Café Union",
            "word_count": 3433,
            "sentence_count": 240,
            "dialogue_ratio": 0.463,
            "avg_sentence_length": 14.3,
            "mattr": 0.812,
            "flesch_ease": 72.1,
            "fog": 9.4,
            "character_mentions": { "emil": 41, "felix": 42 },
            "dominant_character": "shared",
            "sentiment": {
                "compound": 0.12,
                "pos": 0.08,
                "neg": 0.04,
                "neu": 0.88
            },
            "block_range": [1, 16]
        }
    ],
    "block_to_chapter": { "1": 1, "2": 1, "17": 2 }
}
```

**Note:** `block_to_chapter` is internal routing data. CLI writes only `{"chapters": [...]}` to chapters.json (same pattern as characters.json schema-drift fix from Stage 2).

**Key design decisions:**
- `requires()` includes all five dependencies: texttiling, agency, dialogue, sentiment, silence (B3).
- Returns `block_to_chapter` mapping — does NOT mutate texttiling context (B4).
- `dominant_character`: character with most mentions, or `"shared"` if top two differ by ≤ 20%.
- Character mentions: tokenize chapter text, count case-insensitive matches for each name in `character_list` from agency result. Token-level (not substring) prevents "Emil" matching "Emily".
- Single-chapter fallback: if no chapters detected, one chapter spanning the entire text.
- Per-chapter silence stats: filter silence gaps by char range, compute avg_gap_words and longest_gap for inclusion in chapters.json.

---

## 9. `analyzers/silence.py` — SilenceAnalyzer

```python
@register
class SilenceAnalyzer(Analyzer):
    name = "silence"
    description = "Measures gaps between dialogue and maps character silence"

    def requires(self) -> list[str]:
        return ["dialogue"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        """
        1. Get dialogue spans from dialogue result (sorted by start_char).
        2. Compute gaps between consecutive spans.
        3. Include gap before first dialogue and after last dialogue.
        4. Filter out 0-word gaps (adjacent quotes).
        5. Compute statistics.
        """
```

**Output schema:**
```json
{
    "gaps": [
        { "start_char": 5200, "end_char": 6800, "word_count": 312 }
    ],
    "longest_silence": {
        "word_count": 1247,
        "position": 0.45,
        "preview": "The laboratory was empty now..."
    },
    "avg_gap_words": 42.3,
    "total_gaps": 847
}
```

**Key design decisions:**
- 0-word gaps filtered out (C10).
- Zero-dialogue edge case: return empty gaps list, `total_gaps: 0`, `longest_silence: null`, add warning (C9).
- `position` in longest_silence: `start_char / len(text)` (0.0 to 1.0).
- Speaker tracking deferred to Stage 7 (removed from schema for now).

---

## 10. Topological Sort: `analyzers/__init__.py`

Add `resolve_execution_order()`:

```python
def resolve_execution_order(analyzer_names: list[str]) -> list[str]:
    """
    Topological sort of analyzer names using requires().

    Uses Kahn's algorithm.

    Raises ValueError if:
    - A required dependency is not in the requested set (fail-fast, B5).
    - A circular dependency is detected.

    Returns analyzer_names reordered so dependencies come before dependents.
    """
    # 1. For each requested analyzer, check requires() are all in the set.
    #    If not, raise ValueError with a clear message.
    # 2. Build adjacency graph from requires().
    # 3. Kahn's algorithm: start from nodes with in-degree 0.
    # 4. Return sorted list.
```

The CLI calls this on the analyzer list before iterating:
```python
analyzer_names = resolve_execution_order(analyzer_names)
```

---

## 11. CLI Updates

```python
# After all analyzers run:

# 1. Apply readability enrichment to texttiling blocks
if "readability" in results and "texttiling" in results:
    readability_blocks = {
        b["block_id"]: b for b in results["readability"].data["per_block"]
    }
    for block in results["texttiling"].data["blocks"]:
        extra = readability_blocks.get(block["id"], {})
        for key in ("coleman_liau", "smog", "ari"):
            if key in extra:
                block["metrics"][key] = extra[key]

# 2. Apply chapter assignments to texttiling blocks
if "chapters" in results and "texttiling" in results:
    mapping = results["chapters"].data.get("block_to_chapter", {})
    for block in results["texttiling"].data["blocks"]:
        block["chapter"] = mapping.get(str(block["id"]))

# 3. Add pacing to texttiling data
if "pacing" in results and "texttiling" in results:
    results["texttiling"].data["pacing"] = {
        k: v for k, v in results["pacing"].data.items()
    }

# 4. Write analysis.json (AFTER enrichment)
if "texttiling" in results:
    path = write_analysis(output, results["texttiling"].data)

# 5. Write characters.json
if "agency" in results:
    characters_payload = {"characters": results["agency"].data["characters"]}
    path = write_characters(output, characters_payload)

# 6. Write chapters.json (spec-compliant: chapters list only)
if "chapters" in results:
    chapters_payload = {"chapters": results["chapters"].data["chapters"]}
    path = write_chapters(output, chapters_payload)

# 7. Write sentiment.json
if "sentiment" in results:
    path = write_sentiment(output, results["sentiment"].data)

# 8. Manifest — include chapter_count
chapter_count = 0
if "chapters" in results:
    chapter_count = len(results["chapters"].data["chapters"])

manifest = build_manifest(
    ...,
    chapter_count=chapter_count,
    ...
)
```

---

## 12. Config Additions

```python
# Add to DEFAULT_CONFIG:

    # Chapter detection
    "chapter_pattern": None,           # None = DEFAULT_CHAPTER_PATTERN
    "min_chapter_words": 100,          # reject detected "chapters" shorter than this

    # Dialogue
    "dialogue_quote_pairs": None,      # None = QUOTE_PAIRS default

    # Pacing
    "pacing_staccato_threshold": 8,    # avg_sentence_length below = staccato
    "pacing_flowing_threshold": 25,    # avg_sentence_length above = flowing

    # Sentiment
    "sentiment_method": "vader",
    "smoothed_arc_points": 200,        # number of points in smoothed_arc
```

---

## 13. New Dependencies

Add to `pyproject.toml`:
```toml
"vaderSentiment>=3.3.2"
```

---

## 14. File Summary

### New source files (8)
| File | Purpose |
|------|---------|
| `nlp/chapter_detect.py` | Chapter boundary detection utility |
| `nlp/dialogue_extract.py` | Dialogue span extraction utility |
| `analyzers/dialogue.py` | DialogueAnalyzer |
| `analyzers/readability.py` | ReadabilityAnalyzer |
| `analyzers/pacing.py` | PacingAnalyzer |
| `analyzers/sentiment.py` | SentimentAnalyzer |
| `analyzers/chapters.py` | ChaptersAnalyzer (aggregator) |
| `analyzers/silence.py` | SilenceAnalyzer |

### Modified files (5)
| File | Change |
|------|--------|
| `analyzers/__init__.py` | 6 new imports + `resolve_execution_order()` |
| `output/json_export.py` | `write_chapters()`, `write_sentiment()` |
| `cli.py` | Toposort, enrichment pipeline, 4-file output, manifest chapter_count |
| `config.py` | Chapter/dialogue/pacing/sentiment config keys |
| `pyproject.toml` | `vaderSentiment` dependency |

### Test files (10 new)
| File | Est. tests | Key assertions |
|------|-----------|----------------|
| `test_chapter_detect.py` | 8 | Pattern match, blank-line, title from dash, min_words filter, no-chapter fallback, German markers |
| `test_dialogue_extract.py` | 8 | Curly quotes, German quotes, unclosed quotes, multi-paragraph, EOF termination, empty text, 0-length filter |
| `test_dialogue.py` | 5 | Schema, ratio range, span offsets valid, no-dialogue edge |
| `test_readability.py` | 5 | Schema, per-block metrics in range, whole-text summary, empty block |
| `test_pacing.py` | 6 | Distribution stats, staccato detection, flowing detection, configurable thresholds, empty text |
| `test_sentiment.py` | 7 | Arc positions 0-1, extremes found, chapter_averages present, VADER scores in range, smoothed_arc length, schema keys |
| `test_chapters.py` | 9 | Chapter schema, block_to_chapter mapping, character mentions, dominant_character logic, dialogue_ratio aggregated, sentiment aggregated, single-chapter fallback, block_range valid |
| `test_silence.py` | 6 | Gap detection, longest_silence, avg_gap, 0-word filtered, no-dialogue edge, adjacent quotes |
| `test_toposort.py` | 6 | Basic ordering, diamond dependency, independent analyzers, missing dependency raises, circular detection, full Stage 3 order |
| `test_cli_stage3.py` | 6 | All 4 JSON files written, manifest chapter_count, analysis.json has chapter fields, readability enrichment applied, `--only chapters` fails without deps (S1), post-enrichment integrity |

**Estimated: ~67 new tests, total ~159.**

---

## 15. Execution Order (Final)

```
1. texttiling      (no deps)           — already exists
2. agency          (no deps)           — already exists
3. dialogue        (no deps)
4. readability     (texttiling)
5. pacing          (texttiling)
6. sentiment       (no deps)
7. silence         (dialogue)
8. chapters        (texttiling, agency, dialogue, sentiment, silence)
```

Analyzers 3-6 are independent of each other and could run in parallel. Silence depends on dialogue. Chapters depends on everything and runs last.
