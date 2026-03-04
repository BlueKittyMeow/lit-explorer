# Stage 3: Supporting Analyzers
## Detailed Build Plan

---

## Objective

Build the remaining six analyzers — dialogue, readability, pacing, sentiment, chapters, and silence — completing the engine's full analysis pipeline. After this stage, `lit-engine analyze manuscript.txt` produces `analysis.json` (Stage 1), `characters.json` (Stage 2), `chapters.json`, and `sentiment.json`.

---

## Dependencies

- **Stage 1 complete:** base `Analyzer` class, `AnalyzerResult`, registry, config, JSON export, TextTiling analyzer
- **Stage 2 complete:** agency analyzer, pronoun resolution, verb categories, character auto-detection
- **TextTiling blocks provide:** per-block mattr, avg_sentence_length, max_sentence_length, flesch_ease, flesch_grade, gunning_fog, sentence_lengths, `"chapter": None` placeholder
- **New external dependencies:** `vaderSentiment` (VADER sentiment analysis)
- **Already available:** `textstat` (readability), `nltk` (tokenization), `spacy` (NER/parsing)

---

## Architecture Overview

Stage 3 introduces two **shared NLP utilities** (chapter detection, dialogue extraction) and six **analyzers** that feed into two new JSON outputs:

```
         ┌─────────────┐     ┌───────────────┐
         │  dialogue    │     │  sentiment     │
         │  (spans)     │     │  (VADER arc)   │
         └──────┬───────┘     └──────┬─────────┘
                │                    │
         ┌──────┴───────┐           │
         │  silence     │           │
         │  (gaps)      │           │
         └──────┬───────┘           │
                │                   │
    ┌───────────┼───────────────────┼───────────┐
    │           │      chapters     │           │
    │           │    (aggregator)   │           │
    │           └───────┬───────────┘           │
    │                   │                       │
    │  ┌────────────────┤                       │
    │  │ texttiling     │  agency               │
    │  │ (blocks)       │  (characters)         │
    │  └────────────────┘                       │
    └───────────────────────────────────────────┘
              │                    │
         chapters.json       sentiment.json
```

**Execution order** (declared via `requires()`):

```
Independent:  dialogue, sentiment, readability, pacing
Depends on dialogue:  silence
Depends on everything:  chapters
```

---

## 1. New Files

```
engine/src/lit_engine/
├── nlp/
│   ├── chapter_detect.py      ← chapter boundary detection utility
│   └── dialogue_extract.py    ← curly-quote-aware dialogue extraction
├── analyzers/
│   ├── dialogue.py            ← DialogueAnalyzer
│   ├── readability.py         ← ReadabilityAnalyzer
│   ├── pacing.py              ← PacingAnalyzer
│   ├── sentiment.py           ← SentimentAnalyzer
│   ├── chapters.py            ← ChaptersAnalyzer (aggregator)
│   └── silence.py             ← SilenceAnalyzer
```

Plus updates to:
- `analyzers/__init__.py` — add imports for all six new modules
- `output/json_export.py` — add `write_chapters()`, `write_sentiment()`
- `cli.py` — add `chapters.json` and `sentiment.json` output routing
- `config.py` — add chapter/dialogue/sentiment configuration

---

## 2. `nlp/chapter_detect.py`

Shared utility for chapter boundary detection. Used by the chapters analyzer directly, and available to sentiment for chapter_averages.

```python
"""Chapter boundary detection for literary manuscripts."""

import re
from dataclasses import dataclass

@dataclass
class ChapterBoundary:
    number: int          # 1-indexed chapter number
    title: str           # chapter title (may be empty string)
    start_char: int      # start offset in clean text
    end_char: int        # end offset in clean text (exclusive)


# Default pattern: handles "Chapter 1", "Chapter I", "CHAPTER ONE",
# "1.", "I.", standalone Roman numerals, and title lines after blank lines.
DEFAULT_CHAPTER_PATTERN = r"""(?ix)
    ^[ \t]*                           # optional leading whitespace
    (?:
        (?:chapter|teil|kapitel)       # explicit marker (EN/DE)
        \s+
        (?:[IVXLCDM]+|\d+|            # Roman or Arabic numeral
           one|two|three|four|five|    # English words
           six|seven|eight|nine|ten|
           eleven|twelve)
    |
        (?:[IVXLCDM]+|\d+)\.?         # bare numeral with optional period
    )
    \s*$                              # end of line
"""


def detect_chapters(
    text: str,
    pattern: str | None = None,
) -> list[ChapterBoundary]:
    """
    Detect chapter boundaries in a manuscript.

    Strategy:
    1. Split text into lines.
    2. Find lines matching the chapter heading pattern.
    3. Require at least one blank line preceding a heading (except at start).
    4. Capture optional title line immediately following the heading.
    5. Each chapter spans from its heading to the next heading (or end of text).

    Returns list of ChapterBoundary, sorted by start_char.
    """
    ...
```

**Design decisions:**
- Pattern is configurable via `config["chapter_pattern"]`
- Blank-line heuristic prevents false matches mid-paragraph
- Optional title capture: if the line after the heading is short (< 80 chars) and non-empty, treat it as the chapter title (e.g., "Café Union")
- Returns empty list if no chapters detected (single-chapter text)
- German support: "Kapitel", "Teil" markers

---

## 3. `nlp/dialogue_extract.py`

Shared utility for dialogue span extraction.

```python
"""Curly-quote-aware dialogue extraction."""

from dataclasses import dataclass

@dataclass
class DialogueSpan:
    start_char: int      # start offset in text (inclusive, at opening quote)
    end_char: int        # end offset in text (exclusive, after closing quote)
    text: str            # dialogue text (without quotes)


# Quote pairs: (open, close)
QUOTE_PAIRS = [
    ("\u201c", "\u201d"),   # " " curly double
    ("\u201e", "\u201c"),   # „ " German-style double
    ("\u00ab", "\u00bb"),   # « » guillemets
    ('"', '"'),             # " " straight double
]


def extract_dialogue(
    text: str,
    quote_pairs: list[tuple[str, str]] | None = None,
) -> list[DialogueSpan]:
    """
    Extract dialogue spans from text using paired quote matching.

    Strategy:
    1. Scan for opening quote characters.
    2. Find the matching closing quote.
    3. Handle nested quotes (single inside double).
    4. Return spans sorted by start_char.

    Edge cases:
    - Unclosed quotes: span extends to end of paragraph (next blank line).
    - Multi-paragraph dialogue: opening quote without closing on same paragraph
      continues to next paragraph that starts with a quote.
    - German curly quotes „..." (open-low, close-high) — included in defaults.
    """
    ...
```

**Design decisions:**
- Curly quotes are the primary target (the novel uses „..." German-style)
- Straight quotes as fallback
- Configurable quote pairs for internationalization
- Returns character-level offsets for precise position mapping
- Paragraph-bounded: unclosed quotes terminate at paragraph break

---

## 4. `analyzers/dialogue.py` — DialogueAnalyzer

```python
@register
class DialogueAnalyzer(Analyzer):
    name = "dialogue"
    description = "Curly-quote-aware dialogue extraction and ratio analysis"

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        ...
```

**Output schema:**
```json
{
    "total_dialogue_words": 28450,
    "total_narrative_words": 19780,
    "overall_dialogue_ratio": 0.590,
    "spans": [
        {
            "start_char": 1234,
            "end_char": 1356,
            "word_count": 24
        }
    ],
    "span_count": 1847
}
```

**Notes:**
- `spans` stores all dialogue spans with char offsets and word counts
- `overall_dialogue_ratio` = total_dialogue_words / (total_dialogue_words + total_narrative_words)
- Chapters analyzer uses the spans to compute per-chapter `dialogue_ratio`
- Speaker identification is aspirational (spec says "identifies speaker where possible") — initial implementation may defer this
- No dependencies on other analyzers

---

## 5. `analyzers/readability.py` — ReadabilityAnalyzer

```python
@register
class ReadabilityAnalyzer(Analyzer):
    name = "readability"
    description = "Extended readability metrics per block and per chapter"

    def requires(self) -> list[str]:
        return ["texttiling"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        ...
```

**Design question for reviewers:** TextTiling already computes `flesch_ease`, `flesch_grade`, and `gunning_fog` per block. The spec mentions Coleman-Liau, SMOG, and ARI additionally. Two approaches:

**Option A (proposed):** Readability analyzer reads texttiling blocks from context, computes the three additional metrics per block, and returns them as a parallel structure. The chapters analyzer uses these when aggregating. analysis.json blocks remain unchanged (only the original 3 metrics).

**Option B:** Readability analyzer enriches the texttiling blocks in-place (adds coleman_liau, smog, ari to each block's metrics dict). Requires the CLI to merge readability data back into analysis.json.

**Proposed output schema (Option A):**
```json
{
    "per_block": [
        {
            "block_id": 1,
            "coleman_liau": 12.3,
            "smog": 10.1,
            "ari": 11.5
        }
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

**Notes:**
- Depends on texttiling (for block boundaries, to compute per-block)
- `whole_text` provides manuscript-level readability summary
- Chapter-level readability is computed by the chapters aggregator using block data

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
        ...
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
        {
            "block_id": 51,
            "avg_sentence_length": 5.2,
            "sentence_count": 12,
            "preview": "He stopped. Listened. Nothing."
        }
    ],
    "flowing_passages": [
        {
            "block_id": 98,
            "avg_sentence_length": 32.1,
            "sentence_count": 8,
            "preview": "When the morning light finally..."
        }
    ]
}
```

**Detection criteria:**
- **Staccato:** blocks where avg_sentence_length < 8 words (short, punchy prose)
- **Flowing:** blocks where avg_sentence_length > 25 words (sustained, complex sentences)
- Thresholds configurable via `config["pacing_staccato_threshold"]` and `config["pacing_flowing_threshold"]`

**Notes:**
- Reads texttiling blocks from context (uses sentence_lengths already computed)
- Does NOT reparse the text — reuses TextTiling's sentence analysis
- Distribution stats computed from all sentence lengths across all blocks
- Spec says "Contributes to analysis.json" — proposed: add a `"pacing"` top-level key to analysis.json, or return standalone data that the CLI writes alongside analysis.json

---

## 7. `analyzers/sentiment.py` — SentimentAnalyzer

```python
@register
class SentimentAnalyzer(Analyzer):
    name = "sentiment"
    description = "VADER sentence-level sentiment analysis with emotional arc"

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        ...
```

**Output schema (matches spec `sentiment.json`):**
```json
{
    "method": "vader",
    "granularity": "sentence",
    "arc": [
        { "position": 0.0, "compound": 0.15, "pos": 0.08, "neg": 0.02, "neu": 0.90 }
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

**Algorithm:**
1. Sentence-tokenize the full text (NLTK `sent_tokenize`)
2. Score each sentence with VADER `polarity_scores()`
3. Compute `position` as `sentence_index / total_sentences` (0.0 to 1.0)
4. Detect chapter boundaries using `chapter_detect.detect_chapters()`
5. Compute `chapter_averages`: for each chapter, average the `compound` scores of sentences within its character range
6. Find `extremes`: highest and lowest `compound` scores with text previews (truncated to 120 chars)

**Notes:**
- Uses `chapter_detect` utility directly (does NOT depend on chapters analyzer)
- `arc` contains one entry per sentence — for a 240k-char novel this is ~4800 entries
- No smoothing in the raw output — the frontend can smooth for visualization
- `neu` score added to arc entries beyond what spec shows (VADER provides it, useful for visualization)

---

## 8. `analyzers/chapters.py` — ChaptersAnalyzer

The **aggregator** — runs last, pulls from all previous analyzers to build `chapters.json`.

```python
@register
class ChaptersAnalyzer(Analyzer):
    name = "chapters"
    description = "Chapter boundary detection and per-chapter metric aggregation"

    def requires(self) -> list[str]:
        return ["texttiling", "agency", "dialogue", "sentiment"]

    def analyze(self, text, config, context=None) -> AnalyzerResult:
        ...
```

**Output schema (matches spec `chapters.json`):**
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
            "character_mentions": {
                "emil": 41,
                "felix": 42,
                "helena": 1,
                "reichmann": 3
            },
            "dominant_character": "shared",
            "sentiment": {
                "compound": 0.12,
                "pos": 0.08,
                "neg": 0.04,
                "neu": 0.88
            },
            "block_range": [1, 16]
        }
    ]
}
```

**Algorithm:**
1. Detect chapter boundaries using `chapter_detect.detect_chapters()`
2. **Update texttiling blocks:** fill `"chapter"` field by mapping each block's char range to a chapter number (for analysis.json)
3. For each chapter:
   - **word_count, sentence_count, avg_sentence_length:** computed from chapter text slice
   - **mattr:** computed from chapter text (reuse `texttiling.mattr()`)
   - **flesch_ease, fog:** computed from chapter text via `textstat`
   - **dialogue_ratio:** intersect dialogue spans from dialogue analyzer with chapter char range; ratio = dialogue words / total words
   - **character_mentions:** count occurrences of each character name (from agency result's `character_list`) in chapter text (case-insensitive token match)
   - **dominant_character:** the character with most mentions, or `"shared"` if top two are within 20% of each other
   - **sentiment:** average VADER scores from sentiment arc entries within chapter position range
   - **block_range:** [first_block_id, last_block_id] for blocks assigned to this chapter

**Side effect on texttiling data:** The chapters analyzer fills the `"chapter": None` placeholders in texttiling blocks. The CLI must re-write analysis.json after chapters runs (or write analysis.json last).

**Notes:**
- If no chapters detected, returns a single chapter spanning the entire text
- `dominant_character` uses the "shared" label when the top two characters' mention counts differ by ≤ 20%
- Character mention counting is token-level (not substring) to avoid "Emil" matching inside "Emily"

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
        ...
```

**Output schema:**
```json
{
    "gaps": [
        {
            "start_char": 5200,
            "end_char": 6800,
            "word_count": 312,
            "preceding_speaker": null,
            "following_speaker": null
        }
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

**Algorithm:**
1. Get dialogue spans from dialogue result (sorted by start_char)
2. Compute gaps between consecutive dialogue spans
3. Gap = text between end of one dialogue span and start of the next
4. Measure word count of each gap
5. Find longest silence and compute statistics

**Notes:**
- "Where characters go quiet" — this tracks narrative gaps between any dialogue
- Speaker tracking is aspirational for v1 (requires dialogue attribution which is complex)
- Chapters analyzer can slice gaps per chapter for chapters.json contribution
- Gaps at the very start (before first dialogue) and end (after last dialogue) are included

---

## 10. Execution Order and Dependencies

```
                        ┌──────────┐
                        │texttiling│  (already run, Stage 1)
                        │  agency  │  (already run, Stage 2)
                        └────┬─────┘
                             │
             ┌───────────────┼───────────────┐
             │               │               │
        ┌────┴────┐    ┌────┴────┐    ┌─────┴──────┐
        │dialogue │    │sentiment│    │readability  │
        │         │    │         │    │  pacing     │
        └────┬────┘    └────┬────┘    └─────┬──────┘
             │               │               │
        ┌────┴────┐          │               │
        │ silence │          │               │
        └────┬────┘          │               │
             │               │               │
             └───────────────┼───────────────┘
                             │
                      ┌──────┴──────┐
                      │  chapters   │
                      │ (aggregator)│
                      └─────────────┘
```

The CLI runs analyzers in dependency order. `chapters` declares `requires()` on texttiling, agency, dialogue, and sentiment. `silence` declares `requires()` on dialogue. The rest are independent.

---

## 11. Config Additions

```python
DEFAULT_CONFIG update:
    # Chapter detection
    "chapter_pattern": None,       # None = use DEFAULT_CHAPTER_PATTERN
    "chapter_title_max_len": 80,   # max length for a line to be treated as chapter title

    # Dialogue
    "dialogue_quote_pairs": None,  # None = use QUOTE_PAIRS default

    # Pacing
    "pacing_staccato_threshold": 8,   # avg_sentence_length below this = staccato
    "pacing_flowing_threshold": 25,   # avg_sentence_length above this = flowing

    # Sentiment
    "sentiment_method": "vader",   # only VADER for now
```

---

## 12. CLI Updates

```python
# Write output — after chapters runs, analysis.json needs re-writing
# because chapters fills the "chapter" field in texttiling blocks.

# analysis.json (texttiling + chapter assignments)
if "texttiling" in results:
    # If chapters ran, its side effect updated the block chapter fields
    path = write_analysis(output, results["texttiling"].data)

# characters.json (agency)
if "agency" in results:
    characters_payload = {"characters": results["agency"].data["characters"]}
    path = write_characters(output, characters_payload)

# chapters.json (chapters aggregator)
if "chapters" in results:
    path = write_chapters(output, results["chapters"].data)

# sentiment.json (sentiment)
if "sentiment" in results:
    path = write_sentiment(output, results["sentiment"].data)
```

**Note:** analysis.json must be written AFTER the chapters analyzer runs (not before), because chapters fills the `"chapter"` field in texttiling blocks.

---

## 13. Open Questions for Reviewers

1. **Readability per-block enrichment:** Should the readability analyzer add Coleman-Liau/SMOG/ARI to texttiling block metrics (changing the analysis.json schema), or keep them in a separate readability result? TextTiling already provides the 3 core metrics. (See Section 5, Options A vs B.)

2. **Pacing output location:** Spec says pacing "contributes to analysis.json". Should pacing data be a top-level key in analysis.json alongside "blocks"? Or a separate file? Or merged into block data?

3. **Speaker identification in dialogue:** The spec says "identifies speaker where possible." This is non-trivial (requires attribution heuristics: "X said", pronoun resolution, turn-taking inference). Propose deferring to Stage 7 polish, returning `null` for speaker in v1.

4. **Silence per-chapter breakdown:** Spec says silence "contributes to chapters.json." Should the chapters aggregator include silence stats per chapter (avg_gap_words, longest_gap), or is the standalone silence data sufficient?

5. **Chapter side effect on texttiling:** The chapters analyzer needs to fill `"chapter"` fields in texttiling blocks. This means mutating the texttiling result in context. Is this acceptable, or should we use a different mechanism (e.g., chapters returns a block-to-chapter mapping that the CLI applies)?

6. **Sentiment arc size:** ~4800 entries for a full novel. Should we downsample (e.g., every Nth sentence) or keep all entries and let the frontend handle decimation?

---

## 14. Test Strategy

Each analyzer gets its own test file:

| File | Tests | Key assertions |
|------|-------|----------------|
| `test_chapter_detect.py` | 8-10 | Pattern matching, blank-line heuristic, title capture, Roman numerals, no-chapters fallback, German markers |
| `test_dialogue_extract.py` | 8-10 | Curly quotes, straight quotes, German quotes, unclosed quotes, nested quotes, empty text |
| `test_dialogue.py` | 5-7 | AnalyzerResult schema, dialogue_ratio range, span offsets valid |
| `test_readability.py` | 4-6 | Schema, metric ranges, whole-text summary |
| `test_pacing.py` | 5-7 | Distribution stats, staccato detection, flowing detection, empty text |
| `test_sentiment.py` | 6-8 | Arc positions 0-1, extremes found, chapter_averages, VADER scores in range |
| `test_chapters.py` | 8-10 | Chapter schema, block_range valid, character_mentions counted, dominant_character logic, dialogue_ratio aggregated, single-chapter fallback |
| `test_silence.py` | 5-7 | Gap detection, longest_silence, avg_gap, no-dialogue edge case |

**Estimated: ~55-65 new tests**, bringing total to ~155.

Fixture text should include:
- At least 2 "chapters" with headers
- Dialogue in curly and/or German quotes
- Mix of short and long sentences
- Named characters for mention counting

---

## 15. Files Modified (Summary)

| File | Change |
|------|--------|
| `analyzers/__init__.py` | Add 6 new imports |
| `output/json_export.py` | Add `write_chapters()`, `write_sentiment()` |
| `cli.py` | Route chapters.json, sentiment.json; defer analysis.json write; add sentiment/chapter CLI options |
| `config.py` | Add chapter/dialogue/pacing/sentiment config keys |
| `pyproject.toml` | Add `vaderSentiment` dependency |
