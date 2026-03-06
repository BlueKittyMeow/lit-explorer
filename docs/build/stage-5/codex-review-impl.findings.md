### [BLOCKER] Overview dashboard is materially under-implemented versus Stage 5 plan

**File:** [explorer/src/routes/[slug]/overview/+page.svelte](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.svelte)  
**Line(s):** 47–118

The page delivers only 2 mini charts and omits several planned Stage 5 requirements: no dialogue-ratio metric card, no chapter word-count chart, no character verb-domain chart, and no notable callouts from `analysis.notable` (longest sentence / highest MATTR / highest fog). It also does not make mini charts/callouts clickable to Stage 6 placeholder routes.  
Recommended fix: implement the missing metric cards/charts/callouts and wrap them with links to `/[slug]/chapters`, `/[slug]/characters`, and `/[slug]/blocks` per the plan.

### [CONCERN] Theme flash-prevention script does not handle persisted `system` preference

**File:** [explorer/src/app.html](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/app.html)  
**Line(s):** 9–12

If `localStorage.theme === 'system'` and OS theme is dark, the script does not apply `.dark` before hydration, causing a flash of incorrect theme.  
Recommended fix: include explicit `theme === 'system'` handling in the pre-hydration check.

### [CONCERN] Planned route-loader integration tests are missing

**File:** [explorer/tests](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests)  
**Line(s):** N/A (missing `tests/integration/routes.test.ts`)

Stage 5 plan calls for route-loader integration coverage (`+page.server.ts`, `[slug]/+layout.server.ts`, `[slug]/overview/+page.server.ts`), but only unit/component tests are present.  
Recommended fix: add integration tests for valid slug load, invalid slug handling, and landing empty-state behavior.

### [CONCERN] Loader boundary relies on unchecked casts from untrusted JSON

**File:** [explorer/src/lib/server/data.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts)  
**Line(s):** 42

`JSON.parse(content) as T` trusts runtime shape without validation. Corrupt/drifted JSON can pass compile-time typing and fail later in rendering with less actionable errors.  
Recommended fix: add runtime validation (lightweight guards or schema validation) at loader boundaries and raise structured SvelteKit errors.

### [CONCERN] Analysis sub-nav trusts `manifest.slug` for routing

**File:** [explorer/src/routes/[slug]/+layout.svelte](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/+layout.svelte)  
**Line(s):** 7–10

Sub-nav links are built from `data.manifest.slug` instead of the route param slug. If manifest slug is stale/corrupt, in-app navigation can jump to wrong routes.  
Recommended fix: use canonical route params for link generation (or at minimum assert equality and fall back to params).

### [CONCERN] Overview request does redundant manifest I/O

**File:** [explorer/src/routes/[slug]/+layout.server.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/+layout.server.ts), [explorer/src/routes/[slug]/overview/+page.server.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.server.ts), [explorer/src/lib/server/data.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts)  
**Line(s):** 5; 5; 105–113

`[slug]/+layout.server.ts` loads `manifest`, then overview `+page.server.ts` calls `loadAllData()` which loads `manifest` again. This duplicates disk reads on every overview request.  
Recommended fix: reuse parent layout data for `manifest` and load only the other four files in overview loader.

### [SUGGESTION] `listAnalyses()` does serialized manifest reads and no caching

**File:** [explorer/src/lib/server/data.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts)  
**Line(s):** 61–77

Each manifest is loaded sequentially in a loop; landing-page latency will scale linearly with analysis count.  
Suggestion: use `Promise.allSettled` with bounded concurrency and consider short-lived server-side caching.

### [SUGGESTION] Chart bundle can likely be reduced

**File:** [explorer/src/lib/components/MiniChart.svelte](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte)  
**Line(s):** 2

Using `chart.js/auto` pulls all chart registrations. For this page’s limited chart types, manual registration may reduce client bundle size.  
Suggestion: register only used controllers/elements/scales.

### [PRAISE] Path traversal guard is properly layered and tested

**File:** [explorer/src/lib/server/data.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts), [explorer/tests/unit/data.test.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/data.test.ts)  
**Line(s):** 20, 26–35; 146–170

The allowlist regex + resolved path + separator-bound prefix check is strong defense-in-depth, and traversal inputs are covered by tests.

### [PRAISE] Round 1/2 critical schema and reactivity fixes are present

**File:** [explorer/src/lib/types/analysis.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/types/analysis.ts), [explorer/src/lib/components/MiniChart.svelte](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte), [explorer/src/routes/+layout.svelte](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/+layout.svelte), [explorer/src/lib/server/data.ts](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts)  
**Line(s):** 16, 28–30, 43, 80, 152, 170, 173–174; 15–37; 4–7, 9, 16–20; 9, 22–24

Key earlier findings were addressed: `warnings`, `neu`, `smoothed_arc`, nullable extremes, optional readability enrichment fields, optional pacing, reactive chart updates, dynamic env usage, and 3-state theme model.