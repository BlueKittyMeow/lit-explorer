# Stage 4 Patch Review — Codex (Round 2)

## Instructions

You are reviewing the **Stage 4 patch** for **lit-explorer**. This patch addresses findings from the first review round. All 217 tests are passing.

**Read the following files before starting your review:**

1. **Patched code** (focus on these changes):
   - `engine/src/lit_engine/cli.py`:
     - Line 230: `prepare_text()` unpacking fix — was `formatted, clean, offset_map`, now `clean, formatted, offset_map` (BLOCKER fix)
     - Lines 118-121: All-analyzers-fail guard — exits 1 when `analyzer_names` is non-empty but `results` is empty
     - Lines 315-328: `_expand_with_deps()` — changed from `set` to insertion-ordered `list` for deterministic BFS output
     - Lines 348-352: `rerun` docstring — documents partial recompute behavior (does not merge with prior results)

2. **New tests** (2 added):
   - `engine/tests/test_extract.py` lines 146-188: `test_extract_analyze_boundary_equivalence` — runs `analyze` then `extract --json` for block 1 and last block, asserts word counts and total_blocks match
   - `engine/tests/test_cli_stage4.py` lines 174-189: `test_all_analyzers_fail_exits_nonzero` — patches texttiling to raise, asserts exit code != 0

3. **Context from Round 1** (for reference):
   - `docs/build/stage-4/codex-review.md` — your original findings
   - `docs/build/stage-4/gemini-review.md` — Gemini's original findings

**Your review should verify:**
- Does the `prepare_text()` fix resolve the blocker? Is unpacking now `(clean, formatted, offset_map)` matching the return signature in `texttiling.py:35-63`?
- Is the equivalence test sufficient to prevent regression? Does it compare the right values?
- Is the all-fail guard correct? Does `if analyzer_names and not results` cover the right cases (no false positives when `--only` is empty)?
- Is the deterministic BFS ordering correct? Does insertion-order `list` + `set` lookup preserve BFS traversal order?
- Is the `rerun` docstring accurate about partial recompute behavior?
- Any remaining issues from Round 1 that were not addressed?

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

- (none)

### Concerns

- CONCERN: The `extract` blocker fix is correct, but the new equivalence test is weaker than intended and can miss boundary drift.
  - `extract` now correctly unpacks `prepare_text()` as `clean, formatted, offset_map` (`engine/src/lit_engine/cli.py:235`), matching `prepare_text()` return order (`engine/src/lit_engine/analyzers/texttiling.py:35-63`).
  - However, `test_extract_analyze_boundary_equivalence` only compares `word_count` and `total_blocks` (`engine/tests/test_extract.py:181-188`) and does not compare extracted text against `analysis.json` offsets. It even loads `ms_text` but never uses it (`test_extract.py:165-166`), so offset mismatches with identical word counts would pass.

- CONCERN: Round-1 rerun semantics concern is documented, but behavioral spec mismatch remains.
  - The new docstring accurately describes partial recompute behavior (`engine/src/lit_engine/cli.py:348-352`), so the code/docs are now aligned.
  - But `spec.md` still describes rerun as “keeps existing results” (`spec.md:356-358`), which is not what current implementation does (`cli.py:354-365` delegates to fresh analyze subset).

### Suggestions

- SUGGESTION: Strengthen `test_extract_analyze_boundary_equivalence` with direct text equality checks.
  - For each tested block ID, compare:
    1. `extract --json` payload `text`
    2. `manuscript.txt[start_char:end_char]` from `analysis.json` block offsets
  - This would directly protect the boundary/offset invariant and catch regressions the current word-count check cannot.

- SUGGESTION: Resolve rerun contract explicitly in docs/spec.
  - Either update `spec.md` wording to “partial recompute” behavior, or change implementation to preserve/merge prior outputs so the command truly “keeps existing results.”

### Praise

- PRAISE: The original Stage 4 blocker is fixed correctly.
  - `extract` and `analyze` now use the same `prepare_text -> tokenize -> map_tile_offsets -> build_blocks` data flow (`engine/src/lit_engine/cli.py:235, 242-260` with `texttiling.py:35-63, 66-129`).

- PRAISE: The all-analyzers-fail guard is implemented in the right place and behaves as expected.
  - Guard: `if analyzer_names and not results` (`cli.py:118-121`) after per-analyzer loop.
  - Test coverage: `test_all_analyzers_fail_exits_nonzero` (`engine/tests/test_cli_stage4.py:174-189`).

- PRAISE: `_expand_with_deps()` now has deterministic traversal order and preserves BFS layering.
  - Uses `seen` set for dedupe + ordered `order` list + FIFO queue (`engine/src/lit_engine/cli.py:320-335`).

- PRAISE: `rerun` docstring is accurate to actual behavior and removes ambiguity from Round 1.
  - Documented partial recompute semantics (`engine/src/lit_engine/cli.py:348-352`).
