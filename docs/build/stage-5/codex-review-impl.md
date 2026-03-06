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

### [BLOCKER] MiniChart does not react to prop changes (stale chart data)

**File:** `explorer/src/lib/components/MiniChart.svelte`  
**Line(s):** 15–26

`Chart` is created once in `onMount` and never updated when `data`, `options`, or `type` props change. In SvelteKit, navigating between routes with the same component and different params can update props without remounting, which risks showing stale chart data.  
Recommended fix: keep a chart instance and update it in a `$effect` when reactive props change (or destroy/recreate on change).

### [CONCERN] Runtime env handling deviates from plan and SvelteKit convention

**File:** `explorer/src/lib/server/data.ts`  
**Line(s):** 21–24

The loader uses `process.env.ANALYSES_DIR` directly. The Stage 5 plan/r2 explicitly switched to `$env/dynamic/private` for runtime configurability under adapter-node.  
Recommended fix: import `env` from `$env/dynamic/private` and read `env.ANALYSES_DIR` in `getAnalysesDir()`.

### [CONCERN] Planned route-loader integration tests are missing

**File:** `explorer/tests/`  
**Line(s):** N/A (missing `tests/integration/routes.test.ts`)

The implementation includes unit loader tests and component tests, but no route-loader integration test file despite plan scope. This leaves SSR route wiring (`+page.server.ts`, `[slug]/+layout.server.ts`, `[slug]/overview/+page.server.ts`) unverified.  
Recommended fix: add integration tests covering valid slug, invalid slug, and empty-state route loading.

### [CONCERN] MiniChart accessibility smoke test is missing despite plan/test claims

**File:** `explorer/tests/unit/components.test.ts`  
**Line(s):** 1–6

The test file explicitly skips `MiniChart` (“not tested here”), but Stage 5 test scope calls for component smoke checks including chart accessibility wrapper behavior.  
Recommended fix: add at least a lightweight render test for `<figure role="img" aria-label=...>` and `<figcaption class="sr-only">`.

### [CONCERN] Theme toggle does not implement the planned dark/light/system behavior

**File:** `explorer/src/routes/+layout.svelte`  
**Line(s):** 5–11, 25–27

Current implementation is a binary dark/light toggle only. Plan specified dark/light/system mode parity with Scriptorium conventions.  
Recommended fix: implement a 3-state theme preference (`light` | `dark` | `system`) and reflect it in UI and persisted setting.

### [CONCERN] Listing trusts `manifest.slug` instead of directory slug

**File:** `explorer/src/lib/server/data.ts`  
**Line(s):** 64–67

`listAnalyses()` iterates safe directory names but then uses `manifest.slug` for returned links. If manifest content is stale/corrupt/malicious, generated hrefs can be wrong or unexpected.  
Recommended fix: use the validated directory entry as canonical `slug` for routing, optionally warn if it differs from manifest slug.

### [CONCERN] Type contract is stricter than real engine failure modes

**File:** `explorer/src/lib/types/analysis.ts`  
**Line(s):** 20–31  
**Related engine behavior:** `engine/src/lit_engine/cli.py:125-134`

`BlockMetrics` requires enriched readability fields (`coleman_liau`, `smog`, `ari`), but CLI only injects them when readability succeeds. Engine can continue after analyzer failure, so these keys may be absent in real outputs.  
Recommended fix: mark these fields optional or add runtime normalization in loader for partial analyses.

### [SUGGESTION] Improve loader diagnostics for skipped manifests

**File:** `explorer/src/lib/server/data.ts`  
**Line(s):** 74–76

`listAnalyses()` silently swallows all manifest read/parse errors. This is resilient, but operationally opaque when an analysis disappears from the landing page due to corruption.  
Suggestion: log server-side warnings for skipped entries (at least in dev mode).

### [SUGGESTION] Consider replacing global browser resolve condition with test-scoped config

**File:** `explorer/vite.config.ts`  
**Line(s):** 11–13

Global `resolve.conditions = ['browser']` can influence SSR module resolution beyond test concerns. Build currently passes, but this is a fragile global override.  
Suggestion: scope browser conditions to tests only (or remove unless demonstrably needed).

### [PRAISE] Path traversal defense is layered and correctly implemented

**File:** `explorer/src/lib/server/data.ts`  
**Line(s):** 19, 26–35

The combination of strict slug allowlist, resolved-path construction, and separator-bound prefix validation is a strong defense-in-depth approach.

### [PRAISE] Interfaces are substantially aligned with current engine schema

**File:** `explorer/src/lib/types/analysis.ts`  
**Line(s):** 4–196

Stage 5 round-1/2 schema fixes are present: `manifest.warnings`, `sentiment.arc.neu`, `smoothed_arc`, nullable sentiment extremes, `chapter: number | null`, chapters file shape, and pacing typing.

### [PRAISE] Baseline quality gates are in place and passing

**File:** `explorer/package.json`, `explorer/tests/unit/*.test.ts`
**Line(s):** `package.json:6-15`, `data.test.ts`, `components.test.ts`

`vitest`, `svelte-check`, and production build all pass; loader tests cover path traversal and missing-file behavior, providing a solid foundation for Stage 6.
