# Stage 2 Review — Codex

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

*(Codex: write your review findings below this line)*

### Correctness (Schema + Spec Alignment)

- 🟡 CONCERN — **`characters.json` handling for zero-activity characters is underspecified vs schema example.**  
  The spec example explicitly allows sparse entries (e.g., `"felix": {}`) (`spec.md` lines 278-279), while the Stage 2 plan says each character should produce a full metrics object (`docs/build/stage-2/plan.md` lines 283-298). This is workable either way, but you need one canonical rule now, or frontend typing will drift.

- 🟡 CONCERN — **Spec threshold says “appearing > N times”, plan code uses `>= min_mentions`.**  
  Spec wording: “appearing > N times (default 10)” (`spec.md` lines 432-433). Plan code keeps names where `count >= min_mentions` (`stage-2/plan.md` lines 213-216). Small but real behavioral mismatch; choose one.

- ℹ️ NOTE — **Core agency fields do map to `characters.json` schema.**  
  The plan’s target fields (`stage-2/plan.md` lines 283-297) are consistent with schema keys in `spec.md` lines 242-276.

### Completeness (Refactor Fidelity)

- 🟡 CONCERN — **Contradiction in verb-category migration statement.**  
  Plan says categories are “Preserved exactly” (`stage-2/plan.md` line 94) but also says to remove `deny` from `speech` (`line 96). That is a deliberate behavior change, not an exact preservation. Call it out as a controlled deviation.

- ℹ️ NOTE — **No major algorithmic loss from legacy `extract_character_agency_v2()` is evident.**  
  The planned active/passive traversal, stop-verb filtering, category assignment, direct-object extraction, and passive-agent extraction align with legacy behavior (`specimen_analysis_v2.py` lines 396-449; plan lines 268-279, 302-313).

### Interface Design (Stage 1 Compatibility)

- 🟡 CONCERN — **Manifest character list contract is not fully specified at the analyzer boundary.**  
  Stage 2 requires manifest to store detected/specified characters (`stage-2/plan.md` lines 319, 359; `spec.md` line 434), but the analyzer output contract shown only defines per-character metrics (`stage-2/plan.md` lines 283-298). If a detected character has no captured verbs, deriving `character_list` from metrics keys can drop that character. Define an explicit output field (or CLI-side canonical source) for final character list.

- ℹ️ NOTE — **Plan fits current Stage 1 architecture direction.**  
  It assumes `AnalyzerResult`, registry import wiring, and CLI routing updates (`stage-2/plan.md` lines 31-35), which matches current Stage 1 code shape (`engine/src/lit_engine/analyzers/__init__.py` lines 7-73, `engine/src/lit_engine/cli.py` lines 73-129).

### NLP Concerns

- 🟡 CONCERN — **Passive-label risk is identified but not converted into a concrete mitigation test.**  
  Risk is acknowledged (`stage-2/plan.md` lines 434-435), but test plan lacks a parser-label compatibility test (e.g., accepted passive subject labels and expected behavior). Add one to prevent silent breakage across model updates.

- ℹ️ NOTE — **`en_core_web_lg` runtime expectation is strict but consistent with project quality goals.**  
  Dependency section states lg is required (`stage-2/plan.md` line 15), and spec setup recommends downloading lg (`spec.md` line 380). This is coherent, though fallback behavior should still be documented if retained via Stage 1 loader (`engine/src/lit_engine/nlp/loader.py` lines 16-24).

### Pronoun Resolution

- 🔴 BLOCKER — **Proposed `resolve_pronouns()` pseudocode misclassifies `"unknown"` gender as female.**  
  In plan code, anything not `"male"` falls into the female branch (`stage-2/plan.md` lines 153-158). But the same plan states unknown-gender characters should be skipped for pronoun resolution (`lines 223-224`) and test plan expects that (`line 384). This is a logic bug in the proposed implementation.

- 🟡 CONCERN — **Ambiguous sentence can still overwrite global referent for later sentences.**  
  The resolver updates `last_male`/`last_female` before ambiguity gating (`stage-2/plan.md` lines 149-162). In an ambiguous sentence, pronouns are skipped there, but the final seen name can still become the carry-forward referent for the next sentence. This is a known heuristic limitation; worth documenting explicitly.

### Character Auto-Detection

- 🔴 BLOCKER — **Comment says titles are stripped, but pseudocode does not actually strip them.**  
  The code comment claims “strip titles” (`stage-2/plan.md` line 206), but implementation takes `split()[0]` (`line 209), so `"Dr. Emil"` canonicalizes to `"dr."`, not `"emil"`. This will materially hurt NER-based auto-detection quality.

- 🟡 CONCERN — **First-token normalization can collapse distinct people and aliases.**  
  Mapping every PERSON entity to first token (`stage-2/plan.md` lines 208-210) can merge unrelated names (`"John Smith"` and `"John Brown"`) and mis-handle surnames/titles. Consider stronger normalization with honorific filtering + alias merging rules.

### Test Coverage

- 🟡 CONCERN — **No explicit tests for CLI/output integration added in Stage 2 plan.**  
  Plan requires CLI `--characters`, `characters.json` routing, and manifest character updates (`stage-2/plan.md` lines 316-360), but the listed tests focus on analyzer modules (`lines 365-412). Add tests for:
  1. `lit-engine analyze --only agency` writes `characters.json`
  2. `--characters` parsing/normalization
  3. Manifest `character_list` populated correctly for manual + auto modes

- 🟢 SUGGESTION — **“Synthetic spaCy docs” decision may be brittle for dependency/NER behavior.**  
  Decision is to use synthetic docs in fixtures (`stage-2/plan.md` line 424). For parser/NER-heavy logic, include at least one integration test using a real spaCy pipeline to catch model-driven behavior regressions.

### Stop Verbs vs Verb Categories

- ℹ️ NOTE — **Risk is correctly identified and preserving legacy order is reasonable.**  
  Plan explicitly calls out overlap and existing behavior (`stage-2/plan.md` lines 444-445), which matches legacy code’s “stop-verbs first, then categorize” flow (`specimen_analysis_v2.py` lines 411-417).

- 🟢 SUGGESTION — **Lock this behavior with a targeted unit test.**  
  Add a case like `tell/ask/call` proving stop verbs do not increment `verb_domains`, so future category edits don’t silently change counts.

---

### Section Coverage Summary

- Correctness: issues found (no schema-shape blocker, but threshold/type consistency gaps).
- Completeness/refactor fidelity: mostly complete; one explicit contradiction to fix.
- Interface design: generally compatible with Stage 1, but manifest character-list contract needs tightening.
- NLP concerns: major risks identified; one needs concrete mitigation test.
- Pronoun resolution: one blocker bug + one heuristic carryover concern.
- Character auto-detection: one blocker bug + one normalization concern.
- Test coverage: module tests are strong; CLI/integration tests are missing.
- Stop verbs vs categories: approach is sound; add one explicit guard test.
