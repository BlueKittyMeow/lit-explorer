# Stage 1 Review — Gemini

## Instructions

You are reviewing the Stage 1 build plan for **lit-explorer**, a computational stylistics toolkit. Your job is to act as a critical technical reviewer.

**Read the following files before starting your review:**
1. `docs/build/overview.md` — the master build plan with all stages
2. `docs/build/stage-1/plan.md` — the detailed plan you are reviewing
3. `spec.md` — the project specification (the source of truth)
4. The existing working code: `~/Documents/lit-analysis/specimen_analysis_v2.py`

**Your review should cover:**
- Correctness: Does the plan accurately reflect the spec? Any schema mismatches?
- Completeness: Is anything from the spec missing that Stage 1 should handle?
- Risks: Are the identified risks real? Are there risks not identified?
- Interface design: Is the base Analyzer class well-designed? Will it hold up for all 8 analyzers?
- Data integrity: Will the character offset mapping actually work? Propose alternatives if you see problems.
- Test coverage: Are there missing test cases? Edge cases not covered?
- Dependencies: Are the Python package versions and dependencies correct?
- Refactoring fidelity: Does the plan preserve the working algorithm from `specimen_analysis_v2.py` while properly restructuring it?

**Rules:**
- Record ALL your findings below in this document
- DO NOT modify any other files in the repository
- DO NOT write any code outside of this document
- Be specific: cite line numbers, section numbers, or quote the text you're critiquing
- Categorize findings as: 🔴 BLOCKER, 🟡 CONCERN, 🟢 SUGGESTION, ℹ️ NOTE
- If you find nothing wrong with a section, say so — silence is ambiguous

---

## Findings

### 1. Correctness & Schema Consistency

- 🟢 **SUGGESTION**: The `manifest.json` schema in `spec.md` (section "JSON Schema") includes `chapter_count`, but `plan.md` (section 6) shows `chapter_count: int = 0` as a default. For Stage 1, where the chapter analyzer hasn't run yet, this is correct, but the explorer should be prepared for `0` or `null` values.
- ℹ️ **NOTE**: `plan.md` (section 5) defines `block_num` as 1-indexed, while `spec.md` shows `id: 1` and `tile_index: 0`. This is consistent and preserves the expected behavior for both human-readable IDs and zero-indexed array access.

### 2. Completeness

- 🔴 **BLOCKER**: The `plan.md` (section 5) does not explicitly mention the **TextTiling fallback logic** present in `specimen_analysis_v2.py` (lines 80-86). The existing script falls back from `w=40, k=20` to `w=20, k=10` if tokenization fails. This is critical for shorter texts or those with unusual paragraph structures and should be part of the `TextTilingAnalyzer.analyze` implementation.
- 🟢 **SUGGESTION**: `spec.md` mentions a `pacing.py` analyzer for "Sentence length distribution". `plan.md` (section 5) includes `sentence_lengths` in the `texttiling.py` output. This is a sensible consolidation for Stage 1, but we should ensure the `analysis.json` schema in `spec.md` remains the source of truth for where this data lives.

### 3. Risks

- 🟡 **CONCERN**: **Memory usage** for the `en_core_web_lg` model. While `plan.md` (section 4) correctly handles `nlp.max_length`, a 500MB model plus a large spaCy Doc for a 300k+ character manuscript can easily exceed 1GB of RAM. We should add a "Risk" note about memory constraints for low-RAM environments (e.g., small VPS).
- 🟡 **CONCERN**: **Character Offset Mapping** (section 5). The `text.find()` approach is fragile if TextTiling or the `formatted = text.replace('\n', '\n\n')` step alters the text beyond simple whitespace normalization.
    - **Proposed alternative**: Since `TextTilingTokenizer` essentially splits on `\n\n`, we should first split the original text into paragraphs, record their offsets, and then use those offsets to reconstruct the tile boundaries. This is much more robust than fuzzy string searching.

### 4. Interface Design

- 🟢 **SUGGESTION**: The `Analyzer.analyze` method (section 2) takes `config: dict`. For better type safety and IDE support, we should consider using a `TypedDict` or a simple `Config` dataclass, though a dict is acceptable for a prototype.
- 🟢 **SUGGESTION**: `AnalyzerResult` (section 2) should include a `metadata` field to store analyzer-specific execution details (like "was fallback window used?") without cluttering the main `data` payload.

### 5. Data Integrity

- 🔴 **BLOCKER**: `plan.md` (section 5) mentions "Skip if < `min_words` or < `min_alpha` words". If blocks are skipped, the `id` and `tile_index` mapping must remain contiguous and non-overlapping for the frontend. The plan needs to ensure that "skipped" text is either merged into adjacent blocks or accounted for so that the `start_char` / `end_char` ranges don't have gaps that the "Block Explorer" might trip over.

### 6. Test Coverage

- 🟢 **SUGGESTION**: Add `test_unicode_handling` to `test_texttiling.py`. Literary prose often contains smart quotes (” “), em-dashes (—), and accented characters (é). The tokenizer and offset mapping must handle these without offset drift.
- 🟢 **SUGGESTION**: Add `test_extremely_long_sentences` to `test_mattr.py`. Some experimental prose might have a single sentence longer than the MATTR window (50 tokens). The windowing logic should handle this gracefully.

### 7. Dependencies

- ℹ️ **NOTE**: Dependencies in `pyproject.toml` and `requirements.txt` are consistent and match the needs of the existing script.
- 🟡 **CONCERN**: `nltk` data download. `plan.md` (section 10) asks if `conftest.py` should ensure NLTK data is downloaded. **Yes**, `conftest.py` should check for `punkt_tab` and `stopwords` and download them if missing to ensure a "zero-config" test run.

### 8. Refactoring Fidelity

- 🟢 **SUGGESTION**: `specimen_analysis_v2.py` (line 125) saves "notable" blocks to a summary table. `plan.md` (section 5) correctly moves this to the `notable` key in `analysis.json`. We should ensure the "top 5" logic (longest sentences, highest MATTR, etc.) is exactly preserved as Lara is used to these specific metrics.
- ℹ️ **NOTE**: The plan successfully transitions from "Chart generation in Python" to "Data export for SvelteKit", which aligns with the `spec.md` vision of the explorer handling visualization.


