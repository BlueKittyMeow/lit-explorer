# Stage 5 Plan Review (Round 2) — Gemini

## Findings

### Blockers

- 🔴 **BLOCKER**: **`BlockMetrics` interface missing enriched fields** (Section 2).
  The CLI enrichment pipeline (`cli.py:134-141`) adds `coleman_liau`, `smog`, and `ari` to every block's metrics. These are missing from the `BlockMetrics` interface.
  - **Fix**: Add `coleman_liau: number; smog: number; ari: number;` to the `BlockMetrics` interface.
- 🔴 **BLOCKER**: **`Analysis` interface missing `pacing` field** (Section 2).
  The CLI merges the results of the pacing analyzer into the `texttiling` data (`cli.py:148`). This data is written to `analysis.json` but is missing from the `Analysis` TS interface.
  - **Fix**: Add a `pacing: PacingData;` field to the `Analysis` interface and define the `PacingData` interface (matching the schema in Stage 3 plan).

### Concerns

- 🟡 **CONCERN**: **`ChapterSentiment` vs `SentimentPoint` field consistency** (Section 2).
  The `ChapterSentiment` interface correctly includes `neu: number`, matching the `ChaptersAnalyzer` output. The `SentimentPoint` interface also includes it now. However, `SentimentPoint` in `sentiment.py` uses `pos`, `neg`, `neu` while the plan v1 sometimes used full names. The current plan correctly uses the short names, but double-checking that the Svelte components use the short names is vital for data binding.
- 🟡 **CONCERN**: **Slug Regex and Unicode** (Section 3).
  The strict allowlist regex `/^[a-z0-9][a-z0-9_-]*$/` is excellent for security, but ensure the `slugify` function in the Python engine (`json_export.py:58`) always produces slugs that pass this regex, especially when handling accented characters like "Café". The Python engine currently strips non-alphanumeric characters *after* lowercase conversion, which should be fine, but worth verifying in tests.

### Suggestions

- 🟢 **SUGGESTION**: **Optional chaining for `Block.chapter`** (Section 7).
  While the `Block` interface now correctly allows `null` for `chapter`, the `overview` page should use optional chaining or a null check when rendering chapter-related block info to avoid "null" appearing in the UI for incomplete analyses.

### Praise

- 🟢 **PRAISE**: **Robust Path Security** (Section 3).
  The combination of a strict regex allowlist, `path.resolve()`, and prefix verification is a "defense-in-depth" approach that significantly hardens the server layer against path traversal.
- 🟢 **PRAISE**: **Comprehensive Testing Strategy** (Section 10).
  Expanding the test plan to include route loaders and component smoke tests ensures that the data flows correctly from disk all the way to the DOM, fulfilling the architectural goal of a reliable "research notebook."
- 🟢 **PRAISE**: **Accessibility Foundation** (Section 8).
  Wrapping `MiniChart` in `<figure>` with `aria-label` and `<figcaption>` is a great start for accessibility, showing that the "archival feel" doesn't come at the cost of inclusivity.
