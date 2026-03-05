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

- BLOCKER [Correctness / Chapter Assignment]: Short chapters filtered by `min_chapter_words` can cause chapter range gaps, and blocks in those gaps are silently assigned to Chapter 1.
  - `detect_chapters()` builds chapter ranges using the *next heading start* and then removes short chapters (`engine/src/lit_engine/nlp/chapter_detect.py:84-104`). After filtering, adjacent surviving chapters are no longer guaranteed contiguous.
  - `ChaptersAnalyzer` assigns each block by midpoint and defaults to `boundaries[0].number` when no boundary contains the midpoint (`engine/src/lit_engine/analyzers/chapters.py:65-71`).
  - Combined effect: blocks that fall inside a filtered-out chapter’s char range are mis-labeled as chapter 1 instead of nearest surviving chapter (or explicit unassigned). This is a data-integrity error in `chapters.json` and in `analysis.json` enrichment.

### Concerns

- CONCERN [Architecture / Runtime Contracts]: Dependency failures do not prevent dependent analyzers from running, which can yield structurally valid but semantically degraded outputs.
  - The CLI catches analyzer exceptions and continues (`engine/src/lit_engine/cli.py:96-111`), with failure only when *all* analyzers fail (`cli.py:118-121`).
  - Dependent analyzers then run with missing context and fallback to empty/default values (e.g., `ReadabilityAnalyzer` uses `context["texttiling"] if context else None` and proceeds with empty blocks: `engine/src/lit_engine/analyzers/readability.py:27-29`; `ChaptersAnalyzer` similarly degrades to empty context: `engine/src/lit_engine/analyzers/chapters.py:46-57`).
  - This behavior is resilient, but it weakens the `requires()` contract and can silently ship partial analyses without explicit “dependency missing” warnings.

- CONCERN [Spec Compliance / Coupling]: `chapters` declares a hard dependency on `silence`, but silence output is not used in chapter aggregation.
  - Dependency declaration includes `silence` (`engine/src/lit_engine/analyzers/chapters.py:20`).
  - `silence_gaps` is read (`chapters.py:56`) but never consumed afterwards.
  - This adds compute/coupling cost without affecting output and diverges from the stated “silence contributes to chapters” intent in `spec.md` (`spec.md:425`).

- CONCERN [Test Quality]: Circular dependency test for topological sort does not actually test a cycle path.
  - `test_circular_detection` only verifies the normal full-set order resolves (`engine/tests/test_toposort.py:34-44`), so cycle-detection logic could regress without failing this test.

- CONCERN [Offset Robustness]: `locate_sentences()` fallback can produce approximate offsets without any warning channel.
  - On mismatch, it assigns `idx = search_from` and computes `(start, end)` from sentence length (`engine/src/lit_engine/nlp/sentence_locate.py:16-23`).
  - This is intentionally permissive, but downstream consumers (`sentiment`, `chapters`) may treat approximate boundaries as exact. The behavior is only partially tested (`engine/tests/test_sentence_locate.py:24-33`) and not validated against downstream impact.

### Suggestions

- SUGGESTION [Chapter Integrity]: After min-word filtering, rebuild chapter ranges to remain contiguous across surviving chapters, or carry a “filtered chapter span” map and assign blocks explicitly instead of defaulting to chapter 1.
  - Target modules: `engine/src/lit_engine/nlp/chapter_detect.py` and `engine/src/lit_engine/analyzers/chapters.py`.
  - Add regression tests for “short middle chapter filtered out” ensuring no block inside that span maps to chapter 1 by default.

- SUGGESTION [Dependency Policy]: Enforce runtime dependency checks before each analyzer runs.
  - Option A: Skip analyzer when any `requires()` dependency is absent from `results`, emit explicit warning.
  - Option B: Treat missing runtime deps as hard failure for that analyzer (or whole run when requested explicitly).
  - Target module: `engine/src/lit_engine/cli.py`.

- SUGGESTION [Silence Integration]: Either remove `silence` from `ChaptersAnalyzer.requires()` or actually aggregate silence-derived chapter metrics (e.g., chapter gap count/longest silence/avg gap words).
  - Target module: `engine/src/lit_engine/analyzers/chapters.py`.

- SUGGESTION [Test Coverage]: Replace/extend `test_circular_detection` with a true cycle fixture by monkeypatching `_REGISTRY` with temporary analyzers that mutually require each other, then assert `ValueError("Circular dependency detected ...")`.
  - Target module: `engine/tests/test_toposort.py`.

### Praise

- PRAISE [Architecture]: Registry + topological ordering is clean and maintainable, with clear fail-fast behavior for missing requested dependencies.
  - `Analyzer`/`AnalyzerResult` abstraction and registry API are minimal and coherent (`engine/src/lit_engine/analyzers/__init__.py:7-68`).
  - Kahn-based execution ordering and dependency validation are straightforward and deterministic (`analyzers/__init__.py:71-127`).

- PRAISE [Data Contract Discipline]: Output routing in CLI preserves schema boundaries (e.g., `characters.json` writes only the `characters` object; `chapters.json` omits internal `block_to_chapter` map), while keeping richer internal context for enrichment.
  - `engine/src/lit_engine/cli.py:155-165`.

- PRAISE [Text Boundary Engineering]: The TextTiling pipeline (`prepare_text` -> `map_tile_offsets` -> `build_blocks`) is thoughtfully constructed for block-level reproducibility, including fallback warnings and contiguous block semantics.
  - `engine/src/lit_engine/analyzers/texttiling.py:35-121, 124-240`.

- PRAISE [CLI Reliability Improvements]: Stage 4 hardening is present and correct: `extract` unpacking fix, all-fail nonzero exit, deterministic dependency expansion ordering, and clarified rerun semantics.
  - `engine/src/lit_engine/cli.py:118-121, 235, 315-335, 348-352`.

- PRAISE [Regression Coverage Breadth]: The suite covers schema, fallback, CLI integration, and manuscript-level e2e paths, including recent stage-specific regressions.
  - Representative files: `engine/tests/test_cli_stage3.py`, `engine/tests/test_cli_stage4.py`, `engine/tests/test_extract.py`, `engine/tests/test_specimen_e2e.py`.
