# Stage 5 Plan Review — Gemini

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

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, reference the specific section of the plan
- Be specific and constructive

---

## Findings

### Blockers

- 🔴 **BLOCKER**: **`SentimentPoint` interface missing `neu` field** (Section 2).
  The `SentimentAnalyzer` in Stage 3 explicitly adds a `neu` field to each arc entry, and the `ChapterSentiment` interface in the plan correctly includes it. However, the `SentimentPoint` interface at line 128 is missing `neu: number`. This will cause TypeScript errors when loading the full sentiment arc.
  - **Fix**: Add `neu: number;` to the `SentimentPoint` interface.

### Concerns

- 🟡 **CONCERN**: **`Block.chapter` type should allow `null`** (Section 2).
  In `analysis.json`, the `chapter` field for a block is `null` until the `ChaptersAnalyzer` runs. While the CLI currently ensures enrichment, the frontend types should be resilient to incomplete analyses or the "Stage 1 only" state.
  - **Fix**: Change to `chapter: number | null;` in the `Block` interface.
- 🟡 **CONCERN**: **`ANALYSES_DIR` relative path fragility** (Section 3).
  The default path `join(process.cwd(), '..', 'shared', 'analyses')` assumes the Node process is started exactly from the `explorer/` directory. In many CI/CD or Docker environments, the process may start from the monorepo root.
  - **Suggestion**: Use a more robust path resolution or ensure the `ANALYSES_DIR` env var is mandatory in the `adapter-node` production environment.

### Suggestions

- 🟢 **SUGGESTION**: **Add `AnalysisData` hydration helper** (Section 2).
  The `AnalysisData` interface is a great "mega-object" for the overview page. Adding a helper function in `data.ts` called `loadAllData(slug: string)` would clean up the `+page.server.ts` loaders by centralizing the `Promise.all` logic.
- 🟢 **SUGGESTION**: **Accessibility for Chart.js** (Section 8).
  `MiniChart.svelte` renders a raw `<canvas>`. For Scriptorium-grade quality, we should include a visually hidden `<table>` or `<ul>` description of the data within the canvas tag for screen readers.
- 🟢 **SUGGESTION**: **Zod validation** (Section 3).
  Since the explorer reads from a "foreign" data source (the Python engine's files), using a library like `zod` to validate the JSON at the boundary of `data.ts` would provide much better error messages than simple TypeScript interface casts if the schema ever drifts.

### Praise

- 🟢 **PRAISE**: **Exact Schema Mirroring**. Aside from the one missing field, the interfaces perfectly capture the nuances of the engine's output (e.g., distinguishing between `BlockMetrics` and chapter-level metrics).
- 🟢 **PRAISE**: **Path Traversal Guard**. Mentioning the rejection of slugs with `..` or `/` shows a high level of security awareness for a data-loading layer.
- 🟢 **PRAISE**: **Theme Flash Prevention**. Reusing the Scriptorium inline script pattern in `app.html` ensures a professional, polished feel from the first load.
