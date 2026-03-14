# Stage 7: Polish

## Context

Stages 1–6 complete (223 engine tests, 59 explorer tests). All 7 analyzers working. Explorer has 5 interactive pages: landing, overview, chapters, characters, block explorer. Dark mode, theme-reactive charts, keyboard navigation, and accessibility all in place.

**Key gap discovered:** The silence analyzer runs and produces data, but `json_export.py` has no `write_silence()` — the results are computed and discarded. This blocks the Phase 3 spec item "Silence mapping visualization."

**Deferred from Stage 6 reviews:** cancellation guards on MiniChart/VerbDomainChart, deeper interaction tests, `loadAllData` dead code removal, chart lifecycle concerns.

**Scope decision:** Focus on items feasible within existing architecture. Defer version comparison (needs infrastructure + second analysis), character refinement UI (too large), BookNLP (external dependency), verb agency trajectory (needs engine changes), input format support (Phase 4).

After implementation: Gemini+Codex review → Claude sanity-check → triage → apply fixes.

## Changes

### Phase A: Silence data persistence + explorer plumbing

Close the gap where silence data is computed but never written to disk. Wire explorer types and loader.

**Engine changes:**

**Modify:** `engine/src/lit_engine/output/json_export.py`
- Add `write_silence(output_dir, data)` → calls `write_json(output_dir, "silence.json", data)`
- Follows exact pattern of `write_sentiment`

**Modify:** `engine/src/lit_engine/cli.py`
- Import `write_silence`
- Add write block after sentiment (line ~181): `if "silence" in results: write_silence(output, results["silence"].data)`

**Explorer changes:**

**Modify:** `explorer/src/lib/types/analysis.ts`
- Add interfaces: `SilenceGap` (`start_char`, `end_char`, `word_count`), `LongestSilence` (`word_count`, `position`, `preview`), `Silence` (`gaps[]`, `longest_silence`, `avg_gap_words`, `total_gaps`)
- Schema maps directly to `analyzers/silence.py` output (lines 101-108)

**Modify:** `explorer/src/lib/server/data.ts`
- Add `loadSilence(slug)` → `readJson<Silence>(slug, 'silence.json')`

**New:** `explorer/tests/fixtures/test-analysis/silence.json`
- 4 gaps, longest at 210 words, avg 102.5

**Tests:**
- Engine: `test_json_export.py` — silence roundtrip write/read
- Explorer: `data.test.ts` — `loadSilence` returns correct fixture data

### Phase B: Silence visualization page

New `/[slug]/silence` page showing dialogue gap patterns.

**New:** `explorer/src/routes/[slug]/silence/+page.server.ts`
```typescript
const { manifest } = await parent();
const [silence, chapters] = await Promise.all([
    loadSilence(params.slug), loadChapters(params.slug)
]);
return { manifest, silence, chapters };
```

**New:** `explorer/src/routes/[slug]/silence/+page.svelte`

Layout:
```
[MetricCard: Total Gaps] [MetricCard: Avg Gap Words] [MetricCard: Longest Silence]
[=== Bar chart: gap word counts (longest highlighted in rose) ===]
[Longest silence callout: preview text + position]
```

Key details:
- Bar chart via `$effect` + dynamic `import('chart.js/auto')` + cancellation guard (same pattern as blocks page)
- Theme reactivity via `resolveChartColors()` + `onThemeChange()`
- Longest silence bar highlighted in `chartColors.rose`, others in `chartColors.blue`
- Cross-reference gap positions against chapter boundaries from chapters data
- Accessible: `figure` with `aria-label`, `figcaption.sr-only`
- Responsive: chart height 300px → 200px at 768px

**Modify:** `explorer/src/routes/[slug]/+layout.svelte`
- Add `<a href="/{slug}/silence">Silence</a>` to sub-nav (after Blocks)

**Tests:** `explorer/tests/unit/silence-page.test.ts` (~6 tests)
- Renders total gaps count, avg gap words, longest silence preview + word count
- Canvas element present for chart
- Handles 0 gaps gracefully

### Phase C: PNG chart export

Export any Chart.js canvas as a downloadable PNG. Phase 3 spec item #3.

**New:** `explorer/src/lib/utils/chart-export.ts`
```typescript
export function exportChartAsPng(
    chart: { toBase64Image: (type?: string, quality?: number) => string } | undefined,
    filename: string = 'chart.png'
): void {
    if (!chart || typeof document === 'undefined') return;
    const link = document.createElement('a');
    link.href = chart.toBase64Image('image/png', 1.0);
    link.download = filename;
    link.click();
}
```
- Duck-typed chart parameter — no Chart.js import needed
- SSR guard
- No new dependencies

**Modify:** `explorer/src/routes/[slug]/blocks/+page.svelte`
- Import `exportChartAsPng`
- Add export button in `.metric-tabs`: `Export PNG` → `exportChartAsPng(chart, \`${selectedMetric}-blocks.png\`)`
- Button styled as outlined pill (matches `.tab-pill` but distinct)

**Modify:** `explorer/src/routes/[slug]/silence/+page.svelte`
- Same export button pattern for the silence chart

**Tests:** `explorer/tests/unit/chart-export.test.ts` (~3 tests)
- No-op when chart is undefined
- Calls `toBase64Image` and triggers download link click
- Uses default filename when none provided

### Phase D: Polish fixes

Three independent fixes.

**Fix 1: Cancellation guards**

**Modify:** `explorer/src/lib/components/MiniChart.svelte`
- Add `let cancelled = false` + check in `.then()` callback (same pattern as blocks page lines 87-90)

**Modify:** `explorer/src/lib/components/VerbDomainChart.svelte`
- Same cancellation guard pattern

**Fix 2: Sub-nav active state**

**Modify:** `explorer/src/routes/[slug]/+layout.svelte`
- Add `$derived`: `let currentPage = $derived(page.url.pathname.split('/').pop() ?? '')`
- Apply `class:active={currentPage === 'overview'}` + `aria-current={currentPage === 'overview' ? 'page' : undefined}` to each link
- CSS: `.sub-nav a.active { color: var(--accent); border-bottom: 2px solid var(--accent); }`

**Fix 3: Remove dead `loadAllData`**

**Modify:** `explorer/src/lib/server/data.ts`
- Remove `loadAllData()` function (lines 104-114)

**Modify:** `explorer/src/lib/types/analysis.ts`
- Remove `AnalysisData` interface (lines 179-186) — only referenced by `loadAllData`

**Modify:** `explorer/tests/unit/data.test.ts`
- Remove `describe('loadAllData', ...)` block — exercises dead code

**Tests:** ~2 new (sub-nav active state verification)

### Phase E: Interaction tests

Fill test gaps identified in Stage 6 reviews.

**Modify:** `explorer/tests/unit/block-explorer.test.ts` (~5 new tests)
- Keyboard nav: ArrowRight moves to block 2, ArrowLeft returns to block 1
- ArrowLeft at first block is no-op
- Metric switching: click Fog tab → Fog gets `.active` class, MATTR loses it
- Query param sync: mock `$app/state` with `from=2` → block 2 selected initially

**Modify:** `explorer/tests/unit/chapters-page.test.ts` (~3 new tests)
- aria-sort transitions: click Words header → `aria-sort="ascending"` → click again → `"descending"`
- Column switch: click Words then Fog → Words header reverts to `aria-sort="none"`
- Default sort: chapter number column has `aria-sort="ascending"` initially

### Phase F: Re-run engine

Run `lit-engine analyze` on the manuscript to generate `silence.json` in `shared/analyses/the-specimen/`. Manual verification step.

1. `cd engine && python -m lit_engine.cli analyze ~/Documents/lit-analysis/the_specimen_v2.txt --output ../shared/analyses/the-specimen --title "The Specimen"`
2. Verify `silence.json` created with expected schema
3. Smoke test: `cd explorer && npm run dev` → navigate to `/the-specimen/silence`

## Files Summary

| # | Action | File |
|---|--------|------|
| 1 | MODIFY | `engine/src/lit_engine/output/json_export.py` |
| 2 | MODIFY | `engine/src/lit_engine/cli.py` |
| 3 | MODIFY | `engine/tests/test_json_export.py` |
| 4 | MODIFY | `explorer/src/lib/types/analysis.ts` |
| 5 | MODIFY | `explorer/src/lib/server/data.ts` |
| 6 | NEW | `explorer/tests/fixtures/test-analysis/silence.json` |
| 7 | MODIFY | `explorer/tests/unit/data.test.ts` |
| 8 | NEW | `explorer/src/routes/[slug]/silence/+page.server.ts` |
| 9 | NEW | `explorer/src/routes/[slug]/silence/+page.svelte` |
| 10 | NEW | `explorer/tests/unit/silence-page.test.ts` |
| 11 | NEW | `explorer/src/lib/utils/chart-export.ts` |
| 12 | NEW | `explorer/tests/unit/chart-export.test.ts` |
| 13 | MODIFY | `explorer/src/routes/[slug]/blocks/+page.svelte` |
| 14 | MODIFY | `explorer/src/lib/components/MiniChart.svelte` |
| 15 | MODIFY | `explorer/src/lib/components/VerbDomainChart.svelte` |
| 16 | MODIFY | `explorer/src/routes/[slug]/+layout.svelte` |
| 17 | MODIFY | `explorer/tests/unit/block-explorer.test.ts` |
| 18 | MODIFY | `explorer/tests/unit/chapters-page.test.ts` |

**6 new files, 12 modified files. 1 engine change (write_silence). No new dependencies.**

## Test Plan

| Phase | New Tests | Description |
|-------|-----------|-------------|
| A | ~3 | Silence write roundtrip, loadSilence loader |
| B | ~6 | Silence page rendering + empty state |
| C | ~3 | PNG export utility |
| D | ~2 | Sub-nav active state |
| E | ~8 | Keyboard nav, metric switching, aria-sort, query params |
| **Total** | **~22** | Brings explorer from 59 to ~81 tests |

Remove ~1 dead test (`loadAllData`). Net: +21.

## Verification

1. `cd engine && python -m pytest` — 223 + 1 new = 224 tests pass
2. `cd explorer && npm test` — 59 + 22 - 1 = ~80 tests pass
3. `npx svelte-check` — no type errors
4. Dev server: navigate all 5 pages (overview, chapters, characters, blocks, silence)
5. Toggle dark mode on silence page — chart colors update
6. Click Export PNG on blocks page — downloads PNG file
7. Arrow keys navigate blocks on chart
8. Sub-nav highlights current page
9. Sort chapters table — aria-sort attributes transition correctly
