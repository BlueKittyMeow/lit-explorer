# Stage 5 Plan Review — Codex

## Instructions

You are reviewing the **Stage 5 plan** for **lit-explorer**, a computational stylistics toolkit. Stage 5 scaffolds the SvelteKit frontend (the "Explorer"), builds the data loading layer, and delivers two working pages: a landing page (analysis listing) and an overview dashboard (metric cards + mini charts).

**This is a PLAN review, not a code review.** The code has not been written yet. Your job is to find gaps, risks, and ambiguities in the plan before implementation begins.

**Read the following files before starting your review:**

1. **The plan under review:**
   - `docs/build/stage-5/plan.md` — the full Stage 5 implementation plan

2. **Scriptorium architecture reference** (critical context):
   - `docs/build/stage-5/scriptorium-reference.md` — documents the conventions, types, and patterns from Scriptorium (a separate SvelteKit writing app) that lit-explorer must match for future component portability

3. **Spec context:**
   - `spec.md` lines 450–540 — SvelteKit Explorer section (pages, component design)
   - `spec.md` lines 592–616 — Development workflow Phase 2 (Explorer) and Phase 4 (Scriptorium Integration)
   - `spec.md` lines 643–678 — Scriptorium compatibility notes + architecture rationale

4. **JSON contract** (what the explorer consumes):
   - `spec.md` lines 171–335 — JSON schema for all five output files
   - `engine/src/lit_engine/output/json_export.py` — actual JSON writer (does it match the spec types?)

5. **Build overview:**
   - `docs/build/overview.md` — stage map and dependencies

**Your review should evaluate:**
- Do the TypeScript interfaces in the plan accurately mirror the JSON schema from spec.md? Any missing or mistyped fields?
- Is the data loading pattern (`$lib/server/data.ts` reading from disk) appropriate for SvelteKit? Any issues with `+page.server.ts` vs `+server.ts` for this use case?
- Does the routing structure (`/[slug]/overview`, `/[slug]/chapters`, etc.) make sense? Any SvelteKit routing gotchas?
- Are the Scriptorium conventions correctly followed? (Svelte 5 runes, `$props()`, adapter-node, TypeScript strict, custom CSS)
- Is Chart.js the right choice? Any concerns about SSR compatibility with SvelteKit?
- Is the testing strategy sufficient? What's missing?
- Are there accessibility, performance, or UX concerns?
- Does the plan correctly scope Stage 5 vs Stage 6? Is anything missing or premature?
- Any risks with the `ANALYSES_DIR` env var approach?
- Does the plan account for the actual engine output (from `json_export.py`) vs the spec schema? Any drift?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, reference the specific section of the plan
- Be specific and constructive

---

## Findings

### Blockers

- BLOCKER: Section 2 (`$lib/types/analysis.ts`) models `chapters.json` incorrectly for actual engine output.
  - Plan defines `Chapters` as:
    - `chapters: Chapter[]`
    - `block_to_chapter: Record<string, number>`
  - But current CLI intentionally writes `chapters.json` with `chapters` only (no `block_to_chapter`), and `spec.md` schema for `chapters.json` also shows only `chapters`.
  - Impact: Type/runtime contract drift at the explorer boundary; frontend code may assume `block_to_chapter` exists when it will be `undefined`.

- BLOCKER: Section 2 sentiment/manifest interfaces are incomplete versus real JSON payloads.
  - `SentimentPoint` is missing `neu`, and `Sentiment` is missing `smoothed_arc`.
  - `Manifest` is missing `warnings`.
  - These fields exist in engine output and are part of current contract surface used by CLI output files.
  - Impact: Type errors or silent unsafe casts in strict TypeScript.

### Concerns

- CONCERN: Section 3 uses `$env/static/private` for `ANALYSES_DIR` while describing deployment-time override behavior.
  - `static/private` bakes env values at build-time; this conflicts with runtime configurability expectations for `adapter-node` deployments.
  - For deployment/test override flexibility, this should be `dynamic/private` (or clearly documented as build-time-only).

- CONCERN: Section 3 default path `join(process.cwd(), '..', 'shared', 'analyses')` is fragile.
  - It depends on process launch directory assumptions (`explorer/` cwd).
  - In CI, PM2/systemd, Docker, or monorepo-root launches, this likely resolves incorrectly.

- CONCERN: Section 2 types are not resilient to partial analyses.
  - `Block.chapter` is typed as `number`, but analyzer data can be unset/`null` before chapter enrichment.
  - Even if Stage 5 targets full runs, explorer loaders should tolerate partially generated outputs.

- CONCERN: Section 3 path traversal guard (“reject slugs containing `..` or `/`”) is underspecified.
  - It does not explicitly cover all separator/encoding/normalization edge cases.
  - Safer pattern is: strict slug allowlist regex + `path.resolve` + prefix check against resolved `ANALYSES_DIR`.

- CONCERN: Section 10 test scope is too narrow for Stage 5 deliverables.
  - Plan tests only data loaders.
  - Stage 5 also introduces routed pages/layouts/components/theme behavior; without at least loader-route and rendering smoke tests, regressions in SSR/data wiring can pass unnoticed.

### Suggestions

- SUGGESTION: In Section 2, align interfaces to the true engine contract first, then add optional extension fields only where explicitly needed.
  - `Manifest`: add `warnings: string[]`.
  - `SentimentPoint`: add `neu: number`.
  - `Sentiment`: add `smoothed_arc`.
  - `Chapters`: remove `block_to_chapter` from file-facing type (or mark optional with clear “internal-only” comment).
  - `Block.chapter`: use `number | null`.

- SUGGESTION: In Section 3, split filesystem config into:
  - Required runtime env in production (`ANALYSES_DIR`), and
  - Deterministic local default in dev/tests via explicit test setup.
  - This removes `process.cwd()` coupling and makes deployment behavior predictable.

- SUGGESTION: Add lightweight schema validation at loader boundaries.
  - Even minimal runtime guards (or Zod schemas) in `$lib/server/data.ts` will catch engine/frontend drift early with actionable errors.

- SUGGESTION: Add Stage 5 integration tests beyond unit loaders.
  - `+page.server.ts` and `[slug]/overview/+page.server.ts` load tests.
  - Rendering smoke tests for landing and overview (data present + empty state).
  - One accessibility check for `MiniChart` fallback text/labels.

### Praise

- PRAISE: Stage scope split between Stage 5 (scaffold + listing + overview) and Stage 6 (interactive detail pages) is clear and appropriately incremental.

- PRAISE: The plan follows Scriptorium conventions closely (Svelte 5 runes, TypeScript strict, adapter-node, custom CSS, server-side loading pattern), which supports future component portability.

- PRAISE: The filesystem data-loading architecture (`$lib/server/data.ts` + `+page.server.ts`) is the right fit for this no-database explorer and keeps client bundles clean.

- PRAISE: Explicit security consideration (slug/path traversal guard) and fixture-driven loader tests are good foundations; they just need tightening as noted above.
