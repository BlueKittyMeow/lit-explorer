# Stage 5 Implementation Review — Codex

## Instructions

You are reviewing the **Stage 5 implementation** for **lit-explorer**, a computational stylistics toolkit. Stage 5 scaffolded the SvelteKit frontend ("Explorer"), built the data loading layer, and delivered two working pages: a landing page (analysis listing) and an overview dashboard (metric cards + mini charts).

**This is a CODE review.** The implementation is complete with 26 tests passing, svelte-check clean (0 errors, 0 warnings), and the production build succeeding. Your job is to find bugs, security issues, type mismatches, missing edge cases, and deviations from the plan.

**Read the following files before starting your review:**

### Plan and spec context
1. `docs/build/stage-5/plan.md` — the plan this code implements
2. `docs/build/stage-5/scriptorium-reference.md` — Scriptorium conventions we must match
3. `spec.md` lines 450–540 — SvelteKit Explorer section
4. `spec.md` lines 643–678 — Scriptorium compatibility notes

### Implementation files to review

**TypeScript interfaces:**
5. `explorer/src/lib/types/analysis.ts` — all 17 interfaces matching the JSON contract

**Data loading layer:**
6. `explorer/src/lib/server/data.ts` — server-only JSON file loaders with path traversal guard

**Components:**
7. `explorer/src/lib/components/MetricCard.svelte`
8. `explorer/src/lib/components/MiniChart.svelte`
9. `explorer/src/lib/components/AnalysisCard.svelte`

**Routes:**
10. `explorer/src/routes/+layout.svelte` — root layout (top bar, theme toggle)
11. `explorer/src/routes/+page.svelte` — landing page
12. `explorer/src/routes/+page.server.ts` — landing page data loader
13. `explorer/src/routes/[slug]/+layout.svelte` — analysis sub-nav
14. `explorer/src/routes/[slug]/+layout.server.ts` — manifest loader
15. `explorer/src/routes/[slug]/overview/+page.svelte` — overview dashboard
16. `explorer/src/routes/[slug]/overview/+page.server.ts` — full data loader
17. `explorer/src/routes/[slug]/chapters/+page.svelte` — placeholder
18. `explorer/src/routes/[slug]/characters/+page.svelte` — placeholder
19. `explorer/src/routes/[slug]/blocks/+page.svelte` — placeholder

**Styles and HTML:**
20. `explorer/src/app.css` — global styles, CSS custom properties, theming
21. `explorer/src/app.html` — HTML shell with theme flash prevention

**Tests:**
22. `explorer/tests/unit/data.test.ts` — 15 data loader tests
23. `explorer/tests/unit/components.test.ts` — 11 component smoke tests
24. `explorer/tests/fixtures/test-analysis/*.json` — 5 fixture files

**Config:**
25. `explorer/vite.config.ts` — vitest + browser resolve conditions
26. `explorer/svelte.config.js` — adapter-node
27. `explorer/package.json` — dependencies

## Review criteria

Focus on these areas:

### 1. Plan compliance
- Does the implementation match the plan? Missing features? Deviations?
- Are all planned test categories present (unit, component, integration)?
- Were review findings from rounds 1 and 2 (`gemini-review.md`, `codex-review.md`, `gemini-review-2.md`, `codex-review-2.md`) actually addressed in the code?

### 2. Type safety and data integrity
- Do TypeScript interfaces match actual engine JSON output exactly?
- Cross-reference `explorer/tests/fixtures/test-analysis/*.json` with interfaces — any mismatches?
- Are there any `as` casts that could mask runtime errors?
- Does `loadAllData()` handle partial failures (e.g., 4 of 5 files present)?

### 3. Security
- Is the path traversal defense-in-depth actually layered? (regex + resolve + separator)
- Could a crafted slug bypass the guard?
- Any XSS vectors from rendering user-authored text (previews, titles)?
- Is JSON.parse on untrusted file content safe?

### 4. Error handling
- What happens when `loadAllData()` fails mid-parallel? Does `Promise.all` reject cleanly?
- Does `listAnalyses()` silently skip broken manifests, or does one bad entry break the listing?
- Are SvelteKit `error()` calls used consistently?

### 5. Performance
- Is `loadAllData()` reading 5 files per page load acceptable, or should there be caching?
- Is `listAnalyses()` scanning the directory every time? Impact with many analyses?
- Chart.js bundle size — is tree-shaking working with `chart.js/auto`?

### 6. Test quality
- Are tests testing behavior or implementation details?
- Any missing edge cases (e.g., empty analysis, 0-block analysis, missing optional fields)?
- Do component tests verify accessibility attributes?

## Output format

Use these severity levels:

- **BLOCKER** — Must fix before shipping. Bugs, security issues, data integrity problems.
- **CONCERN** — Should fix. Gaps that could cause issues in production or Stage 6.
- **SUGGESTION** — Nice to have. Improvements for code quality or developer experience.
- **PRAISE** — Things done well. Patterns to keep.

For each finding:
```
### [SEVERITY] Short title

**File:** `path/to/file`
**Line(s):** N–M (if applicable)

Description of the issue and recommended fix.
```

---

*Write your findings below this line.*
