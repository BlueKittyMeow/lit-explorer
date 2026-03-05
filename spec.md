# Lit-Explorer
### A computational stylistics toolkit for literary manuscripts
### Design Document v0.1

---

## Vision

Lara opens a web interface, selects a manuscript, and within minutes has a rich analytical portrait: the psychological architecture of the prose, character agency profiles, dialogue patterns, emotional arcs, and the ability to click on any spike in any chart to read the exact passage that caused it. It's ProWritingAid for literary scholars — but open, extensible, and built to eventually live inside Scriptorium.

**Design philosophy:** The analysis engine should be a black box that accepts text and emits structured JSON. The frontend should feel like an interactive research notebook. The two should know nothing about each other except the shape of the data.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                lit-explorer (monorepo)            │
│                                                   │
│  ┌────────────────────┐   ┌────────────────────┐  │
│  │   engine/           │   │   explorer/         │  │
│  │   (Python package)  │   │   (SvelteKit app)   │  │
│  │                     │   │                     │  │
│  │  ┌───────────────┐  │   │  ┌───────────────┐  │  │
│  │  │  Analyzers     │  │   │  │  Routes        │  │  │
│  │  │  - texttiling  │  │   │  │  /             │  │  │
│  │  │  - agency      │  │   │  │  /overview     │  │  │
│  │  │  - dialogue    │  │   │  │  /chapters     │  │  │
│  │  │  - readability │  │   │  │  /characters   │  │  │
│  │  │  - sentiment   │  │   │  │  /blocks/:id   │  │  │
│  │  │  - pacing      │  │   │  │  /compare      │  │  │
│  │  └───────────────┘  │   │  └───────────────┘  │  │
│  │         │           │   │         │           │  │
│  │  ┌───────────────┐  │   │  ┌───────────────┐  │  │
│  │  │  NLP Core      │  │   │  │  Components    │  │  │
│  │  │  - spaCy lg    │  │   │  │  - Charts      │  │  │
│  │  │  - pronoun res │  │   │  │  - BlockReader │  │  │
│  │  │  - NLTK tiles  │  │   │  │  - ProfileCard│  │  │
│  │  └───────────────┘  │   │  │  - DataTable   │  │  │
│  │         │           │   │  └───────────────┘  │  │
│  │    ┌─────────┐      │   │         │           │  │
│  │    │  CLI    │      │   │    ┌─────────┐      │  │
│  │    │  main() │      │   │    │  Stores  │      │  │
│  │    └────┬────┘      │   │    │ (Svelte) │      │  │
│  │         │           │   │    └─────────┘      │  │
│  └─────────┼───────────┘   └────────┼────────────┘  │
│            │                        │               │
│            ▼                        ▼               │
│     ┌──────────────────────────────────┐            │
│     │   shared/analyses/{manuscript}/   │            │
│     │     analysis.json                 │            │
│     │     blocks.json                   │            │
│     │     characters.json               │            │
│     │     chapters.json                 │            │
│     │     manuscript.txt (copy)         │            │
│     └──────────────────────────────────┘            │
└──────────────────────────────────────────────────┘
```

**The contract:** The Python engine writes JSON files to `shared/analyses/{slug}/`. The SvelteKit app reads them via `+server.js` endpoints that load from disk. They share no code, no runtime, no process. The JSON schema IS the API.

---

## Repository Structure

```
lit-explorer/
├── README.md
├── spec.md                          ← this file
│
├── engine/                          ← Python package
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── src/
│   │   └── lit_engine/
│   │       ├── __init__.py
│   │       ├── cli.py              ← CLI entry: lit-engine analyze <file>
│   │       ├── config.py           ← character lists, stop verbs, etc.
│   │       ├── analyzers/
│   │       │   ├── __init__.py
│   │       │   ├── texttiling.py   ← TextTiling segmentation + MATTR
│   │       │   ├── agency.py       ← character verb profiling + coref
│   │       │   ├── dialogue.py     ← dialogue vs narration ratios
│   │       │   ├── readability.py  ← Flesch, Fog, textstat metrics
│   │       │   ├── sentiment.py    ← VADER emotional arc
│   │       │   ├── pacing.py       ← sentence length distribution
│   │       │   ├── chapters.py     ← chapter detection + per-chapter stats
│   │       │   └── silence.py      ← gaps between dialogue
│   │       ├── nlp/
│   │       │   ├── __init__.py
│   │       │   ├── loader.py       ← lazy spaCy model loading
│   │       │   ├── coref.py        ← pronoun resolution heuristics
│   │       │   └── verb_categories.py ← semantic verb classification
│   │       └── output/
│   │           ├── __init__.py
│   │           └── json_export.py  ← writes the canonical JSON schema
│   └── tests/
│       ├── test_texttiling.py
│       ├── test_agency.py
│       └── fixtures/
│           └── sample_text.txt     ← short excerpt for fast testing
│
├── explorer/                        ← SvelteKit app
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css
│   │   ├── routes/
│   │   │   ├── +layout.svelte      ← nav, manuscript selector
│   │   │   ├── +layout.server.ts   ← loads available analyses
│   │   │   ├── +page.svelte        ← landing: upload or select
│   │   │   ├── overview/
│   │   │   │   ├── +page.svelte    ← dashboard: all charts at a glance
│   │   │   │   └── +page.server.ts
│   │   │   ├── chapters/
│   │   │   │   ├── +page.svelte    ← chapter-by-chapter breakdown
│   │   │   │   └── +page.server.ts
│   │   │   ├── characters/
│   │   │   │   ├── +page.svelte    ← agency profiles side by side
│   │   │   │   ├── [name]/
│   │   │   │   │   ├── +page.svelte ← single character deep dive
│   │   │   │   │   └── +page.server.ts
│   │   │   │   └── +page.server.ts
│   │   │   ├── blocks/
│   │   │   │   ├── +page.svelte    ← block explorer (click chart → text)
│   │   │   │   ├── [id]/
│   │   │   │   │   ├── +page.svelte ← single block close reading
│   │   │   │   │   └── +page.server.ts
│   │   │   │   └── +page.server.ts
│   │   │   └── compare/
│   │   │       ├── +page.svelte    ← compare two manuscript versions
│   │   │       └── +page.server.ts
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── Chart.svelte        ← reusable chart (wraps Chart.js)
│   │   │   │   ├── BlockReader.svelte  ← prose display with annotations
│   │   │   │   ├── ProfileCard.svelte  ← character verb profile
│   │   │   │   ├── VerbDomain.svelte   ← bar chart of semantic categories
│   │   │   │   ├── PieChart.svelte     ← voice distribution pie
│   │   │   │   ├── ChapterRow.svelte   ← chapter stats row
│   │   │   │   ├── MetricCard.svelte   ← single stat with sparkline
│   │   │   │   └── ManuscriptSelector.svelte
│   │   │   ├── stores/
│   │   │   │   └── analysis.ts     ← Svelte stores for loaded data
│   │   │   ├── types/
│   │   │   │   └── analysis.ts     ← TypeScript interfaces matching JSON schema
│   │   │   └── utils/
│   │   │       └── format.ts       ← number formatting, color scales
│   │   └── static/
│   │       └── (favicon, etc.)
│   └── tests/
│       └── ... (vitest, matching Scriptorium patterns)
│
└── shared/                          ← the bridge
    └── analyses/
        └── the-specimen/            ← created by engine, read by explorer
            ├── manifest.json        ← metadata about the analysis run
            ├── analysis.json        ← TextTiling blocks + metrics
            ├── characters.json      ← agency profiles
            ├── chapters.json        ← chapter-level stats
            ├── sentiment.json       ← emotional arc
            └── manuscript.txt       ← copy of source text (for block reading)
```

---

## JSON Schema (The Contract)

This is the critical boundary. Everything the engine produces and everything the explorer consumes is defined here.

### manifest.json

```json
{
  "title": "The Specimen",
  "slug": "the-specimen",
  "source_file": "the_specimen_v2.txt",
  "analyzed_at": "2026-03-03T02:30:00Z",
  "engine_version": "0.1.0",
  "word_count": 43218,
  "char_count": 240809,
  "chapter_count": 16,
  "character_list": ["emil", "felix"],
  "analyzers_run": [
    "texttiling", "agency", "dialogue", "readability",
    "sentiment", "pacing", "chapters", "silence"
  ],
  "parameters": {
    "texttiling_w": 40,
    "texttiling_k": 20,
    "spacy_model": "en_core_web_lg",
    "coref_enabled": true,
    "mattr_window": 50
  }
}
```

### analysis.json (TextTiling blocks)

```json
{
  "parameters": { "w": 40, "k": 20, "mattr_window": 50 },
  "total_blocks": 217,
  "blocks": [
    {
      "id": 1,
      "tile_index": 0,
      "start_char": 0,
      "end_char": 1247,
      "word_count": 198,
      "sentence_count": 5,
      "metrics": {
        "mattr": 0.7916,
        "avg_sentence_length": 41.5,
        "max_sentence_length": 122,
        "flesch_ease": 30.5,
        "flesch_grade": 20.6,
        "gunning_fog": 22.0
      },
      "sentence_lengths": [42, 18, 122, 9, 7],
      "preview": "When lights were paling one by one...",
      "chapter": 0
    }
  ],
  "notable": {
    "longest_sentences": [1, 98, 132, 130, 16],
    "highest_mattr": [68, 25, 95, 4, 140],
    "highest_fog": [1, 132, 131, 98, 130],
    "shortest_sentences": [297, 180, 51]
  }
}
```

### characters.json (Agency profiles)

```json
{
  "characters": {
    "emil": {
      "total_verbs": 744,
      "active_count": 722,
      "passive_count": 22,
      "intransitive_count": 392,
      "via_name": 277,
      "via_pronoun": 620,
      "verb_domains": {
        "perception": 82,
        "cognition": 70,
        "motion": 67,
        "physical_action": 84,
        "gesture": 55,
        "emotion": 36,
        "resistance": 11,
        "speech": 6,
        "other": 311
      },
      "top_verbs": [
        { "verb": "see", "count": 34, "category": "perception" },
        { "verb": "know", "count": 25, "category": "cognition" }
      ],
      "top_actions": [
        { "action": "shake -> head", "count": 5 },
        { "action": "open -> mouth", "count": 4 },
        { "action": "resist -> urge", "count": 3 }
      ],
      "passive_verbs": [
        { "verb": "make", "count": 2 },
        { "verb": "force", "count": 2 }
      ],
      "passive_agents": [
        { "agent": "crematory", "count": 1 }
      ]
    },
    "felix": { }
  }
}
```

### chapters.json

```json
{
  "chapters": [
    {
      "number": 1,
      "title": "Café Union",
      "word_count": 3433,
      "sentence_count": 240,
      "dialogue_ratio": 0.463,
      "avg_sentence_length": 14.3,
      "mattr": 0.812,
      "flesch_ease": 72.1,
      "fog": 9.4,
      "character_mentions": {
        "emil": 41,
        "felix": 42,
        "helena": 1,
        "reichmann": 3
      },
      "dominant_character": "shared",
      "sentiment": {
        "compound": 0.12,
        "pos": 0.08,
        "neg": 0.04,
        "neu": 0.88
      },
      "block_range": [1, 16]
    }
  ]
}
```

### sentiment.json

```json
{
  "method": "vader",
  "granularity": "sentence",
  "arc": [
    { "position": 0.0, "compound": 0.15, "pos": 0.08, "neg": 0.02 },
    { "position": 0.01, "compound": -0.34, "pos": 0.01, "neg": 0.12 }
  ],
  "chapter_averages": [
    { "chapter": 1, "compound": 0.12 }
  ],
  "extremes": {
    "most_positive": { "position": 0.45, "text_preview": "...", "score": 0.89 },
    "most_negative": { "position": 0.78, "text_preview": "...", "score": -0.92 }
  }
}
```

---

## Python Engine

### CLI Interface

```bash
# Full analysis (all analyzers)
lit-engine analyze manuscript.txt --output ./shared/analyses/the-specimen/

# Specify characters (auto-detected if omitted)
lit-engine analyze manuscript.txt --characters emil,felix

# Run specific analyzers only
lit-engine analyze manuscript.txt --only texttiling,agency

# Custom TextTiling parameters
lit-engine analyze manuscript.txt --tt-window 40 --tt-smoothing 20

# Re-run a single analyzer (partial recompute with transitive deps)
lit-engine rerun agency manuscript.txt --output ./shared/analyses/the-specimen/

# List available analyzers
lit-engine list-analyzers

# Extract a specific block for close reading
lit-engine extract manuscript.txt --block 203 --tt-window 20
```

### Dependencies

```
# requirements.txt
spacy>=3.7
nltk>=3.8
textstat>=0.7
matplotlib>=3.7       # for optional PNG chart export
seaborn>=0.13         # for optional PNG chart export
vaderSentiment>=3.3   # sentiment analysis
```

```bash
# Setup
python -m spacy download en_core_web_lg
python -c "import nltk; nltk.download('punkt_tab'); nltk.download('stopwords')"
```

### Analyzer Interface

Every analyzer follows the same pattern:

```python
class Analyzer:
    """Base interface for all analyzers."""

    name: str           # e.g., "texttiling"
    description: str    # human-readable
    requires_spacy: bool = False
    requires_nltk: bool = False

    def analyze(self, text: str, config: dict) -> dict:
        """
        Accept raw text + config, return JSON-serializable dict.
        This dict becomes the analyzer's section of the output.
        """
        raise NotImplementedError

    def requires(self) -> list[str]:
        """List other analyzers this depends on (for ordering)."""
        return []
```

### Analyzers

**texttiling** — Semantic segmentation via TextTiling + MATTR + readability per block. Core of the architecture chart. Produces `analysis.json`.

**agency** — Character verb profiling with pronoun resolution + passive voice detection + semantic verb categorization. Produces `characters.json`.

**dialogue** — Curly-quote-aware dialogue extraction. Computes dialogue ratio per chapter and identifies speaker where possible. Contributes to `chapters.json`.

**readability** — textstat metrics (Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog, Coleman-Liau, SMOG, Automated Readability Index) per block and per chapter.

**sentiment** — VADER sentence-level sentiment analysis. Produces emotional arc and identifies extreme moments. Produces `sentiment.json`.

**pacing** — Sentence length distribution, rhythm patterns, staccato/flowing passage detection. Contributes to `analysis.json`.

**chapters** — Chapter boundary detection (regex-based, configurable), per-chapter aggregation of all other metrics, character presence counting. Produces `chapters.json`.

**silence** — Measures gaps between dialogue (in word count). Maps where characters go quiet. Contributes to `chapters.json`.

### Character Auto-Detection

If `--characters` is not provided, the engine should auto-detect likely character names:

1. Run spaCy NER, collect all PERSON entities
2. Count occurrences, filter to those appearing > N times (default 10)
3. Use the top characters (capped at 8 to keep analysis focused)
4. Store detected list in `manifest.json` for frontend to read

### Pronoun Resolution Strategy

For literary prose with a small cast (2-6 characters), the heuristic resolver works as follows:

1. Track most recent named character mention per gender per sentence
2. For "he/him/his" → assign to most recent male character
3. For "she/her/hers" → assign to most recent female character
4. In sentences with BOTH male characters named, skip pronoun resolution (ambiguous)
5. Track confidence: `via_name` vs `via_pronoun` counts let the frontend show how much of the data is inferred

This is documented as an approximation. The schema leaves room for a future `coref_method` field in `manifest.json` that could be `"heuristic"`, `"booknlp"`, or `"neural"`.

---

## SvelteKit Explorer

### Tech Stack

Matching Scriptorium's patterns:
- SvelteKit with `adapter-node`
- Svelte 5 (runes)
- TypeScript
- Vitest for testing
- Chart.js for charts (lightweight, interactive, good Svelte bindings)
- No database — reads JSON from disk via `+page.server.ts` load functions

### Pages

**`/` — Landing**
- Shows list of available analyses (reads `shared/analyses/*/manifest.json`)
- Upload button to trigger a new analysis (calls engine via subprocess)
- Each manuscript shows: title, word count, date analyzed, analyzers run

**`/overview` — Dashboard**
- At-a-glance view of the manuscript
- Key metrics in cards: total words, chapters, characters detected, dialogue ratio
- Mini versions of the main charts (click to expand)
- "Notable" callouts: longest sentence, richest passage, most complex chapter

**`/chapters` — Chapter Breakdown**
- Table/cards for each chapter showing all per-chapter metrics
- Sortable by any column
- Character dominance bars (like the ASCII chart we made, but interactive)
- Dialogue ratio bars
- Click a chapter → filtered view of its blocks

**`/characters` — Agency Profiles**
- Side-by-side character cards
- Semantic verb domain bar charts
- Voice distribution pie charts
- Top verbs and top actions lists
- Click a character → deep dive page

**`/characters/[name]` — Character Deep Dive**
- Full verb listing with categories
- Passive voice section (what's done TO them)
- Verb frequency over narrative progression (does their agency change?)
- Comparison toggle (overlay another character)

**`/blocks` — Block Explorer**
- The big chart (MATTR + sentence length over blocks)
- CLICK ON ANY POINT → slides open the block text below
- Block text displayed with sentence boundaries highlighted
- Readability metrics sidebar for the selected block
- Navigate between blocks with arrow keys

**`/blocks/[id]` — Block Close Reading**
- Full text of a single block
- Every sentence on its own line with word count
- Readability scores
- Character mentions highlighted
- Links to adjacent blocks

**`/compare` — Version Comparison (Phase 2)**
- Select two manuscript versions
- Side-by-side metric comparison
- Delta charts (what changed between revisions)

### Component Design

All chart components should be designed for extraction into Scriptorium later:

```svelte
<!-- Chart.svelte — wraps Chart.js canvas -->
<script lang="ts">
  import { onMount } from 'svelte';
  import Chart from 'chart.js/auto';

  let { data, type = 'line', options = {} }: {
    data: ChartData;
    type?: string;
    options?: ChartOptions;
  } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart;

  onMount(() => {
    chart = new Chart(canvas, { type, data, options });
    return () => chart.destroy();
  });
</script>

<canvas bind:this={canvas}></canvas>
```

```svelte
<!-- BlockReader.svelte — displays a text block with annotations -->
<script lang="ts">
  import type { Block } from '$lib/types/analysis';

  let { block, highlightCharacters = true }: {
    block: Block;
    highlightCharacters?: boolean;
  } = $props();
</script>

<article class="block-reader">
  <header>
    <span class="block-num">Block {block.id}</span>
    <span class="metrics">
      MATTR: {block.metrics.mattr.toFixed(3)} ·
      Avg sentence: {block.metrics.avg_sentence_length.toFixed(1)} words ·
      Fog: {block.metrics.gunning_fog.toFixed(1)}
    </span>
  </header>
  <div class="prose">
    <!-- render sentences with highlighting -->
  </div>
</article>
```

### Styling

Simple, readable, archival feel. Dark option. Think: a research notebook, not a SaaS dashboard. Minimal color palette, generous whitespace, monospace for metrics, serif for prose display. The charts should feel like figures in an academic paper, not a startup pitch deck.

Color palette (light mode):
- Background: `#faf9f7` (warm paper)
- Text: `#2c2c2c`
- Accent: `#4a6fa5` (muted blue)
- Highlight: `#e8c170` (warm gold)
- Chart colors: muted, distinguishable, print-friendly

---

## Development Workflow

### Phase 1: Engine (Python)
1. Extract and refactor existing `specimen_analysis_v2.py` into the analyzer pattern
2. Implement JSON export to the canonical schema
3. Build CLI with `click` or `argparse`
4. Add VADER sentiment analyzer
5. Add silence mapping
6. Write tests against fixture text
7. Document: `lit-engine analyze the_specimen.txt` should Just Work

### Phase 2: Explorer (SvelteKit)
1. Scaffold SvelteKit app matching Scriptorium's patterns
2. Build `+page.server.ts` loaders that read from `shared/analyses/`
3. Landing page with analysis listing
4. Overview dashboard with metric cards
5. Block explorer with interactive chart → text reveal
6. Character profiles page
7. Chapter breakdown page

### Phase 3: Polish & Features
1. Auto-detect characters (NER-based)
2. Version comparison (`/compare`)
3. PNG chart export (for embedding in documents)
4. BookNLP integration (optional venv, richer coref + directed sentiment)
5. Silence mapping visualization
6. Verb agency over narrative progression (does a character gain/lose agency?)

### Phase 4: Scriptorium Integration
1. Move Chart, BlockReader, ProfileCard components into Scriptorium's `$lib`
2. Add "Analyze" button to Scriptorium's novel view
3. Scriptorium calls `lit-engine` as a subprocess with the novel's compiled text
4. Analysis results stored in Scriptorium's data directory
5. Reference Desk (Phase 4 of Scriptorium spec) consumes character data from analysis
6. Character entities auto-populated from agency analysis
7. Document ↔ character mention links generated from NER results

---

## Existing Work

The following already works and should be refactored into the engine:

**From `~/Documents/lit-analysis/specimen_analysis_v2.py`:**
- `analyze_psychology()` → becomes `texttiling` analyzer
- `extract_character_agency_v2()` → becomes `agency` analyzer
- `resolve_pronouns_simple()` → moves to `nlp/coref.py`
- `mattr()` function → moves to `analyzers/texttiling.py`
- `explore_block()` → becomes part of CLI `extract` command
- Verb categories dict → moves to `nlp/verb_categories.py`

**From interactive analysis sessions (not yet in script):**
- Chapter detection with curly-quote-aware dialogue ratio → `chapters` analyzer
- Character dominance per chapter → `chapters` analyzer
- Character presence counting → `chapters` analyzer

**Manuscripts available for testing:**
- `~/Documents/lit-analysis/the_specimen.txt` — v1, 290k chars
- `~/Documents/lit-analysis/the_specimen_v2.txt` — v2, 241k chars (updated revision)

---

## Scriptorium Compatibility Notes

For eventual integration, match these Scriptorium patterns:

- **SvelteKit version:** Svelte 5 with runes (`$props()`, `$state()`, `$derived()`)
- **Adapter:** `@sveltejs/adapter-node`
- **Testing:** Vitest
- **TypeScript:** yes, strict
- **Package manager:** npm
- **No external CSS framework** — write your own (Scriptorium does this)
- **Server-side data loading** via `+page.server.ts` (not client-side fetch)
- **No database in the explorer** — reads JSON files. When integrated into Scriptorium, the data lives in Scriptorium's SQLite alongside novel metadata.

---

## Open Questions

1. **BookNLP:** Worth setting up a Python 3.9 venv for richer coreference + directed sentiment? Current heuristic pronoun resolution works for 2-lead novels but doesn't handle ambiguous "he" in scenes where both leads are present.

2. **Manuscript format:** Currently assumes `.txt`. Should we support HTML (from Scriptorium's TipTap editor) and `.scriv` (Scrivener) input? Scriptorium already has `.scriv` import code we could reference.

3. **Real-time vs batch:** Current design is batch (run engine, view results). Should the explorer be able to trigger analysis from the UI? (Probably yes — subprocess call from a SvelteKit server action.)

4. **Multi-manuscript comparison:** The `/compare` route assumes two versions of the same manuscript. But Lara might want to compare The Specimen against another novel entirely (baseline literary fingerprint). Worth building for?

---

## Why This Architecture

**Why monorepo?** Engine and explorer develop together. Shared type definitions. One `git clone` to get everything. Can split later if needed.

**Why JSON files, not a database?** The analysis data is write-once, read-many. There's no user state to persist, no concurrent writes, no relational queries needed. JSON files are human-readable (you can inspect them in any editor), trivially versionable (git-diff friendly), and the explorer's `+page.server.ts` can read them with zero dependencies. When this integrates into Scriptorium, the data moves into SQLite alongside the rest of the novel metadata — but that's Scriptorium's concern, not the explorer's.

**Why SvelteKit for a tool with one user?** Because that one user also maintains Scriptorium, and every component built here is a component that doesn't need to be rebuilt when the analysis features migrate into the writing app. The development cost is roughly the same as any other frontend, with the bonus of direct portability.

**Why Python for the engine instead of JavaScript?** spaCy, NLTK, textstat, and the entire NLP ecosystem is Python. There are no comparable JavaScript libraries for TextTiling, dependency parsing, or coreference resolution. The engine MUST be Python. The frontend can be anything — we chose SvelteKit because of Scriptorium.
