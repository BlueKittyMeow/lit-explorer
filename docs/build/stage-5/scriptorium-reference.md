# Scriptorium Architecture Reference

> Context for reviewers: Scriptorium is a separate SvelteKit writing application
> that lit-explorer will eventually integrate into (spec Phase 4). This document
> captures the patterns, types, and conventions we must match in the lit-explorer
> frontend so components can migrate cleanly. Reviewers who cannot access the
> Scriptorium repo should treat this as the canonical reference.

## 1. Overview

Scriptorium is a **preservation-first writing application** built with SvelteKit + SQLite.
Two roles: **writer** (Kyla) and **archivist** (Lara). It handles novel organization,
rich-text editing (TipTap), snapshot versioning, full-text search (FTS5), Scrivener import,
compile/export (Pandoc), and version comparison/merge.

**Key architectural principle:** File is source of truth for content. HTML stored on disk
at `/data/{novel-uuid}/docs/{docid}.html`; SQLite stores metadata + search index only.

## 2. Tech Stack (What We Must Match)

| Concern | Scriptorium | Lit-Explorer Must Use |
|---|---|---|
| Framework | SvelteKit | SvelteKit |
| Svelte version | Svelte 5 (runes) | Svelte 5 (runes) |
| Adapter | `@sveltejs/adapter-node` | `@sveltejs/adapter-node` |
| Language | TypeScript (strict) | TypeScript (strict) |
| Testing | Vitest | Vitest |
| Package manager | npm | npm |
| CSS | Custom (no framework) | Custom (no framework) |
| Data loading | `+page.server.ts` | `+page.server.ts` |
| Node version | 22+ | 22+ |

## 3. Svelte 5 Runes Patterns

Scriptorium uses runes exclusively. No legacy stores, no `createEventDispatcher`.

### Component props
```svelte
<script lang="ts">
  let { data, type = 'line', options = {} }: {
    data: ChartData;
    type?: string;
    options?: ChartOptions;
  } = $props();
</script>
```

### Reactive state
```typescript
let tree: TreeNode[] = $state([]);
let activeDocId: string | null = $state(null);
let showSnapshots = $state(false);
let totalWords = $derived(tree.reduce((sum, n) => sum + (n.word_count ?? 0), 0));
```

### Effects
```typescript
$effect(() => {
  // runs when dependencies change
  chart.update({ data });
});
```

### No centralized store library
All state is component-local via `$state`. Server data arrives through
`+page.server.ts` `load()` functions and flows down as props. No Svelte stores,
no Redux, no context API for global state.

## 4. Data Models (Relevant Types)

### Novel (the manuscript container)
```typescript
interface Novel {
  id: string;           // UUID
  title: string;
  subtitle: string | null;
  status: string;       // 'draft' | 'revision' | 'complete' | 'abandoned'
  word_count_target: number | null;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;  // soft-delete
}
```

### Document (atomic writing unit = one "scene" or "chapter")
```typescript
interface Document {
  id: string;           // UUID
  novel_id: string;
  parent_id: string | null;   // folder it belongs to
  title: string;              // e.g., "Chapter 1 - Cafe Union"
  synopsis: string | null;
  word_count: number;         // computed from stripped HTML on save
  compile_include: number;    // 1/0 boolean
  sort_order: number;         // float for easy reordering
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
```

Content lives at `/data/{novel_id}/docs/{id}.html` (TipTap HTML output).

### Folder (organizational container)
```typescript
interface Folder {
  id: string;
  novel_id: string;
  parent_id: string | null;
  title: string;
  folder_type: string | null;  // 'Manuscript' | 'Research' | 'Notes' | 'Characters'
  sort_order: number;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
}
```

### TreeNode (UI binder tree)
```typescript
interface TreeNode {
  id: string;
  type: 'folder' | 'document';
  title: string;
  sort_order: number;
  folder_type?: string | null;
  word_count?: number;
  compile_include?: number;
  synopsis?: string | null;
  deleted_at: string | null;
  children: TreeNode[];
}
```

### Snapshot (immutable version)
```typescript
interface Snapshot {
  id: string;
  document_id: string;
  content_path: string;
  word_count: number | null;
  reason: string;        // 'autosave' | 'manual' | 'pre-restructure' | 'pre-sync-conflict'
  created_at: string;
}
```

## 5. Chapter Handling — Critical for Integration

**Scriptorium has no first-class "chapter" entity.** Chapters are Documents
organized in the tree hierarchy:

```
Novel
├── Manuscript/ (folder, folder_type: "Manuscript")
│   ├── Chapter 1: The Beginning (document, sort_order: 1.0)
│   ├── Chapter 2: The Rising Action (document, sort_order: 2.0)
│   └── Chapter 3: The Climax (document, sort_order: 3.0)
├── Research/ (folder)
└── Notes/ (folder)
```

### Chapter title normalization (from compare/match module)
Scriptorium strips chapter prefixes for matching:
```typescript
function normalizeTitle(title: string): string {
  let t = title.toLowerCase().trim();
  t = t.replace(/^chapter\s+\d+\s*[:—–\-]?\s*/i, '').trim();
  return t;
}
```

This is the same pattern our `chapter_detect.py` uses (regex: `chapter|kapitel|teil` +
number + optional dash/title). The engine's `ChapterBoundary.title` field already
stores the normalized title after the dash.

### Compile assembly wraps chapters in sections
```html
<section class="chapter">
  <h1>Chapter 1: The Beginning</h1>
  <!-- document HTML content -->
</section>
```

### Integration implication
When Scriptorium triggers analysis (Phase 4), it will:
1. Walk the binder tree, collect documents in sort_order
2. Concatenate their stripped HTML into plain text
3. Pass to `lit-engine analyze` as a subprocess
4. Map analysis chapter boundaries back to Scriptorium document IDs

The engine's chapter detection (regex on "Chapter N") works on the compiled text.
For Scriptorium integration, chapter boundaries will be **known** from the tree
structure — no detection needed. The engine should accept an optional
`--chapter-boundaries` flag or config that provides pre-known boundaries, bypassing
regex detection. This is a Phase 4 concern, not Stage 5.

## 6. File & Data Patterns

### Content storage
- **Documents**: `/data/{novelId}/docs/{docId}.html` (atomic writes: tmp → fsync → rename)
- **Snapshots**: `/data/{novelId}/snapshots/{docId}/{snapshotId}.html`
- **Database**: SQLite with WAL mode (`scriptorium.db`)
- **Search**: FTS5 virtual table on stripped plaintext

### Lit-explorer's JSON files pattern
Our engine writes to `shared/analyses/{slug}/`. Scriptorium will eventually store
analysis results alongside novel data. The JSON schema is the bridge:

| Engine output | Scriptorium consumer |
|---|---|
| `manifest.json` | Novel analysis metadata (store in SQLite row) |
| `analysis.json` | Block explorer data (store as JSON blob or separate table) |
| `characters.json` | Character profiles → Reference Desk (Phase 4) |
| `chapters.json` | Per-chapter metrics → chapter cards/dashboard |
| `sentiment.json` | Emotional arc → visualization |

## 7. API Route Patterns

Scriptorium uses SvelteKit file-based routing with `+server.ts` endpoints:

```
src/routes/
├── api/
│   ├── novels/+server.ts           GET (list), POST (create)
│   ├── novels/[id]/+server.ts      GET, PUT, DELETE
│   ├── novels/[id]/tree/+server.ts GET (full tree)
│   ├── documents/[id]/+server.ts   GET (metadata+content), PUT (save)
│   ├── search/+server.ts           GET (?q=term&novel=id)
│   └── ...
├── novels/[id]/+page.svelte        Editor page
├── novels/compare/+page.svelte     Compare/merge
├── admin/+page.svelte              Admin dashboard
└── +page.svelte                    Library (novel list)
```

**Lit-explorer should follow the same patterns:**
- API endpoints in `src/routes/api/` using `+server.ts`
- Page data via `+page.server.ts` load functions (not client-side fetch)
- File-based routing for all pages

### Auth pattern (for reference, not needed in explorer)
Scriptorium uses session tokens (SHA-256 hashed, bcrypt passwords, 30-day sliding
expiry). The explorer is single-user with no auth — but if we ever add auth for
the integrated version, Scriptorium's pattern is the model.

## 8. Component Patterns

### Editor: TipTap (ProseMirror)
- Props: `docId`, `initialContent`, `title`, `onsave` callback
- Output: HTML
- Features: autosave with debounce, live word count, search highlighting, focus mode

### Compile pipeline
1. Tree-walk → collect documents in sort_order
2. Assemble HTML with `<section class="chapter">` wrappers
3. Pandoc: stdin → stdout → target format

### Compare/merge
- 4-phase document matching: exact title → fuzzy title → content similarity (Jaccard) → unmatched
- Word-level diffing via `jsdiff`
- Merge choices: use A / use B / keep both / skip

### Theming
- CSS custom properties (~27 variables)
- Dark/light/system mode toggle
- No external CSS framework
- Flash prevention via inline `<script>` in `app.html`

## 9. What Lit-Explorer Stage 5 Should Borrow

### Must match
- Svelte 5 runes everywhere (`$props`, `$state`, `$derived`, `$effect`)
- TypeScript strict mode
- `+page.server.ts` for data loading
- `adapter-node`
- Custom CSS (no Tailwind, no Bootstrap)
- npm (not pnpm, not yarn, not bun)
- Vitest for tests

### Should match (for future component portability)
- Chart components as standalone `.svelte` files with typed `$props()`
- Reusable UI primitives: cards, tables, modals as components in `$lib/components/`
- Types in `$lib/types/` (mirroring Scriptorium's `$lib/types.ts` pattern)
- Server utilities in `$lib/server/`

### Not needed (explorer-specific)
- No auth (single-user)
- No database (reads JSON from disk)
- No TipTap editor (read-only text display)
- No drag-and-drop tree
- No snapshot versioning

## 10. Future Integration Touchpoints (Phase 4)

These are decisions we should be aware of but NOT implement in Stage 5:

1. **Analysis trigger**: Scriptorium's novel view gets an "Analyze" button →
   calls `lit-engine` as subprocess with compiled text
2. **Results storage**: Analysis JSON moves into Scriptorium's data directory
   (or SQLite table)
3. **Character entity bridge**: Agency analysis populates Scriptorium's
   Reference Desk character profiles (Phase 4 of Scriptorium spec)
4. **Chapter boundary passthrough**: Scriptorium knows its own chapter structure
   from the binder tree — should pass boundaries to engine rather than
   re-detecting via regex
5. **Component migration**: Chart, BlockReader, ProfileCard components move
   from explorer's `$lib` into Scriptorium's `$lib`
