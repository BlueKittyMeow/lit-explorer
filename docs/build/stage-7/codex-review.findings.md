### [BLOCKER] Chapter Boundary Mapping Cannot Be Derived From Planned Inputs
Phase B says the silence page will “cross-reference gap positions against chapter boundaries,” but the planned loader returns only `silence` + `chapters`. `silence` is char-based (`start_char`/`end_char`), while `chapters` only has block ranges, so chapter boundary overlays are not derivable without `analysis.blocks` (or chapter char spans in engine output).  
Refs: [plan.md:51](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:51), [plan.md:73](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:73), [silence.py:104](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/analyzers/silence.py:104), [chapters.json:16](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/fixtures/test-analysis/chapters.json:16)

### [CONCERN] Silence Type Must Explicitly Model `longest_silence` as Nullable
The analyzer returns `longest_silence: None` for no-dialogue/zero-gap cases, so TS should be `LongestSilence | null`; otherwise the page/callout logic is brittle in exactly the “0 gaps gracefully” case in the plan.  
Refs: [silence.py:34](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/analyzers/silence.py:34), [silence.py:99](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/analyzers/silence.py:99), [plan.md:83](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:83)

### [CONCERN] `pathname.split('/').pop()` Is Not Robust for Active Nav
This fails for trailing-slash paths (`.../overview/` => `''`) and is fragile if route depth changes. Normalize trailing slashes or derive from stable route segment logic.  
Refs: [plan.md:134](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:134), [layout.svelte:10](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/+layout.svelte:10)

### [CONCERN] Test Plan Misses Two High-Value Regression Guards
Planned tests are strong, but there’s no explicit integration assertion that `analyze` writes `silence.json` via CLI output flow, and no race/unmount tests validating the new cancellation guards in `MiniChart`/`VerbDomainChart`.  
Refs: [cli.py:157](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/cli.py:157), [MiniChart.svelte:19](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte:19), [VerbDomainChart.svelte:17](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/VerbDomainChart.svelte:17), [plan.md:201](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:201)

### [SUGGESTION] Use Chart.js Type Imports Instead of Duck-Typed Chart Param
`import type { Chart } from 'chart.js'` gives compile-time safety with no runtime cost, so you can keep the utility lightweight without losing type guarantees.  
Refs: [plan.md:91](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:91)

### [PRAISE] `write_silence` Placement in Engine Pipeline Is Architecturally Sound
Adding it alongside other per-analyzer JSON writes after enrichment and before manifest creation matches existing flow and has no ordering conflicts.  
Refs: [cli.py:161](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/cli.py:161), [cli.py:180](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/cli.py:180), [json_export.py:41](/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/output/json_export.py:41)

### [PRAISE] Dead Code Cleanup Appears Safe
`loadAllData` and `AnalysisData` are localized and removable with low blast radius; routes already load only page-specific datasets.  
Refs: [data.ts:105](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts:105), [analysis.ts:180](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/types/analysis.ts:180), [overview/+page.server.ts:6](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.server.ts:6)

### [PRAISE] Planned Interaction Tests Directly Target Current Gaps
The proposed keyboard/query-param/aria-sort additions align with clear holes in current `block-explorer` and `chapters` test coverage.  
Refs: [block-explorer.test.ts:137](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/block-explorer.test.ts:137), [chapters-page.test.ts:89](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/chapters-page.test.ts:89), [plan.md:155](/home/bluekitty/Documents/Git/lit-explorer/docs/build/stage-7/plan.md:155)