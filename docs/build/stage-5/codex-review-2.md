# Stage 5 Plan Review (Round 2) — Codex

## Instructions

You are reviewing the **updated Stage 5 plan** for **lit-explorer** after Round 1 findings have been addressed. Your job is to verify the fixes landed correctly and flag any remaining issues.

**Round 1 findings that were addressed:**
- BLOCKER: `Chapters` interface included `block_to_chapter` but engine writes only `chapters` → removed from type, added explanatory comment
- BLOCKER: `SentimentPoint` missing `neu` → added
- BLOCKER: `Sentiment` missing `smoothed_arc` → added `SmoothedPoint` interface + field
- BLOCKER: `Manifest` missing `warnings` → added `warnings: string[]`
- CONCERN: `$env/static/private` → switched to `$env/dynamic/private`
- CONCERN: `ANALYSES_DIR` fragile default → `getAnalysesDir()` per-request, `resolve()` instead of `join()`
- CONCERN: `Block.chapter` typed as `number` → now `number | null`
- CONCERN: Path traversal guard underspecified → strict allowlist regex + `path.resolve()` + prefix check
- CONCERN: Test scope too narrow → added route loader integration tests + component smoke tests
- SUGGESTION: Align interfaces to true engine contract → all fields now match verified engine output
- SUGGESTION: `loadAllData()` helper → added
- Sentiment extremes now `| null` (matches engine `_empty_result`)

**Deferred:**
- Zod validation — fixtures + TypeScript types catch drift; revisit if real issues arise

**Read the following files:**

1. `docs/build/stage-5/plan.md` — the updated plan (verify all sections)
2. `docs/build/stage-5/scriptorium-reference.md` — Scriptorium architecture context
3. `engine/src/lit_engine/output/json_export.py` — actual JSON writer (verify `warnings` field)
4. `engine/src/lit_engine/analyzers/sentiment.py` — verify `smoothed_arc` shape, `neu` in arc entries
5. `engine/src/lit_engine/analyzers/chapters.py` — verify `block_to_chapter` is internal only
6. `engine/src/lit_engine/cli.py` lines 130–170 — enrichment pipeline, verify `chapters.json` payload construction
7. `engine/src/lit_engine/analyzers/texttiling.py` line 236 — verify `Block.chapter` default is `None`

**Your review should verify:**
- Are all Round 1 blockers resolved? Cross-check each interface field against the actual engine code.
- Is `$env/dynamic/private` correctly used (not cached at module level)?
- Does the path traversal guard (allowlist regex + resolve + prefix check) cover the edge cases from Round 1?
- Are the new test categories (route loaders, component smoke tests) well-scoped?
- Any new issues introduced by the fixes?
- Any remaining schema drift between plan interfaces and engine output?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- Be specific and constructive

---

## Findings

### Blockers

- BLOCKER: Remaining schema drift in Section 2 (`$lib/types/analysis.ts`) for `analysis.json`.
  - `BlockMetrics` still omits enriched readability fields added by the CLI pipeline: `coleman_liau`, `smog`, `ari` (engine enrichment in `cli.py`).
  - `Analysis` still omits top-level `pacing`, which is merged into `analysis.json` by the CLI when pacing runs.
  - This means the plan’s interfaces still do not fully match real engine output for common full runs.

### Concerns

- CONCERN: Section 3 fallback path remains deployment-fragile despite the `resolve()` improvement.
  - `getAnalysesDir()` uses `resolve(process.cwd(), '..', 'shared', 'analyses')` when env is unset.
  - This still assumes an `explorer/` working directory and can misresolve when launched from monorepo root or service managers.

- CONCERN: Section 3 path-prefix guard wording is still slightly underspecified.
  - The plan says “verify resolved path starts with `ANALYSES_DIR` prefix”; this should explicitly require normalized base path + path separator boundary to avoid false-positive prefix matches (`/base/analyses2` vs `/base/analyses`).

### Suggestions

- SUGGESTION: Extend Section 2 `analysis` types to match current engine shape:
  - Add `coleman_liau`, `smog`, `ari` to `BlockMetrics`.
  - Add `PacingData` interface and `pacing?: PacingData` on `Analysis` (optional if supporting partial runs).

- SUGGESTION: Tighten Section 3 path safety wording to an explicit recipe:
  - `base = resolve(getAnalysesDir())`
  - `candidate = resolve(base, slug)`
  - allow only if `candidate === base || candidate.startsWith(base + sep)`

- SUGGESTION: For fallback directory behavior, prefer explicit env in production and test harnesses, treating the computed fallback as dev-only convenience.

### Praise

- PRAISE: Round-1 blockers were largely fixed correctly in the updated plan.
  - `Manifest.warnings` added.
  - `SentimentPoint.neu` and `Sentiment.smoothed_arc` added.
  - `Sentiment.extremes` now nullable.
  - `Chapters` type now reflects file output (`chapters` only) with a clear internal-note about `block_to_chapter`.
  - `Block.chapter` now `number | null`.

- PRAISE: Section 3 improved meaningfully with `$env/dynamic/private`, per-request `getAnalysesDir()`, and a defense-in-depth traversal approach (allowlist + resolve + prefix check).

- PRAISE: Section 10 test strategy is now much stronger, adding route-loader integration and component smoke tests alongside loader unit tests.
