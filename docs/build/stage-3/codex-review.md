# Stage 3 Implementation Review — Codex

## Instructions

You are reviewing the Stage 3 **implementation document** for **lit-explorer**, a computational stylistics toolkit. This document incorporates findings from the first plan review (yours and Gemini's) and resolves all identified blockers.

**Read the following files before starting your review:**
1. `docs/build/stage-3/plan.md` — the original plan (for context on what changed)
2. `docs/build/stage-3/implementation.md` — **the document you are reviewing**
3. `spec.md` — the project specification (source of truth for schemas)
4. The existing working code (reference implementations):
   - `~/Documents/lit-analysis/directed_sentiment.py` — VADER sentiment + chapter detection
   - `~/Documents/lit-analysis/animacy_tracker.py` — chapter detection alternative
   - `~/Documents/lit-analysis/passage_analyzer.py` — dialogue ratio, readability metrics
   - `~/Documents/lit-analysis/specimen_analysis_v2.py` — readability per block, sentence lengths
5. The Stage 1+2 implementation (already built and passing 92 tests):
   - `engine/src/lit_engine/analyzers/__init__.py` — base Analyzer class, registry, `list_analyzers()`
   - `engine/src/lit_engine/analyzers/texttiling.py` — TextTiling (flesch_ease, flesch_grade, gunning_fog, sentence_lengths, mattr per block; `"chapter": None` placeholder)
   - `engine/src/lit_engine/analyzers/agency.py` — character agency (auto-detect, pronoun resolution, HONORIFICS with noble particles)
   - `engine/src/lit_engine/nlp/coref.py` — pronoun resolution heuristics
   - `engine/src/lit_engine/nlp/verb_categories.py` — semantic verb classification
   - `engine/src/lit_engine/config.py` — current DEFAULT_CONFIG
   - `engine/src/lit_engine/cli.py` — current CLI (analysis.json, characters.json, manifest.json)
   - `engine/src/lit_engine/output/json_export.py` — JSON export (build_manifest already has chapter_count param)
6. The target manuscript formatting:
   - Chapters: `Chapter N - Title` format (16 chapters, preceded by blank lines)
   - Dialogue: curly double quotes only (U+201C opening, U+201D closing)

**Your review should verify:**
- Were all blockers from the first review properly resolved (B1-B4)?
- Are the output schemas for chapters.json and sentiment.json spec-compliant?
- Is the block_to_chapter mapping approach clean and complete?
- Is the CLI enrichment pipeline (readability → chapters → pacing → write) correctly ordered?
- Is the topological sort specification correct (Kahn's algorithm, error handling)?
- Are the dialogue extraction edge cases (multi-paragraph, EOF, quote priority) fully specified?
- Is the sentiment char-range mapping for chapter averages sound?
- Are the test cases comprehensive enough to catch regressions?
- Any remaining gaps, inconsistencies, or ambiguities?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, cite the specific section of the implementation doc or spec
- Be specific and constructive

---

## Findings

(Codex: record your findings here)

### Blockers

- BLOCKER: Topological sort spec allows missing dependencies to be silently skipped, which can produce invalid runs for dependency-heavy analyzers.
  In Section 10, `resolve_execution_order()` explicitly says missing required analyzers are skipped (`docs/build/stage-3/implementation.md:493-496`). For commands like `--only chapters`, this can schedule `chapters` without required context (`texttiling`, `dialogue`, etc.), leading to brittle runtime behavior.  
  Recommendation: fail fast with a clear dependency error unless an explicit `--allow-missing-deps` mode is added.

### Concerns

- CONCERN: Sentiment schema intentionally drifts from `spec.md` and should be synchronized before frontend typing.
  Stage 3 adds `neu` to each `arc` entry and introduces `smoothed_arc` (`implementation.md:344-348`, `359-362`), while `spec.md` sentiment arc shows only `position`, `compound`, `pos`, `neg` (`spec.md:323-326`) and no `smoothed_arc`.  
  This may be fine as an additive extension, but the spec should be updated in the same stage to avoid contract ambiguity.

- CONCERN: `block["chapter"]` assignment can remain `None` if mapping misses a block, but schema examples imply numeric chapter assignment.
  CLI applies `block["chapter"] = mapping.get(str(block["id"]))` (`implementation.md:529-532`) with no fallback or validation. If any block is missing from mapping, `chapter` stays null-ish even after chapters runs.  
  Add validation that every block ID is assigned after chapters (or explicitly define allowed nulls post-stage-3 in spec).

- CONCERN: `min_chapter_words=200` may suppress legitimate short chapters.
  The filter is introduced as default (`implementation.md:100-112`, `122`, `578`). For manuscripts with short interludes/prologues, this can drop real chapters and skew chapter_count + chapter averages.

- CONCERN: Sentence char-range mapping method in sentiment needs explicit fallback behavior.
  Section 7 says sentence offsets come from `text.find(sentence, search_from)` (`implementation.md:362`). Repeated sentence text or tokenization-normalized whitespace can produce misses/misalignment if not guarded. The document should specify fallback/error strategy.

- CONCERN: File inventory counts are internally inconsistent.
  Section 14 says “New files (10)” but lists only two test files there (`implementation.md:605-618`), while later claims “Test files (10 new)” (`628-640`). This is editorial, but it makes implementation scope tracking ambiguous.

### Suggestions

- SUGGESTION: Add one explicit CLI integration test for dependency failure semantics.
  Current test list includes `test_toposort.py` and `test_cli_stage3.py` (`implementation.md:639-641`) but does not explicitly assert behavior for `--only chapters` or `--only silence` when deps are omitted. This is where the missing-dependency policy should be locked.

- SUGGESTION: Add a post-enrichment integrity check before writing `analysis.json`.
  After readability/chapter/pacing enrichment (`implementation.md:516-541`), validate:
  1. every block has required metrics keys,
  2. every block has a chapter after chapters runs,
  3. pacing key exists only when pacing ran.
  This will prevent silent partial writes.

- SUGGESTION: If `smoothed_arc` is retained, define exact interpolation/downsampling semantics.
  Section 7 says “linear interpolation” and `~200 points` (`implementation.md:334-335`, `361`, `589`) but doesn’t define behavior for short texts (`<200` points) or tie handling. A deterministic rule helps stable tests and frontend expectations.

### Praise

- PRAISE: B1 (readability/pacing contract) is resolved cleanly with an explicit enrichment pipeline and single canonical block metrics location.
  See Section 1 resolution and Section 11 merge flow (`implementation.md:10-14`, `516-537`).

- PRAISE: B3/B4 are resolved with a cleaner architecture.
  `chapters.requires()` now includes `silence` (`implementation.md:378-380`), and cross-analyzer mutation was replaced by explicit `block_to_chapter` mapping applied in CLI (`24-37`, `427`, `529-532`).

- PRAISE: The chapter detector now aligns with the stated manuscript format and avoids prior false-positive risks.
  Explicit marker requirement and heading-line title extraction (`implementation.md:85-94`, `119-121`) address the earlier broad-pattern concerns.

- PRAISE: Test scope is substantially improved and now includes toposort/CLI integration/regression checks.
  Section 14 introduces dedicated test files for ordering, CLI outputs, and enrichment behavior (`implementation.md:628-641`).
