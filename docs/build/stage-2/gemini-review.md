# Stage 2 Review — Gemini

## Instructions

You are reviewing the Stage 2 build plan for **lit-explorer**, a computational stylistics toolkit. Your job is to act as a critical technical reviewer.

**Read the following files before starting your review:**
1. `docs/build/overview.md` — the master build plan with all stages
2. `docs/build/stage-2/plan.md` — the detailed plan you are reviewing
3. `spec.md` — the project specification (the source of truth)
4. The existing working code: `~/Documents/lit-analysis/specimen_analysis_v2.py` (lines 260–559 are the agency code)
5. The Stage 1 implementation (already built):
   - `engine/src/lit_engine/analyzers/__init__.py` — base Analyzer class and registry
   - `engine/src/lit_engine/config.py` — current config
   - `engine/src/lit_engine/nlp/loader.py` — spaCy loader
   - `engine/src/lit_engine/cli.py` — current CLI
   - `engine/src/lit_engine/output/json_export.py` — current JSON export

**Your review should cover:**
- Correctness: Does the plan accurately match the `characters.json` schema in `spec.md`?
- Completeness: Is the refactoring from `specimen_analysis_v2.py` complete? Any logic lost?
- Interface design: Does the agency analyzer fit cleanly into the Stage 1 architecture?
- NLP concerns: Are there spaCy API issues, dependency label changes, or parsing edge cases?
- Pronoun resolution: Is the ambiguity detection sound? Any missed edge cases?
- Character auto-detection: Will NER work well enough on literary prose?
- Test coverage: Missing test cases or edge cases?
- Stop verbs vs verb categories: Is the overlap handled correctly?

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

- 🟢 **SUGGESTION**: The `characters.json` schema in `spec.md` includes `total_verbs`, `active_count`, `passive_count`, `intransitive_count`, `via_name`, and `via_pronoun` at the top level of each character object. The plan in section 5 confirms this match.
- ℹ️ **NOTE**: The plan (section 5) correctly identifies that `top_verbs` and `top_actions` should be lists of dicts rather than raw Counters, which is required for the JSON schema.

### 2. Completeness & Refactoring Fidelity

- 🔴 **BLOCKER**: The `stop_verbs` check from `specimen_analysis_v2.py` (lines 405-408) is missing an explicit implementation detail in the `AgencyAnalyzer` section (section 5). In the original script, verbs in `stop_verbs` are excluded from `active_verbs` AND `verb_categories`. The plan mentions preserving the behavior but doesn't show it in the core algorithm steps. This must be explicitly handled to avoid polluting the agency data with "be", "have", etc.
- 🔴 **BLOCKER**: The original script tracks `intransitive` count by checking if a verb has NO `dobj` children (lines 417-418). The plan (section 5) mentions this but needs to ensure that "intransitive" is mutually exclusive with "active_actions" (transitive) to keep the `active_count` logic consistent.
- 🟢 **SUGGESTION**: In `nlp/verb_categories.py` (section 2), the plan identifies the shadowing bug for the verb `deny`. The decision to assign it to `resistance` is sound, but we should also check for other overlaps (e.g., `suggest` which could be `speech` or `cognition`).

### 3. Risks & NLP Concerns

- 🟡 **CONCERN**: **Memory & Performance**. `en_core_web_lg` on a 240k character manuscript is heavy. The Stage 1 `parse_document` (section 7 of Stage 1 implementation, or `nlp/loader.py`) handles `max_length`, but Stage 2 must ensure it doesn't re-parse the text if another analyzer already did. However, since Stage 1 (TextTiling) uses NLTK, the Agency analyzer *will* be the first to trigger the spaCy parse.
- 🟡 **CONCERN**: **NER Normalization** (section 4). Taking only the `first_name` (e.g., "Felix von Braun" -> "felix") is a good heuristic for literary prose but might fail for characters known by titles or surnames (e.g., "Mrs. Dalloway" -> "mrs"). 
    - **Proposed improvement**: Keep a map of first-name -> full-name to ensure "Felix" and "Felix von Braun" are merged, but "Mrs. Dalloway" doesn't become "Mrs".
- 🟡 **CONCERN**: **Gender Inference** (section 4). The 70% threshold is a good start, but the "nearby sentences" window is undefined. 
    - **Proposed fix**: Use the same sentence + 1 sentence lookahead/lookback for co-occurrence to stay consistent with the coref heuristic.

### 4. Interface Design

- 🟢 **SUGGESTION**: `AgencyAnalyzer` should register itself in `analyzers/__init__.py` just like `TextTilingAnalyzer`.
- ℹ️ **NOTE**: The `context` parameter in `analyze()` is correctly included in the plan (section 5), allowing the agency analyzer to potentially see TextTiling blocks if needed in the future (though not required for Stage 2).

### 5. Data Integrity (Pronoun Resolution)

- 🔴 **BLOCKER**: **Ambiguity Detection**. The plan (section 3) skips resolution if `males_in_sent > 1`. However, if "Emil" is mentioned in sentence 1, and "Felix" is mentioned in sentence 2, a "He" in sentence 2 should strictly refer to "Felix". The `last_male` should be updated *as* the sentence is scanned, not just at the end of the sentence, to handle intra-sentence resolution correctly.
    - **Correction**: The plan's "First pass" (section 3) updates `last_male` inside the token loop. This is good. But the "Second pass" needs to ensure that if "Emil" appears early in a sentence and "Felix" appears later, a pronoun *between* them refers to "Emil", and a pronoun *after* Felix refers to "Felix".

### 6. Test Coverage

- 🟢 **SUGGESTION**: Add `test_passive_voice_without_agent` to `test_agency.py`. "Emil was struck." (no "by X") should still record "struck" as a passive verb for Emil even if `passive_agents` is empty.
- 🟢 **SUGGESTION**: Add `test_overlapping_names` to `test_auto_detect.py`. If a text has "Emil" and "Emily", the normalization/NER should not merge them.

### 7. Dependencies & Refactoring Fidelity

- ℹ️ **NOTE**: The move of `verb_categories` and `stop_verbs` to standalone modules/config is a significant improvement over the monolithic script.
- 🟡 **CONCERN**: The original script uses `agg` backend for matplotlib (line 21). Since the plan drops chart generation in favor of the explorer, this dependency should be removed from `pyproject.toml` unless we explicitly keep it for "Phase 3" (optional PNG export). The plan currently keeps it in `optional-dependencies`, which is correct.

