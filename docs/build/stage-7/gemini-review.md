# Stage 7 Plan Review (Gemini): Polish

## Scope

Silence data persistence (engine writes silence.json), new silence visualization page, PNG chart export utility, cancellation guards on chart components, sub-nav active state, dead code cleanup, and ~22 new interaction tests.

## Plan Document

Read the plan at: `docs/build/stage-7/plan.md`

## Key Files for Context

### Engine (silence persistence)
- `engine/src/lit_engine/analyzers/silence.py` — Silence analyzer that produces gap data (currently discarded)
- `engine/src/lit_engine/output/json_export.py` — JSON export functions (write_analysis, write_characters, etc. — NO write_silence yet)
- `engine/src/lit_engine/cli.py` — CLI output section (lines 157-185) where each JSON is written

### Explorer patterns to follow
- `explorer/src/routes/[slug]/blocks/+page.svelte` — Most complex chart page (cancellation guard pattern, chart onClick, keyboard nav, theme reactivity)
- `explorer/src/routes/[slug]/overview/+page.svelte` — Chart color usage pattern with onThemeChange
- `explorer/src/lib/components/MiniChart.svelte` — SSR-safe Chart.js dynamic import (MISSING cancellation guard)
- `explorer/src/lib/components/VerbDomainChart.svelte` — Horizontal bar chart (MISSING cancellation guard)
- `explorer/src/lib/utils/chart-colors.ts` — Shared chart color utility with MutationObserver theme tracking
- `explorer/src/routes/[slug]/+layout.svelte` — Sub-nav layout (currently NO active state indicator)

### Data layer
- `explorer/src/lib/server/data.ts` — Data loading functions (has loadAllData dead code on line 105)
- `explorer/src/lib/types/analysis.ts` — TypeScript interfaces (has AnalysisData dead type on line 180)

### Tests
- `explorer/tests/unit/block-explorer.test.ts` — Block explorer tests (needs keyboard nav, metric switch tests)
- `explorer/tests/unit/chapters-page.test.ts` — Chapter tests (needs aria-sort transition tests)
- `explorer/tests/unit/data.test.ts` — Data loader tests (has dead loadAllData test)
- `explorer/tests/fixtures/test-analysis/` — Test fixture JSON files

## Review Criteria

1. **Engine change safety**: Is `write_silence` correctly placed in the output pipeline? Any ordering concerns?
2. **Silence page design**: Is the bar chart the right visualization for dialogue gaps? Any missing dimensions?
3. **PNG export approach**: Is duck-typed `toBase64Image` appropriate, or should we use Chart.js types?
4. **Dead code removal**: Is it safe to remove `loadAllData` and `AnalysisData`? Any hidden consumers?
5. **Test coverage**: Do ~22 new tests adequately cover the new features and fill Stage 6 gaps?
6. **Sub-nav active state**: Is `pathname.split('/').pop()` robust enough for URL matching?

## Severity Levels

Use these exact severity levels:
- `### [BLOCKER]` — Must fix before implementation
- `### [CONCERN]` — Should address, acceptable to defer
- `### [SUGGESTION]` — Nice to have
- `### [PRAISE]` — Good practice worth noting
