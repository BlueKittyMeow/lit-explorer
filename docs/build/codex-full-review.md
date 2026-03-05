# Full Codebase Review — Codex

## Instructions

You are reviewing the **complete lit-explorer engine codebase** (Stages 1–4). This is a computational stylistics toolkit that analyzes literary manuscripts using NLP techniques. The engine currently has 217 passing tests and has been validated against The Specimen manuscript.

**Architecture overview:**
- CLI (`click`) orchestrates 8 analyzers via a topological sort + enrichment pipeline
- Analyzers follow an ABC pattern: `Analyzer.analyze(text, config, context) -> AnalyzerResult`
- Analyzers are registered via `@register` decorator into `_REGISTRY`
- Output is a set of JSON files (`analysis.json`, `characters.json`, `chapters.json`, `sentiment.json`, `manifest.json`) plus a `manuscript.txt` copy
- NLP utilities are shared modules: spaCy loader, coreference resolution, verb categorization, chapter detection, dialogue extraction, sentence location

**Read ALL of the following source files:**

### Core modules (3 files)
- `engine/src/lit_engine/__init__.py` — version string
- `engine/src/lit_engine/config.py` — `merge_config()`, default parameters
- `engine/src/lit_engine/cli.py` — CLI entry point: `analyze`, `extract`, `rerun`, `list-analyzers` commands, enrichment pipeline, per-analyzer error handling

### Analyzers (9 files)
- `engine/src/lit_engine/analyzers/__init__.py` — `Analyzer` ABC, `AnalyzerResult`, `@register`, `_REGISTRY`, `resolve_execution_order()` (Kahn's toposort), `list_analyzers()`, `get_analyzer()`
- `engine/src/lit_engine/analyzers/texttiling.py` — `prepare_text()`, `map_tile_offsets()`, `build_blocks()`, `TextTilingAnalyzer` (MATTR, notable blocks)
- `engine/src/lit_engine/analyzers/agency.py` — `AgencyAnalyzer` (spaCy NER/dep parse, verb categorization, passive voice, auto-detect characters)
- `engine/src/lit_engine/analyzers/chapters.py` — `ChaptersAnalyzer` (chapter detection, block-to-chapter mapping, per-chapter sentiment/mentions aggregation)
- `engine/src/lit_engine/analyzers/dialogue.py` — `DialogueAnalyzer` (dialogue ratio, span extraction)
- `engine/src/lit_engine/analyzers/readability.py` — `ReadabilityAnalyzer` (Coleman-Liau, SMOG, ARI per block + whole text)
- `engine/src/lit_engine/analyzers/pacing.py` — `PacingAnalyzer` (sentence length distribution, staccato/flowing detection)
- `engine/src/lit_engine/analyzers/sentiment.py` — `SentimentAnalyzer` (VADER per-sentence, smoothed arc, chapter averages, extremes)
- `engine/src/lit_engine/analyzers/silence.py` — `SilenceAnalyzer` (gaps between dialogue spans)

### NLP utilities (7 files)
- `engine/src/lit_engine/nlp/__init__.py`
- `engine/src/lit_engine/nlp/loader.py` — `load_spacy()` with fallback + LRU cache, `parse_document()`
- `engine/src/lit_engine/nlp/coref.py` — `resolve_pronouns()` (rule-based he/she/they → character mapping)
- `engine/src/lit_engine/nlp/verb_categories.py` — verb taxonomy (speech, motion, cognition, etc.), `categorize_verb()`, `build_lookup()`
- `engine/src/lit_engine/nlp/chapter_detect.py` — `detect_chapters()` (regex + blank-line + min-word filter)
- `engine/src/lit_engine/nlp/dialogue_extract.py` — `extract_dialogue()` (priority-ordered quote pairs, cross-paragraph handling)
- `engine/src/lit_engine/nlp/sentence_locate.py` — `locate_sentences()` (sentence-to-char-offset mapping)

### Output (2 files)
- `engine/src/lit_engine/output/__init__.py`
- `engine/src/lit_engine/output/json_export.py` — `write_json()`, `build_manifest()`, `slugify()`, `copy_manuscript()`

### Tests (25 test files, 217 tests total)
- `engine/tests/test_texttiling.py` — 16 tests
- `engine/tests/test_agency.py` — 17 tests
- `engine/tests/test_chapters.py` — 10 tests
- `engine/tests/test_dialogue_analyzer.py` — 6 tests
- `engine/tests/test_dialogue_extract.py` — 10 tests
- `engine/tests/test_readability.py` — 5 tests
- `engine/tests/test_pacing.py` — 7 tests
- `engine/tests/test_sentiment.py` — 9 tests
- `engine/tests/test_silence.py` — 7 tests
- `engine/tests/test_chapter_detect.py` — 10 tests
- `engine/tests/test_coref.py` — 8 tests
- `engine/tests/test_verb_categories.py` — 7 tests
- `engine/tests/test_loader.py` — 6 tests
- `engine/tests/test_sentence_locate.py` — 5 tests
- `engine/tests/test_json_export.py` — 13 tests
- `engine/tests/test_mattr.py` — 6 tests
- `engine/tests/test_prepare_text.py` — 7 tests
- `engine/tests/test_auto_detect.py` — 10 tests
- `engine/tests/test_fallback_paths.py` — 7 tests
- `engine/tests/test_toposort.py` — 6 tests
- `engine/tests/test_extract.py` — 10 tests
- `engine/tests/test_cli_agency.py` — 4 tests
- `engine/tests/test_cli_stage3.py` — 6 tests
- `engine/tests/test_cli_stage4.py` — 12 tests
- `engine/tests/test_specimen_e2e.py` — 8 tests (skips if Specimen not available)

### Also read for spec compliance:
- `spec.md` — full project specification

**Your review should evaluate:**

1. **Correctness**: Are there any logic bugs, off-by-one errors, incorrect data transformations, or silent failures?
2. **Spec compliance**: Does the implementation match `spec.md`? Any deviations, missing features, or undocumented behavior?
3. **Architecture**: Is the analyzer registry + toposort + enrichment pipeline pattern sound? Any coupling issues, circular dependencies, or fragile contracts?
4. **Error handling**: Are edge cases covered? Missing `None` checks, unhandled exceptions, file I/O risks?
5. **Security**: Any path traversal, injection, or unsafe file operations?
6. **Performance**: Any O(n^2) loops, repeated re-parsing, or unnecessary allocations that would matter on 100K+ word manuscripts?
7. **Test quality**: Are tests actually testing the right invariants? Any tests that always pass regardless of correctness? Coverage gaps?
8. **Code quality**: Dead code, duplicated logic, naming inconsistencies, overly complex functions?
9. **JSON schema correctness**: Do the output JSON files match the schema described in `spec.md`?
10. **Cross-module contracts**: Are the interfaces between analyzers, CLI, and output consistent? Any fragile assumptions?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, cite the specific file and line numbers
- Be specific and constructive
- Group findings by category, then by module/area

---

## Findings

(Codex: record your findings here)

### Blockers

### Concerns

### Suggestions

### Praise
