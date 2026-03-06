# Hotfix Review: Chapter 1 Detection + Longest Sentence Preview

## Scope

Two targeted fixes — one engine bug, one UX improvement — with corresponding test and frontend updates.

## Files to Review

### Engine changes
- `engine/src/lit_engine/nlp/chapter_detect.py` — Relaxed blank-line requirement for first chapter heading (frontmatter tolerance)
- `engine/src/lit_engine/analyzers/texttiling.py` — Added `longest_sentence_preview` field to block data
- `engine/tests/test_chapter_detect.py` — Updated blank-line test, added frontmatter tolerance test
- `engine/tests/test_texttiling.py` — Added `longest_sentence_preview` to required block keys

### Frontend changes
- `explorer/src/lib/types/analysis.ts` — Added `longest_sentence_preview` to Block interface
- `explorer/src/routes/[slug]/overview/+page.svelte` — Notable "longest sentences" now shows actual sentence text
- `explorer/tests/fixtures/test-analysis/analysis.json` — Added `longest_sentence_preview` to fixture blocks

## Review Criteria

1. **Correctness**: Does the chapter detection fix handle the epigraph case without introducing false positives (e.g., TOC entries)?
2. **Regression risk**: Could relaxing the blank-line rule for the first heading break any existing manuscript parsing?
3. **Data contract**: Is `longest_sentence_preview` correctly generated and consumed across the engine→JSON→frontend pipeline?
4. **Test coverage**: Are the new/updated tests sufficient?

## Severity Levels

Use these exact severity levels:
- `### [BLOCKER]` — Must fix before merge
- `### [CONCERN]` — Should fix, acceptable to defer
- `### [SUGGESTION]` — Nice to have
- `### [PRAISE]` — Good practice worth noting
