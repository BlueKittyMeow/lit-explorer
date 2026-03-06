Loaded cached credentials.
Server 'context7' supports tool updates. Listening for changes...
### [BUG/INCONSISTENCY] Ignored Whole-Text Readability Metrics
The `lit-engine` CLI (`engine/src/lit_engine/cli.py`) ignores the `whole_text` results produced by the `readability` analyzer. Only the per-block metrics are merged into the final `analysis.json`.
**Impact**: This forces the frontend to calculate averages manually in `+page.svelte` using a simple mean of blocks. For non-linear metrics like SMOG or Gunning Fog, this manual average is less accurate than the engine's whole-text calculation.
**Suggestion**: Update the CLI enrichment pipeline to merge the `whole_text` object into the root of the `analysis.json` payload, and update the frontend to prioritize these pre-calculated values.

### [CONCERN] Hardcoded Chart Colors (Theme Consistency)
The `MiniChart` instances in `explorer/src/routes/[slug]/overview/+page.svelte` use hardcoded HSL values for `borderColor` and `backgroundColor` (e.g., `hsl(220, 50%, 55%)`).
**Impact**: These hardcoded values ignore the CSS variable-based theme defined in `app.css`. This can lead to poor contrast or aesthetic inconsistency when the application is switched to dark mode, as the charts will not automatically adapt to the theme change.
**Suggestion**: Use CSS variables (e.g., via `getComputedStyle` in the `$effect` block) or a dedicated theme utility to provide colors to Chart.js that stay in sync with the `app.css` variables.

### [CONCERN] SSR-Incompatible Chart.js Import
`explorer/src/lib/components/MiniChart.svelte` uses a top-level import for `chart.js/auto`.
**Impact**: While the `Chart` instantiation is correctly wrapped in a client-only `$effect`, the top-level import itself can cause the SvelteKit server to crash during SSR if the version of `chart.js` references `window` or `document` at the module level.
**Suggestion**: Use a dynamic import for `Chart` within the `$effect` block (e.g., `const { default: Chart } = await import('chart.js/auto')`) to ensure the library is only loaded in the browser.

### [SUGGESTION] `MiniChart` Label Consistency
The `MiniChart` component receives a descriptive `label` prop (e.g., "Sentiment arc across the text"), but this is used only for `aria-label` and `figcaption`. The internal Chart.js dataset `label` remains hardcoded as "Sentiment" or "MATTR" in `+page.svelte`.
**Impact**: This creates a mismatch between what screen readers hear from the `figure` tag and what is provided by the chart's internal accessibility features or potential legends.
**Suggestion**: Synchronize the dataset label with the component's `label` prop to ensure consistency across all accessibility layers.

### [SUGGESTION] Improved Error Visibility in `listAnalyses`
In `explorer/src/lib/server/data.ts`, the `listAnalyses` function silently skips any directory where `manifest.json` fails to load or parse, logging only a generic `console.warn`.
**Impact**: This makes it difficult for users to understand why a specific analysis is missing from the landing page grid.
**Suggestion**: Consider returning a "corrupt" status or including the invalid entry in the list so the UI can display a placeholder card with a "Repair needed" or "Invalid output" message, aiding in engine-to-explorer debugging.

### [PRAISE] Robust Path Traversal Protection
The `validateSlug` function in `explorer/src/lib/server/data.ts` implements a multi-layered "defense-in-depth" approach. By combining a strict alphanumeric regex allowlist with an absolute path resolution check (`candidate.startsWith(base + sep)`), it effectively prevents any directory traversal attempts via the `slug` parameter.

### [PRAISE] High-Fidelity Schema Mirroring
The TypeScript interfaces in `explorer/src/lib/types/analysis.ts` are exceptionally well-crafted. They perfectly mirror the complex, multi-file JSON contract produced by the Python engine, including optional fields for enriched readability metrics and pacing data, ensuring a robust developer experience.

### [PRAISE] Idiomatic Svelte 5 Implementation
The overview page demonstrates an excellent grasp of Svelte 5 runes. The use of `$derived` for calculating averages and formatting chart data ensures that the dashboard remains reactive and performant without manual state management.
