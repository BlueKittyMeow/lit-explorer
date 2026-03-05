# Full Codebase Review — Gemini

## Evaluation Summary

The **lit-explorer** engine is a robust, well-architected computational stylistics toolkit. This adversarial review confirms that the core logic is sound, but identifies a few subtle risks in character mention counting and boundary heuristics that may manifest on extremely large or unusually formatted manuscripts.

---

## Findings

### 1. Correctness & Data Integrity

- 🟢 **PRAISE**: **Deterministic Offset Mapping** (`texttiling.py`). The use of an `offset_map` ensures 100% accuracy for character-level data retrieval in the frontend.
- 🟡 **CONCERN**: **Midpoint Heuristic for Block Assignment** (`chapters.py:65`). Assigning a block to a chapter based on its midpoint (`block_mid`) is generally safe, but if a very short chapter (e.g., a 1-paragraph prologue) ends exactly at a block boundary, the block might be "pulled" into the wrong chapter.
- 🟡 **CONCERN**: **Sentence Location Fallback** (`sentence_locate.py:16`). If a tokenizer normalizes whitespace heavily (e.g., converting multiple newlines to one), `text.find()` will fail and the scanner will fallback to `idx = search_from`. While safe, this could lead to slight offset "compression" if many sentences fail to match exactly.

### 2. Performance & Scalability

- 🟡 **CONCERN**: **Quadratic Mention Counting** (`chapters.py:112-115`). Inside the chapter loop, the code calls `ch_tokens.count(name)` for every character. For a manuscript with 50 chapters and 20 detected characters, this results in 1,000 full-chapter token scans. 
    - *Impact*: Negligible for *The Specimen*, but could become slow for very long novels with many minor characters.
    - *Recommendation*: Use a single `Counter(ch_tokens)` pass per chapter.
- 🟡 **CONCERN**: **Memory Footprint** (`loader.py`). The use of `en_core_web_lg` (~500MB) plus the large spaCy Doc object (~2-3x text size) remains the primary resource constraint for deployment.

### 3. Architecture & Robustness

- 🟢 **PRAISE**: **Plugin Registry** (`analyzers/__init__.py`). The topological sorting of the analyzer pipeline is excellent and handles transitive dependencies perfectly for the `rerun` command.
- 🟢 **PRAISE**: **Resilient Enrichment** (`cli.py`). The pipeline handles failed analyzers gracefully by checking for result presence before enrichment or output writing.
- 🟡 **CONCERN**: **Dialogue Scanner Nesting** (`dialogue_extract.py:68-120`). The current scanner is linear and priority-based. While it handles continued dialogue, it does not use a stack for nesting. This means `'He said, "Hello," and waved.'` works, but a more complex nesting of different quote types might lead to premature termination of the outer span.

### 4. Code Quality & Security

- 🟢 **PRAISE**: **Safe Slugification** (`json_export.py:58`). Prevents path traversal and ensures valid directory names.
- 🟢 **PRAISE**: **Refactoring Fidelity**. The implementation successfully modularizes the original logic from `specimen_analysis_v2.py` without losing the nuanced metrics Lara depends on.

---

## Conclusion

The engine is production-ready for the Explorer phase. The identified concerns are "at-scale" edge cases that do not impact the primary use case or the validation against *The Specimen*.
