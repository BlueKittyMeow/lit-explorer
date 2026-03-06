### [BLOCKER] First-heading exception now accepts TOC entries as real chapter boundaries
In [`detect_chapters`](\`/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/nlp/chapter_detect.py:75\`), the blank-line guard is skipped for the *first matched heading anywhere*, not just true chapter starts. That admits common TOC lines like `Chapter 1 - ...` as the first chapter, which can produce wrong boundaries and duplicate chapter numbers downstream.

Concrete repro I ran returns a false TOC chapter:
`[(1, 'Dawn', ...), (1, 'Actual Start', ...)]`.

This directly conflicts with the false-positive criterion (TOC case). The new tests in [`test_chapter_detect.py`](\`/home/bluekitty/Documents/Git/lit-explorer/engine/tests/test_chapter_detect.py:86\`) cover epigraph tolerance but do not cover TOC rejection.

### [CONCERN] UI will show bad output for pre-hotfix analyses without migration/fallback
The UI now renders [`longestSentenceBlock.longest_sentence_preview`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.svelte:150\`) and the type makes it required in [`Block`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/types/analysis.ts:43\`), but data is loaded without runtime validation/migration in [`readJson`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/server/data.ts:42\`). Older `analysis.json` files lacking this field will likely render `"undefined"` in Notables.

### [SUGGESTION] Add semantic test for `longest_sentence_preview`, not just key presence
Current TextTiling coverage only verifies the key exists in block schema ([`test_texttiling.py:50`](\`/home/bluekitty/Documents/Git/lit-explorer/engine/tests/test_texttiling.py:50\`)). It does not assert that:
1. the preview corresponds to the sentence with `max_sentence_length`, and
2. truncation behavior (200 chars + ellipsis) is correct.

A focused assertion here would protect the new UX behavior from silent regressions.

### [PRAISE] Good end-to-end contract wiring for the new field
The new `longest_sentence_preview` is propagated consistently from engine output ([`texttiling.py:240`](\`/home/bluekitty/Documents/Git/lit-explorer/engine/src/lit_engine/analyzers/texttiling.py:240\`)) to backend test expectations ([`test_texttiling.py:9`](\`/home/bluekitty/Documents/Git/lit-explorer/engine/tests/test_texttiling.py:9\`)), frontend types ([`analysis.ts:43`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/src/lib/types/analysis.ts:43\`)), UI consumption ([`+page.svelte:150`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/src/routes/[slug]/overview/+page.svelte:150\`)), and fixture data ([`analysis.json:15`](\`/home/bluekitty/Documents/Git/lit-explorer/explorer/tests/fixtures/test-analysis/analysis.json:15\`)).