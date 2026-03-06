### [BLOCKER] Block Chart Rebuilds On Every Selection Change
`selectedBlockId` is read inside the chart-construction `$effect`, so every block change destroys/recreates the full Chart.js instance instead of only updating point styling. This defeats the intended incremental-update effect and will scale poorly on larger analyses.  
Evidence: [blocks/+page.svelte#L70](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L70), [blocks/+page.svelte#L84](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L84), [blocks/+page.svelte#L155](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L155)

### [CONCERN] Async Chart Imports Are Not Cancellation-Safe
Each chart effect creates the chart inside `import(...).then(...)` without a cancellation guard. If the effect is invalidated before the promise resolves, a stale chart can still be created after cleanup.  
Evidence: [VerbDomainChart.svelte#L17](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/VerbDomainChart.svelte#L17), [MiniChart.svelte#L19](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte#L19), [blocks/+page.svelte#L77](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L77)

### [CONCERN] `from` Query Param Is Not Sanitized/Clamped
`from` is parsed directly and can become `NaN` or out-of-range. UI then mixes fallback panel state with invalid selection state (chart highlight/nav disabled logic keyed off raw `selectedBlockId`).  
Evidence: [blocks/+page.svelte#L23](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L23), [blocks/+page.svelte#L29](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L29), [blocks/+page.svelte#L214](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L214)

### [CONCERN] Chart Colors Don’t React To Runtime Theme Changes
Theme can be toggled at runtime, but chart color state is resolved once per component mount with no reactive trigger on theme flips, so charts can remain in old-theme colors.  
Evidence: [routes/+layout.svelte#L16](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/+layout.svelte#L16), [characters/+page.svelte#L10](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/characters/+page.svelte#L10), [overview/+page.svelte#L26](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/overview/+page.svelte#L26), [BlockMetricsPanel.svelte#L10](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/BlockMetricsPanel.svelte#L10)

### [CONCERN] Chapters Sentiment Cell Is Effectively Color-Only
Sentiment is conveyed via a dot + `title` tooltip, but there is no readable cell text for screen readers and non-hover contexts.  
Evidence: [chapters/+page.svelte#L114](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/chapters/+page.svelte#L114)

### [SUGGESTION] Stage 6 Tests Are Mostly Smoke-Level For Interactions
New tests validate rendering but miss key behavior regressions: keyboard nav in block explorer, metric-switch chart updates, selection sync from query param, and exact `aria-sort` transitions.  
Evidence: [block-explorer.test.ts#L137](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/block-explorer.test.ts#L137), [chapters-page.test.ts#L89](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/chapters-page.test.ts#L89), [characters-page.test.ts#L134](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/characters-page.test.ts#L134)

### [SUGGESTION] Chart Lifecycle Logic Is Duplicated In Multiple Places
`MiniChart`, `VerbDomainChart`, and block explorer each own similar import/create/destroy logic, which increases drift risk for fixes (race handling, theme updates, cleanup behavior).  
Evidence: [MiniChart.svelte#L15](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte#L15), [VerbDomainChart.svelte#L14](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/VerbDomainChart.svelte#L14), [blocks/+page.svelte#L70](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L70)

### [SUGGESTION] `loadAllData` Looks Like Dead Production API Surface
`loadAllData` is exported but appears unused by app routes and only exercised in unit tests; consider removing or reintroducing via an actual route usage to reduce maintenance surface.  
Evidence: [data.ts#L105](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts#L105), [data.test.ts#L74](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/data.test.ts#L74)

### [PRAISE] Server Loaders Are Scoped Well By Page
The Stage 6 route loaders generally fetch only what each page needs and correctly reuse manifest from parent layout, which keeps payloads and coupling down.  
Evidence: [chapters/+page.server.ts#L4](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/chapters/+page.server.ts#L4), [characters/+page.server.ts#L4](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/characters/+page.server.ts#L4), [blocks/+page.server.ts#L4](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.server.ts#L4), [+layout.server.ts#L4](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/+layout.server.ts#L4)

### [PRAISE] Shared SSR-Safe Chart Color Utility Is A Good Direction
`resolveChartColors()` cleanly avoids SSR document access while centralizing chart token mapping, and overview/characters/blocks adoption improves consistency.  
Evidence: [chart-colors.ts#L35](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/utils/chart-colors.ts#L35), [overview/+page.svelte#L5](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/overview/+page.svelte#L5), [characters/+page.svelte#L4](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/characters/+page.svelte#L4), [blocks/+page.svelte#L5](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/%5Bslug%5D/blocks/+page.svelte#L5)