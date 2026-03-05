# Stage 5: SvelteKit Explorer — Scaffolding + Data Loading

## Goal

Scaffold the SvelteKit frontend, build the data loading layer, and deliver two
working pages: the landing page (analysis listing) and the overview dashboard
(metric cards + mini charts). Match Scriptorium's conventions for future component
portability.

See [scriptorium-reference.md](scriptorium-reference.md) for the full architectural
context on Scriptorium's patterns, types, and conventions.

## Context

The Python engine (Stages 1–4) is complete with 219 tests passing. It produces
five JSON files per analysis in `shared/analyses/{slug}/`:

- `manifest.json` — metadata (title, word count, analyzers run, parameters, warnings)
- `analysis.json` — TextTiling blocks with per-block metrics
- `characters.json` — agency profiles per character
- `chapters.json` — per-chapter aggregated metrics (chapters list only; `block_to_chapter` is internal to the engine and not written to disk)
- `sentiment.json` — sentence-level emotional arc, smoothed arc, + extremes

The explorer reads these files. No database, no runtime dependency on the engine.

## Conventions (from Scriptorium)

- Svelte 5 with runes (`$props()`, `$state()`, `$derived()`, `$effect()`)
- TypeScript strict
- `@sveltejs/adapter-node`
- Data loading via `+page.server.ts` (never client-side fetch for initial data)
- Custom CSS (no framework) — warm paper aesthetic, research notebook feel
- npm
- Vitest
- Types in `$lib/types/`
- Server utilities in `$lib/server/`
- Components in `$lib/components/`

## Changes

### 1. Project scaffolding — `explorer/`

```
explorer/
├── package.json
├── svelte.config.js
├── vite.config.ts
├── tsconfig.json
├── src/
│   ├── app.html
│   ├── app.css                  ← global styles, CSS custom properties
│   ├── lib/
│   │   ├── types/
│   │   │   └── analysis.ts      ← TypeScript interfaces matching JSON schema
│   │   ├── server/
│   │   │   └── data.ts          ← JSON file loaders
│   │   └── components/
│   │       ├── MetricCard.svelte
│   │       ├── MiniChart.svelte
│   │       └── AnalysisCard.svelte
│   └── routes/
│       ├── +layout.svelte       ← top bar, nav, theme
│       ├── +layout.server.ts    ← (optional: load analysis list for nav)
│       ├── +page.svelte         ← landing page
│       ├── +page.server.ts      ← load analysis listing
│       └── [slug]/
│           ├── +layout.svelte   ← analysis-scoped nav (overview/chapters/characters/blocks)
│           ├── +layout.server.ts ← load manifest for this analysis
│           ├── overview/
│           │   ├── +page.svelte  ← dashboard
│           │   └── +page.server.ts ← load all JSON for this analysis
│           ├── chapters/         ← Stage 6 (placeholder)
│           ├── characters/       ← Stage 6 (placeholder)
│           └── blocks/           ← Stage 6 (placeholder)
└── tests/
    ├── unit/
    │   └── data.test.ts         ← data loader tests
    └── fixtures/
        └── test-analysis/       ← minimal valid JSON set for testing
            ├── manifest.json
            ├── analysis.json
            ├── characters.json
            ├── chapters.json
            └── sentiment.json
```

Initialize with: `npm create svelte@latest` → Skeleton project, TypeScript, Vitest.

### 2. TypeScript interfaces — `$lib/types/analysis.ts`

Map the JSON contract from spec.md into TypeScript interfaces:

```typescript
// Manifest
export interface Manifest {
  title: string;
  slug: string;
  source_file: string;
  analyzed_at: string;
  engine_version: string;
  word_count: number;
  char_count: number;
  chapter_count: number;
  character_list: string[];
  analyzers_run: string[];
  parameters: Record<string, unknown>;
  warnings: string[];
}

// analysis.json
export interface BlockMetrics {
  mattr: number;
  avg_sentence_length: number;
  max_sentence_length: number;
  flesch_ease: number;
  flesch_grade: number;
  gunning_fog: number;
  // Enriched by readability analyzer via CLI pipeline
  coleman_liau: number;
  smog: number;
  ari: number;
}

export interface Block {
  id: number;
  tile_index: number;
  start_char: number;
  end_char: number;
  word_count: number;
  sentence_count: number;
  metrics: BlockMetrics;
  sentence_lengths: number[];
  preview: string;
  chapter: number | null;
}

export interface Notable {
  longest_sentences: number[];
  highest_mattr: number[];
  highest_fog: number[];
  shortest_sentences: number[];
}

// Pacing data (merged into analysis.json by CLI when pacing analyzer runs)
export interface PacingPassage {
  block_id: number;
  avg_sentence_length: number;
  sentence_count: number;
  preview: string;
}

export interface PacingData {
  sentence_count: number;
  distribution: {
    mean: number;
    median: number;
    std_dev: number;
    min: number;
    max: number;
    percentiles: Record<string, number>;
  };
  staccato_passages: PacingPassage[];
  flowing_passages: PacingPassage[];
}

export interface Analysis {
  parameters: Record<string, number>;
  total_blocks: number;
  blocks: Block[];
  notable: Notable;
  pacing?: PacingData;  // present when pacing analyzer ran
}

// characters.json
export interface VerbEntry {
  verb: string;
  count: number;
  category?: string;
}

export interface ActionEntry {
  action: string;
  count: number;
}

export interface PassiveAgent {
  agent: string;
  count: number;
}

export interface CharacterProfile {
  total_verbs: number;
  active_count: number;
  passive_count: number;
  intransitive_count: number;
  via_name: number;
  via_pronoun: number;
  verb_domains: Record<string, number>;
  top_verbs: VerbEntry[];
  top_actions: ActionEntry[];
  passive_verbs: VerbEntry[];
  passive_agents: PassiveAgent[];
}

export interface Characters {
  characters: Record<string, CharacterProfile>;
}

// chapters.json
export interface ChapterSentiment {
  compound: number;
  pos: number;
  neg: number;
  neu: number;
}

export interface Chapter {
  number: number;
  title: string;
  word_count: number;
  sentence_count: number;
  dialogue_ratio: number;
  avg_sentence_length: number;
  mattr: number;
  flesch_ease: number;
  fog: number;
  character_mentions: Record<string, number>;
  dominant_character: string;
  sentiment: ChapterSentiment;
  block_range: [number, number];
}

export interface Chapters {
  chapters: Chapter[];
  // Note: block_to_chapter is internal to the engine (used for enriching
  // analysis.json blocks). It is NOT written to chapters.json.
}

// sentiment.json
export interface SentimentPoint {
  position: number;
  compound: number;
  pos: number;
  neg: number;
  neu: number;
}

export interface SmoothedPoint {
  position: number;
  compound: number;
}

export interface SentimentExtreme {
  position: number;
  text_preview: string;
  score: number;
}

export interface Sentiment {
  method: string;
  granularity: string;
  arc: SentimentPoint[];
  smoothed_arc: SmoothedPoint[];
  chapter_averages: { chapter: number; compound: number }[];
  extremes: {
    most_positive: SentimentExtreme | null;
    most_negative: SentimentExtreme | null;
  };
}

// Combined: everything loaded for a single analysis
export interface AnalysisData {
  manifest: Manifest;
  analysis: Analysis;
  characters: Characters;
  chapters: Chapters;
  sentiment: Sentiment;
}

// Landing page: summary for listing
export interface AnalysisSummary {
  slug: string;
  title: string;
  word_count: number;
  chapter_count: number;
  character_list: string[];
  analyzed_at: string;
  analyzers_run: string[];
}
```

### 3. Data loading layer — `$lib/server/data.ts`

Server-only module that reads JSON from `shared/analyses/`:

```typescript
import { readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { env } from '$env/dynamic/private';
import type {
  Manifest, Analysis, Characters, Chapters, Sentiment,
  AnalysisSummary, AnalysisData
} from '$lib/types/analysis';

function getAnalysesDir(): string {
  return env.ANALYSES_DIR || resolve(process.cwd(), '..', 'shared', 'analyses');
}

export async function listAnalyses(): Promise<AnalysisSummary[]> { ... }
export async function loadManifest(slug: string): Promise<Manifest> { ... }
export async function loadAnalysis(slug: string): Promise<Analysis> { ... }
export async function loadCharacters(slug: string): Promise<Characters> { ... }
export async function loadChapters(slug: string): Promise<Chapters> { ... }
export async function loadSentiment(slug: string): Promise<Sentiment> { ... }

/** Load all data for a single analysis (overview page). */
export async function loadAllData(slug: string): Promise<AnalysisData> {
  const [manifest, analysis, characters, chapters, sentiment] = await Promise.all([
    loadManifest(slug),
    loadAnalysis(slug),
    loadCharacters(slug),
    loadChapters(slug),
    loadSentiment(slug),
  ]);
  return { manifest, analysis, characters, chapters, sentiment };
}
```

- `listAnalyses()` scans the directory for subdirs containing `manifest.json`
- Each loader reads the file, parses JSON, returns typed object
- `loadAllData()` hydrates all five files in parallel for the overview page
- **Path traversal guard** (explicit recipe):
  1. Validate slug against allowlist regex: `/^[a-z0-9][a-z0-9_-]*$/`
  2. `const base = resolve(getAnalysesDir());`
  3. `const candidate = resolve(base, slug);`
  4. Allow only if `candidate === base || candidate.startsWith(base + sep)` (separator boundary prevents `/base/analyses2` matching `/base/analyses`)
  5. Reject anything else with `error(400)`
- Missing file → throw `error(404)` from `@sveltejs/kit`
- **`$env/dynamic/private`** for runtime configurability with `adapter-node` (not `static`, which bakes at build time)
- `ANALYSES_DIR` env var for overriding in tests and deployment; `getAnalysesDir()` called per-request (not cached at module level) so env changes take effect
- **Slug/Unicode note**: The engine's `slugify()` strips non-ASCII after lowercasing (e.g., "Café Union" → "caf-union"). The explorer's slug allowlist regex (`/^[a-z0-9][a-z0-9_-]*$/`) is compatible. Add a data loader test that verifies a slug containing accented source title round-trips correctly through the fixture data.

### 4. Landing page — `/`

`+page.server.ts`: calls `listAnalyses()`, returns sorted by `analyzed_at` (newest first).

`+page.svelte`: Grid of analysis cards. Each card shows:
- Title (from manifest)
- Word count + chapter count
- Characters detected (as tags/chips)
- Date analyzed (relative: "2 hours ago")
- Analyzers run count ("8 analyzers")
- Click → `/[slug]/overview`

If no analyses found, show empty state with instructions to run `lit-engine analyze`.

### 5. Root layout — `+layout.svelte`

- Top bar: "Lit Explorer" branding, link to home
- Theme toggle (dark/light/system) — CSS custom properties, same pattern as Scriptorium
- Flash prevention inline script in `app.html`
- Nav links (contextual: when inside `[slug]`, show overview/chapters/characters/blocks)

### 6. Analysis layout — `[slug]/+layout.svelte`

`+layout.server.ts`: loads manifest for this slug, passes to layout.

`+layout.svelte`: Sub-navigation tabs for the analysis pages:
- Overview | Chapters | Characters | Blocks
- Shows manuscript title in header
- Stage 6 placeholder pages for chapters/characters/blocks (just "Coming soon" with the nav working)

### 7. Overview dashboard — `[slug]/overview/`

`+page.server.ts`: loads all five JSON files via the data layer.

`+page.svelte`: Dashboard with:

**Metric cards row** (MetricCard component):
- Total words (from manifest)
- Chapters (count)
- Characters (count + names)
- Blocks (from analysis.total_blocks)
- Dialogue ratio (average across chapters)
- Avg readability (Flesch ease, averaged)

**Mini charts** (MiniChart component — thin Chart.js wrapper):
- Sentiment arc sparkline (compound over position)
- MATTR over blocks sparkline
- Chapter word counts bar chart
- Character verb domain comparison (small grouped bar)

**Notable callouts**:
- Longest sentence (block ID + preview from notable)
- Richest passage (highest MATTR block)
- Most complex chapter (highest fog)
- Most positive / most negative moments (from sentiment extremes)

Each mini chart and notable is clickable → will navigate to the relevant detail
page in Stage 6 (for now, link to the placeholder).

### 8. Shared components

**MetricCard.svelte**:
```svelte
<script lang="ts">
  let { label, value, subtitle = '' }: {
    label: string;
    value: string | number;
    subtitle?: string;
  } = $props();
</script>
```

**MiniChart.svelte** — Chart.js canvas wrapper with accessibility:
```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { ChartData, ChartOptions } from 'chart.js';

  let { data, type = 'line', options = {}, label = 'Chart' }: {
    data: ChartData;
    type?: string;
    options?: ChartOptions;
    label?: string;
  } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart;

  onMount(() => {
    chart = new Chart(canvas, { type, data, options });
    return () => chart.destroy();
  });
</script>

<figure role="img" aria-label={label}>
  <canvas bind:this={canvas}></canvas>
  <!-- Visually hidden data summary for screen readers -->
  <figcaption class="sr-only">
    {label}: {data.datasets?.[0]?.data?.length ?? 0} data points
  </figcaption>
</figure>
```

Note: Chart.js operates on `<canvas>` which is opaque to screen readers. The
`<figure>` wrapper with `aria-label` and a visually hidden `<figcaption>` provides
a baseline accessible description. Stage 6 detail pages can add richer data tables.

**AnalysisCard.svelte** — landing page card for each analysis.

### 9. Global styles — `app.css`

CSS custom properties for theming (matching Scriptorium's pattern):

```css
:root {
  --bg-primary: #faf8f5;       /* warm paper */
  --bg-secondary: #f0ece6;
  --bg-card: #ffffff;
  --text-primary: #2c2417;
  --text-secondary: #6b5d4d;
  --text-muted: #9a8b78;
  --accent: #8b6914;            /* warm gold */
  --accent-hover: #a37d1a;
  --border: #e0d8cc;
  --shadow: rgba(44, 36, 23, 0.08);
  /* ... */
}

:root.dark {
  --bg-primary: #1a1814;
  --bg-secondary: #242019;
  --bg-card: #2a2520;
  --text-primary: #e8e0d4;
  --text-secondary: #b0a494;
  --text-muted: #7a6e60;
  --accent: #d4a832;
  --border: #3a342c;
  --shadow: rgba(0, 0, 0, 0.3);
}
```

Research notebook aesthetic: serif headings (`Georgia, 'Times New Roman', serif`),
monospace metrics (`'JetBrains Mono', 'Fira Code', monospace`), generous whitespace,
subtle card shadows.

### 10. Testing

**Unit tests — data loaders** (`tests/unit/data.test.ts`):
- `listAnalyses()` returns expected summaries from fixture dir
- `loadManifest()` returns typed manifest with `warnings` field
- `loadAllData()` returns complete `AnalysisData` object
- Each loader handles missing file (404 error)
- Path traversal rejection (`../etc/passwd`, `foo/bar`, encoded `%2e%2e` → error)
- Slug allowlist validation (rejects non-matching patterns)
- Empty analyses dir → empty array
- Slug from accented title (e.g., "caf-union" from "Café Union") loads correctly

**Integration tests — route loaders** (`tests/integration/routes.test.ts`):
- Landing page `+page.server.ts` `load()` returns analysis list
- `[slug]/+layout.server.ts` `load()` returns manifest for valid slug
- `[slug]/overview/+page.server.ts` `load()` returns full `AnalysisData`
- Invalid slug → 404
- Empty state: landing page with no analyses → empty array (not crash)

**Component smoke tests** (`tests/unit/components.test.ts`):
- `MetricCard` renders label and value
- `AnalysisCard` renders title, word count, character chips
- `MiniChart` renders `<canvas>` inside accessible `<figure>`

**Fixture data** (`tests/fixtures/test-analysis/`):
Minimal but valid JSON files matching the schema. Small enough to be readable
in tests. 2 chapters, 2 characters, 5 blocks, 10 sentiment points. Includes
`smoothed_arc` and `warnings` fields to match actual engine output.

## Files Created

| File | Purpose |
|---|---|
| `explorer/package.json` | Dependencies: svelte, sveltekit, chart.js, vitest |
| `explorer/svelte.config.js` | adapter-node, alias config |
| `explorer/vite.config.ts` | Vitest integration |
| `explorer/tsconfig.json` | Strict TypeScript |
| `explorer/src/app.html` | Shell with theme flash prevention |
| `explorer/src/app.css` | Global styles, CSS custom properties, theming |
| `explorer/src/lib/types/analysis.ts` | TypeScript interfaces for all JSON schemas |
| `explorer/src/lib/server/data.ts` | JSON file loaders (server-only) |
| `explorer/src/lib/components/MetricCard.svelte` | Metric display card |
| `explorer/src/lib/components/MiniChart.svelte` | Chart.js canvas wrapper |
| `explorer/src/lib/components/AnalysisCard.svelte` | Landing page analysis card |
| `explorer/src/routes/+layout.svelte` | Root layout (top bar, theme, nav) |
| `explorer/src/routes/+page.svelte` | Landing page |
| `explorer/src/routes/+page.server.ts` | Landing page data loader |
| `explorer/src/routes/[slug]/+layout.svelte` | Analysis-scoped layout (sub-nav) |
| `explorer/src/routes/[slug]/+layout.server.ts` | Load manifest for analysis |
| `explorer/src/routes/[slug]/overview/+page.svelte` | Overview dashboard |
| `explorer/src/routes/[slug]/overview/+page.server.ts` | Load all analysis data |
| `explorer/src/routes/[slug]/chapters/+page.svelte` | Placeholder |
| `explorer/src/routes/[slug]/characters/+page.svelte` | Placeholder |
| `explorer/src/routes/[slug]/blocks/+page.svelte` | Placeholder |
| `explorer/tests/unit/data.test.ts` | Data loader unit tests |
| `explorer/tests/unit/components.test.ts` | Component smoke tests |
| `explorer/tests/integration/routes.test.ts` | Route loader integration tests |
| `explorer/tests/fixtures/test-analysis/manifest.json` | Test fixture |
| `explorer/tests/fixtures/test-analysis/analysis.json` | Test fixture |
| `explorer/tests/fixtures/test-analysis/characters.json` | Test fixture |
| `explorer/tests/fixtures/test-analysis/chapters.json` | Test fixture |
| `explorer/tests/fixtures/test-analysis/sentiment.json` | Test fixture |

## Dependencies

```json
{
  "devDependencies": {
    "@sveltejs/adapter-node": "^5",
    "@sveltejs/kit": "^2",
    "svelte": "^5",
    "svelte-check": "^4",
    "typescript": "^5",
    "vite": "^6",
    "vitest": "^3",
    "@testing-library/svelte": "^5"
  },
  "dependencies": {
    "chart.js": "^4"
  }
}
```

## Verification

1. `cd explorer && npm install && npm run build` — builds without errors
2. `npm run check` — svelte-check passes
3. `npm test` — all data loader tests pass
4. `npm run dev` — landing page shows analysis listing (needs JSON in `shared/analyses/`)
5. Click analysis → overview dashboard renders with metric cards + charts
6. Theme toggle works (dark/light/system)
7. Sub-nav links work, placeholder pages render

## Out of Scope (Stage 6+)

- Block explorer (Chart.js interactive click-to-read)
- Character profiles page
- Character deep dive page
- Chapter breakdown (sortable table)
- Reusable BlockReader.svelte component
- Any engine integration from the UI (subprocess trigger)
- Version comparison (`/compare`)
