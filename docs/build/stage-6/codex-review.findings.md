### [BLOCKER] Stage 6 Plan Document Missing
The required plan file [`.claude/plans/streamed-marinating-bentley.md`](/home/bluekitty/Documents/Git/lit-explorer/.claude/plans/streamed-marinating-bentley.md) is not present in this workspace (`.claude/` only contains [`settings.json`](/home/bluekitty/Documents/Git/lit-explorer/.claude/settings.json)). Architectural breakdown, loader scope, component boundaries, and test intent cannot be fully validated without that source artifact.

### [CONCERN] Character Profile Percentage Math Can Be Invalid
`characters.json` values can violate naive denominator assumptions (for example, `via_pronoun` can exceed `total_verbs`), so any planned “pronoun %” based on `total_verbs` will exceed 100%. The plan should explicitly define denominators and test both reference-based and verb-based ratios using [`shared/analyses/the-specimen/characters.json`](/home/bluekitty/Documents/Git/lit-explorer/shared/analyses/the-specimen/characters.json).

### [CONCERN] Chapter Boundary Plugin Needs Null/Source Rules
The type contract allows `Block.chapter` to be nullable in [`analysis.ts`](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/types/analysis.ts#L44), so chapter boundary rendering should be sourced from `chapters[].block_range` (with fallback behavior) rather than assuming every block has a chapter id from `analysis.blocks`.

### [CONCERN] Canvas Click UX Is Not Sufficiently Accessible by Default
Current chart wrapper is an image-like figure in [`MiniChart.svelte`](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte#L42). A click-only block selector would exclude keyboard/screen-reader users unless the plan includes keyboard-operable selection and explicit live selection text outside the canvas.

### [CONCERN] Page Data Loading Should Be Narrow, Not Overview-Style
Overview intentionally loads everything via `Promise.all` in [`overview/+page.server.ts`](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.server.ts#L7). Stage 6 routes should not copy that pattern; each page should load only required JSON plus `manifest` from parent to avoid unnecessary I/O.

### [CONCERN] ~24 Tests Is Likely Light for Interaction Complexity
Current tests are mostly smoke/data-loader oriented ([`components.test.ts`](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/components.test.ts), [`data.test.ts`](/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/unit/data.test.ts)). Stage 6 needs dedicated state tests for chart selection, chapter sort toggling/`aria-sort`, and boundary-drawing logic, not just render assertions.

### [SUGGESTION] Lock Mobile Table Strategy Up Front
Given long chapter titles and many sortable numeric columns in [`chapters.json`](/home/bluekitty/Documents/Git/lit-explorer/shared/analyses/the-specimen/chapters.json), explicitly plan horizontal scroll with a sticky first column and fixed numeric alignment to preserve cross-column comparability on mobile.

### [SUGGESTION] Keep Chart Color Utility SSR-Safe With Fallbacks
A shared color resolver is a good abstraction, but it should define client-only CSS variable reads with deterministic fallback values before `document` exists, aligned with existing theme variables in [`app.css`](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/app.css#L15).

### [PRAISE] SSR-Safe Chart Lifecycle Pattern Is Already Solid
The dynamic import + destroy lifecycle in [`MiniChart.svelte`](/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/components/MiniChart.svelte#L15) is a strong base for Stage 6 interactive chart work.

### [PRAISE] Existing Data Contracts Support the Planned Pages Well
The current schema and specimen data already expose the right primitives (block metrics/notables, chapter ranges, verb domains), so Stage 6 can focus on UI composition and interaction behavior rather than backend/schema churn.