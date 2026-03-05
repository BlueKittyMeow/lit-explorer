# Stage 4 Code Review — Gemini

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

### Blockers

- 🔴 **BLOCKER**: **Incorrect Unpacking in `extract` command** (`engine/src/lit_engine/cli.py:212`).
  The `prepare_text` function in `texttiling.py` returns `(clean, formatted, offset_map)`, but the `extract` command in `cli.py` unpacks it as `formatted, clean, offset_map = prepare_text(text)`. This swaps the clean and formatted text variables.
  - **Impact**: `TextTilingTokenizer` runs on the non-formatted text (fewer newlines), and `map_tile_offsets` is called with swapped arguments, leading to incorrect character offsets. The resulting `block_text` extracted at line 253 will contain extra newlines and potentially drifted content.
  - **Fix**: Change line 212 to `clean, formatted, offset_map = prepare_text(text)`.

### Concerns

- 🟡 **CONCERN**: **Incomplete Error Resilience in Enrichment Pipeline** (`engine/src/lit_engine/cli.py:115-128`).
  The enrichment pipeline correctly checks for the presence of `readability` and `texttiling` results. however, if an analyzer fails (e.g., `agency` fails), it is not added to the `results` dict. While the `analyze` command handles this gracefully for output writing, some downstream analyzers might depend on the *data* from failed upstream analyzers if they don't explicitly check context presence.
  - **Verification**: `ChaptersAnalyzer.analyze` (Stage 3) needs to be robust against missing keys in `context`. The current CLI ensures that if a required dependency is missing from the *requested set*, it fails early, but it doesn't fail early if a dependency *crashes during runtime*. This is acceptable for a "best-effort" pipeline, but worth noting.

### Suggestions

- 🟢 **SUGGESTION**: **Refactor `extract` to avoid logic duplication** (`engine/src/lit_engine/cli.py:228-242`).
  The `extract` command duplicates the fallback logic and block building logic from `TextTilingAnalyzer.analyze`. While acceptable for a prototype, moving this logic into a shared method in `TextTilingAnalyzer` (e.g., a `get_blocks` method) would improve maintainability and ensure consistency between `analyze` and `extract`.
- 🟢 **SUGGESTION**: **Improve `test_extract` to verify text integrity**.
  The current tests for `extract` verify that the command runs and returns the correct schema, but they don't verify that the extracted `text` matches the original manuscript at the specified offsets. Adding a test that asserts `manuscript[start:end] == extracted_text` (after fixing the blocker) would prevent regressions in offset mapping.

### Praise

- 🟢 **PRAISE**: **Transitive Dependency Resolution** (`engine/src/lit_engine/cli.py:302-320`).
  The BFS implementation in `_expand_with_deps` combined with the topological sort in `analyze` is a very elegant solution for the `rerun` command. It ensures that re-running a complex aggregator like `chapters` automatically pulls in all necessary data.
- 🟢 **PRAISE**: **Robust Error Handling** (`engine/src/lit_engine/cli.py:102-107`).
  Catching `Exception` but not `BaseException` is correct Python practice, ensuring `KeyboardInterrupt` still works. The persistence of error messages into the `manifest.json` warnings is excellent for debugging.
- 🟢 **PRAISE**: **End-to-End Test Structure** (`engine/tests/test_specimen_e2e.py`).
  The use of a class-scoped fixture to run the pipeline once for multiple assertions is efficient and well-implemented. The coverage of all 6 output files and key manifest metrics provides high confidence in the overall system.
