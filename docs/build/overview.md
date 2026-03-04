# Lit-Explorer: Build Plan Overview
## Engine (Phase 1) → Explorer (Phase 2)

---

## Build Process

Each stage follows this cycle:

1. **Plan** — detailed plan document written to `docs/build/stage-N/plan.md`
2. **Review** — Gemini and Codex each review the plan independently, recording findings in their own review docs
3. **Triage** — we review findings, separate real issues from hallucinations
4. **Implementation Doc** — finalized implementation spec incorporating valid feedback
5. **Second Pass** (optional) — archive first review docs, run another review cycle if confidence is low
6. **Red-Green Tests** — write failing tests first, then implement until they pass
7. **Archive & Advance** — archive the stage docs, move to the next stage

---

## Stage Map

### Stage 1: Foundation + TextTiling Analyzer
**Goal:** Package scaffolding, base analyzer pattern, NLP utilities, config, and the TextTiling analyzer — the backbone everything else is built on.

**Produces:**
- `engine/` package structure with `pyproject.toml`
- Base `Analyzer` class
- `nlp/` module (lazy spaCy loader only — coref and verb categories are Stage 2)
- `config.py` (character lists, stop verbs, parameters)
- `output/json_export.py` (canonical JSON writer)
- `analyzers/texttiling.py` — refactored from `analyze_psychology()`
- `analysis.json` + `manifest.json` output
- Test suite against fixture text

**Key risk:** Getting the analyzer interface right. Every subsequent analyzer depends on this contract.

---

### Stage 2: Agency Analyzer
**Goal:** Character verb profiling with pronoun resolution, passive voice detection, and semantic verb categorization.

**Produces:**
- `analyzers/agency.py` — refactored from `extract_character_agency_v2()`
- `nlp/coref.py` — pronoun resolution heuristics
- `nlp/verb_categories.py` — semantic verb classification
- Character auto-detection via spaCy NER
- `characters.json` output

**Key risk:** Pronoun resolution accuracy. The heuristic works for 2-lead novels but needs clear documentation of its limitations. Also, spaCy NER on literary prose can be noisy.

---

### Stage 3: Supporting Analyzers
**Goal:** All remaining analyzers — chapters, dialogue, readability, pacing, sentiment, silence.

**Produces:**
- `analyzers/chapters.py` — chapter boundary detection + per-chapter aggregation
- `analyzers/dialogue.py` — curly-quote-aware dialogue extraction
- `analyzers/readability.py` — textstat metrics per block and per chapter
- `analyzers/pacing.py` — sentence length distribution + rhythm patterns
- `analyzers/sentiment.py` — VADER emotional arc
- `analyzers/silence.py` — gaps between dialogue
- `chapters.json` + `sentiment.json` output

**Key risk:** Chapter detection regex needs to handle varied formatting. Dialogue extraction with curly quotes vs straight quotes. Analyzer ordering — chapters and dialogue depend on readability/pacing data.

---

### Stage 4: CLI + Integration
**Goal:** Full CLI, orchestration, end-to-end pipeline, integration tests.

**Produces:**
- `cli.py` — `lit-engine analyze`, `lit-engine rerun`, `lit-engine list-analyzers`, `lit-engine extract`
- Analyzer dependency resolution and ordering
- Manifest generation
- End-to-end test: `lit-engine analyze the_specimen_v2.txt` → complete `shared/analyses/the-specimen/`
- Validated JSON output against the canonical schema

**Key risk:** Orchestration ordering, error handling when individual analyzers fail, memory usage on large manuscripts (spaCy doc for 240k chars).

---

### Stage 5: SvelteKit Explorer — Scaffolding + Data Loading
**Goal:** SvelteKit app skeleton, data loading layer, landing page, overview dashboard.

**Produces:**
- `explorer/` SvelteKit app (Svelte 5, runes, TypeScript, adapter-node)
- TypeScript interfaces matching JSON schema
- `+page.server.ts` loaders reading from `shared/analyses/`
- Landing page with analysis listing
- Overview dashboard with metric cards
- Styling: warm paper aesthetic, research notebook feel

**Key risk:** Svelte 5 runes API — ensure we're using `$props()`, `$state()`, `$derived()` correctly per Scriptorium patterns.

---

### Stage 6: Explorer — Interactive Pages
**Goal:** Block explorer, character profiles, chapter breakdown — the interactive analysis views.

**Produces:**
- Block explorer with Chart.js → click-to-read
- Character profiles page (side-by-side, verb domains, voice pies)
- Character deep dive page
- Chapter breakdown (sortable table, dominance bars)
- Reusable Chart.svelte, BlockReader.svelte, ProfileCard.svelte components

**Key risk:** Chart.js interactivity with Svelte 5 lifecycle. Click-to-reveal UX for block explorer needs to feel responsive.

---

### Stage 7: Polish + Compare (Phase 3 features)
**Goal:** Version comparison, PNG export, silence visualization, verb agency over narrative progression.

**Produces:**
- `/compare` route for manuscript version comparison
- PNG chart export
- Silence mapping visualization
- Agency trajectory over narrative progression
- Dark mode

---

## Dependencies Between Stages

```
Stage 1 (Foundation + TextTiling)
  └─→ Stage 2 (Agency) — needs base Analyzer, NLP loader
  └─→ Stage 3 (Supporting) — needs base Analyzer, TextTiling blocks
       └─→ Stage 4 (CLI) — needs all analyzers
            └─→ Stage 5 (Explorer scaffold) — needs JSON output to exist
                 └─→ Stage 6 (Explorer pages) — needs scaffold + data
                      └─→ Stage 7 (Polish) — needs everything
```

Stages 2 and 3 can potentially be developed in parallel once Stage 1 is solid, since they produce independent JSON files. But Stage 3's `chapters.py` aggregates data from other analyzers, so it's cleaner to do them sequentially.

---

## Existing Code Inventory

| Source | Destination | Status |
|--------|-------------|--------|
| `analyze_psychology()` | `analyzers/texttiling.py` | Stage 1 |
| `mattr()` | `analyzers/texttiling.py` | Stage 1 |
| `extract_character_agency_v2()` | `analyzers/agency.py` | Stage 2 |
| `resolve_pronouns_simple()` | `nlp/coref.py` | Stage 2 |
| `verb_categories` dict | `nlp/verb_categories.py` | Stage 2 |
| `stop_verbs` set | `config.py` | Stage 1 |
| `explore_block()` | `cli.py` (extract command) | Stage 4 |
| Chart generation code | Dropped (explorer handles visualization) | — |

## Test Manuscripts

- `~/Documents/lit-analysis/the_specimen.txt` — v1, ~290k chars
- `~/Documents/lit-analysis/the_specimen_v2.txt` — v2, ~241k chars (primary target)
