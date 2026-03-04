# Stage 3 Implementation Review — Gemini

## Instructions

You are reviewing the Stage 3 **implementation document** for **lit-explorer**, a computational stylistics toolkit. This document incorporates findings from the first plan review (yours and Codex's) and resolves all identified blockers.

**Read the following files before starting your review:**
1. `docs/build/stage-3/plan.md` — the original plan (for context on what changed)
2. `docs/build/stage-3/implementation.md` — **the document you are reviewing**
3. `spec.md` — the project specification (source of truth for schemas)
4. The existing working code (reference implementations):
   - `~/Documents/lit-analysis/directed_sentiment.py` — VADER sentiment + chapter detection
   - `~/Documents/lit-analysis/animacy_tracker.py` — chapter detection alternative
   - `~/Documents/lit-analysis/passage_analyzer.py` — dialogue ratio, readability metrics
   - `~/Documents/lit-analysis/specimen_analysis_v2.py` — readability per block, sentence lengths
5. The Stage 1+2 implementation (already built and passing 92 tests):
   - `engine/src/lit_engine/analyzers/__init__.py` — base Analyzer class, registry, `list_analyzers()`
   - `engine/src/lit_engine/analyzers/texttiling.py` — TextTiling (flesch_ease, flesch_grade, gunning_fog, sentence_lengths, mattr per block; `"chapter": None` placeholder)
   - `engine/src/lit_engine/analyzers/agency.py` — character agency (auto-detect, pronoun resolution, HONORIFICS with noble particles)
   - `engine/src/lit_engine/nlp/coref.py` — pronoun resolution heuristics
   - `engine/src/lit_engine/nlp/verb_categories.py` — semantic verb classification
   - `engine/src/lit_engine/config.py` — current DEFAULT_CONFIG
   - `engine/src/lit_engine/cli.py` — current CLI (analysis.json, characters.json, manifest.json)
   - `engine/src/lit_engine/output/json_export.py` — JSON export (build_manifest already has chapter_count param)
6. The target manuscript formatting:
   - Chapters: `Chapter N - Title` format (16 chapters, preceded by blank lines)
   - Dialogue: curly double quotes only (U+201C opening, U+201D closing)

**Your review should verify:**
- Were all blockers from the first review properly resolved (B1-B4)?
- Are the output schemas for chapters.json and sentiment.json spec-compliant?
- Is the block_to_chapter mapping approach clean and complete?
- Is the CLI enrichment pipeline (readability → chapters → pacing → write) correctly ordered?
- Is the topological sort specification correct (Kahn's algorithm, error handling)?
- Are the dialogue extraction edge cases (multi-paragraph, EOF, quote priority) fully specified?
- Is the sentiment char-range mapping for chapter averages sound?
- Are the test cases comprehensive enough to catch regressions?
- Any remaining gaps, inconsistencies, or ambiguities?

**Rules:**
- Record ALL findings below in this document
- Do NOT modify any code files — this is a review-only document
- Categorize findings as: BLOCKER, CONCERN, SUGGESTION, or PRAISE
- For each finding, cite the specific section of the implementation doc or spec
- Be specific and constructive

---

## Findings

(Gemini: record your findings here)
