# Stage 6 Plan Review (Gemini): Explorer Interactive Pages

## Scope

Three new interactive pages replacing placeholder stubs in the SvelteKit explorer: Block Explorer (click-to-read chart), Chapters (sortable table), Characters (agency profile cards). Plus shared chart color utility and 4 new components.

## Plan Document

Read the plan at: `.claude/plans/streamed-marinating-bentley.md`

## Key Files for Context

### Existing patterns to follow
- `explorer/src/routes/[slug]/overview/+page.svelte` — Current chart integration pattern (MiniChart, CSS variable colors, $derived data transforms)
- `explorer/src/routes/[slug]/overview/+page.server.ts` — Server load pattern with parent()
- `explorer/src/lib/components/MiniChart.svelte` — SSR-safe Chart.js pattern (dynamic import in $effect)
- `explorer/src/lib/components/MetricCard.svelte` — Simple presentational component pattern
- `explorer/src/lib/types/analysis.ts` — All TypeScript interfaces for the JSON data contract
- `explorer/src/app.css` — Design system (CSS variables, chart colors, card utility, dark mode)

### Existing data (what the pages will consume)
- `shared/analyses/the-specimen/analysis.json` — 177 blocks with metrics, notables, pacing
- `shared/analyses/the-specimen/chapters.json` — 16 chapters with per-chapter stats
- `shared/analyses/the-specimen/characters.json` — 8 character profiles with verb domains

### Test patterns
- `explorer/tests/unit/components.test.ts` — Component testing with @testing-library/svelte
- `explorer/tests/unit/data.test.ts` — Data layer testing with vitest mocks
- `explorer/tests/fixtures/test-analysis/` — Test fixture JSON files

### Layout and navigation
- `explorer/src/routes/[slug]/+layout.svelte` — Sub-nav with links to all four pages
- `explorer/src/lib/server/data.ts` — All data loading functions (loadAnalysis, loadChapters, etc.)

## Review Criteria

1. **Architectural soundness**: Is the component breakdown appropriate? Are we over- or under-abstracting?
2. **Chart.js interactivity**: Is the Block Explorer's click-to-select approach viable? Are there edge cases with the custom chapter boundary plugin?
3. **Data flow**: Do the server loads fetch the right data? Any unnecessary loading?
4. **Responsive design**: Will the table and chart layouts work on mobile?
5. **Test coverage**: Are the planned ~24 tests sufficient for the 4 new components and 3 pages?
6. **Accessibility**: Are charts, tables, and interactive elements accessible?

## Severity Levels

Use these exact severity levels:
- `### [BLOCKER]` — Must fix before implementation
- `### [CONCERN]` — Should address, acceptable to defer
- `### [SUGGESTION]` — Nice to have
- `### [PRAISE]` — Good practice worth noting
