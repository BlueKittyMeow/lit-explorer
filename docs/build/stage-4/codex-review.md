# Stage 4 Code Review — Codex

## Instructions

You are reviewing the **Stage 4 implementation** for **lit-explorer**, a computational stylistics toolkit. Stage 4 adds two new CLI commands (`extract`, `rerun`), per-analyzer error handling, and end-to-end validation against The Specimen manuscript. All code is written and passing (215 tests).

**Read the following files before starting your review:**

1. **The code under review** (Stage 4 additions):
   - `engine/src/lit_engine/cli.py` — the main file modified:
     - Lines 102-107: per-analyzer error handling (try/except around `analyzer.analyze()`)
     - Lines 204-299: `extract` command (re-tile + block extraction with human/JSON output)
     - Lines 302-320: `_expand_with_deps()` helper (BFS transitive dependency expansion)
     - Lines 323-345: `rerun` command (delegates to `analyze` via `ctx.invoke`)
   - `engine/pyproject.toml` — `slow` pytest marker added

2. **Stage 4 test files** (28 new tests):
   - `engine/tests/test_extract.py` — 9 tests: valid block, bounds checking, JSON output, sentence breakdown
   - `engine/tests/test_cli_stage4.py` — 11 tests: `_expand_with_deps`, rerun command, analyzer error handling
   - `engine/tests/test_specimen_e2e.py` — 8 tests: full pipeline against The Specimen (skips if not available)

3. **Context** (already passing, for reference):
   - `engine/src/lit_engine/analyzers/__init__.py` — `_REGISTRY`, `resolve_execution_order()`, `get_analyzer()`
   - `engine/src/lit_engine/analyzers/texttiling.py` — `prepare_text()`, `map_tile_offsets()`, `build_blocks()` (reused by `extract`)
   - `engine/src/lit_engine/config.py` — `merge_config()`, fallback window/smoothing defaults
   - `spec.md` lines 341-364 — CLI interface specification

**Your review should verify:**
- Is the `extract` command producing the same block boundaries as `analyze`? (Both must use `prepare_text` → `TextTilingTokenizer` → `map_tile_offsets` → `build_blocks`.)
- Is the `--block` 1-based ID convention correct and consistent with `analysis.json`?
- Does `_expand_with_deps` correctly resolve transitive dependencies? (e.g., `chapters` → `{texttiling, agency, dialogue, sentiment, silence, chapters}`)
- Does `rerun` correctly delegate to `analyze` via `ctx.invoke`? Any edge cases with Click context passing?
- Is the error handling in the analyzer loop sufficient? (`except Exception` catches the right scope, doesn't swallow `KeyboardInterrupt`)
- Do downstream analyzers and the enrichment pipeline handle missing results gracefully when an upstream analyzer fails?
- Are the test fixtures adequate? (Especially: is the extract fixture text large enough for TextTiling with fallback params?)
- Is the Specimen e2e test well-structured? (Class-scoped fixture, skip logic, reasonable assertions)
- Any missing edge cases, dead code paths, or spec compliance issues?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, cite the specific file and line numbers
- Be specific and constructive

---

## Findings

(Codex: record your findings here)

### Blockers

- BLOCKER: `extract` is not using the same text-preparation flow as `analyze` due swapped `prepare_text()` unpacking, so block boundaries/offsets can diverge.
  - In `extract`, `prepare_text()` is unpacked as `formatted, clean, offset_map` (`engine/src/lit_engine/cli.py:230`).
  - But `prepare_text()` returns `(clean_text, formatted_text, offset_map)` (`engine/src/lit_engine/analyzers/texttiling.py:35-63`).
  - This means `TextTilingTokenizer` in `extract` runs on the wrong text variant and `map_tile_offsets()` receives mismatched arguments (`cli.py:239`, `254-255`), violating the requirement that `extract` and `analyze` use the same boundary pipeline.

### Concerns

- CONCERN: `rerun` semantics do not match the spec phrase “keeps existing results”; it re-invokes `analyze` on a subset and rewrites manifest from that subset.
  - Spec CLI contract: `lit-engine rerun ...` “keeps existing results” (`spec.md:356-358`).
  - Current `rerun` just expands deps and delegates to `analyze` (`engine/src/lit_engine/cli.py:340-353`), and `analyze` writes a fresh manifest using `analyzers_run=list(results.keys())` (`cli.py:194`) and `chapter_count` only from current run (`182-185`).
  - Result: rerunning one analyzer can produce a manifest that no longer reflects previously generated outputs in the folder.

- CONCERN: Analyzer-level failure handling can hide total pipeline failure by still exiting 0.
  - `analyze` catches per-analyzer exceptions and continues (`cli.py:105-110`), but never returns non-zero even if all requested analyzers fail.
  - This is resilient, but automation may interpret a completely failed run as success.

- CONCERN: `_expand_with_deps()` returns `list(set)` order, which is non-deterministic.
  - Implementation accumulates into a set and returns `list(needed)` (`cli.py:315-329`).
  - Toposort later stabilizes execution order, but CLI logging/`--only` construction in `rerun` (`cli.py:343`) can vary run-to-run, making debugging noisier.

- CONCERN: Stage 4 tests do not currently verify extract/analyze boundary equivalence (the key behavioral requirement).
  - `test_extract.py` validates structure/range/output formatting (`engine/tests/test_extract.py:46-156`) but does not compare block text/IDs against `analysis.json` generated by `analyze`.
  - This gap is why the `prepare_text()` unpacking regression was not caught.

### Suggestions

- SUGGESTION: Add one golden-path equivalence test: run `analyze` on fixture, then `extract --block N --json`, assert extracted text/word_count/sentence_count match `analysis.json` block `N` slice from `manuscript.txt`.
  - Target files: `engine/tests/test_extract.py`, `engine/tests/test_cli_stage4.py`.

- SUGGESTION: In `analyze`, track failure count and return exit code 1 when all requested analyzers fail (or when any “required output” analyzer fails).
  - This preserves per-analyzer resilience while making CI/automation outcomes accurate.

- SUGGESTION: For `rerun`, either:
  1) document that it performs a partial recompute and overwrites manifest to that subset, or
  2) load prior manifest/results and merge metadata to truly “keep existing results.”

### Praise

- PRAISE: `_expand_with_deps()` correctly resolves transitive dependencies for real Stage 3 graph shapes (e.g., `chapters` includes `texttiling`, `agency`, `dialogue`, `sentiment`, `silence`, and itself).
  - Implementation: `engine/src/lit_engine/cli.py:310-329`.
  - Validated by test: `engine/tests/test_cli_stage4.py:51-56`.

- PRAISE: Per-analyzer exception handling is scoped correctly to avoid swallowing `KeyboardInterrupt`/`SystemExit`.
  - Handler catches `Exception` only (`cli.py:107`), not `BaseException`, so user interrupts still propagate.

- PRAISE: The Specimen end-to-end test structure is solid: class-scoped run fixture, skip-if-missing gate, and meaningful output assertions.
  - `engine/tests/test_specimen_e2e.py:15-31` and checks `33-97`.

- PRAISE: `pyproject.toml` marker setup for slow tests is correct and practical.
  - `engine/pyproject.toml:28-30`.
