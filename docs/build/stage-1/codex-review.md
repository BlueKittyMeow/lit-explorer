# Stage 1 Review — Codex

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

*(Codex: write your review findings below this line)*

### Correctness

- 🔴 BLOCKER — **Base analyzer contract conflicts with the spec’s source-of-truth API.**  
  `spec.md` defines `Analyzer.analyze(...)-> dict` (`spec.md` lines 397-401), but Stage 1 defines `Analyzer.analyze(...)-> AnalyzerResult` (`docs/build/stage-1/plan.md` lines 97-123). This is not just stylistic: every later analyzer and orchestrator code path depends on this contract. Either the spec must be updated now, or Stage 1 should keep the return type as `dict` and surface warnings elsewhere.

- 🟡 CONCERN — **`chapter` field default is inconsistent with schema example.**  
  Stage 1 says `chapter` defaults to `null` (`plan.md` line 229), while schema example shows numeric `chapter: 0` (`spec.md` line 226). Pick one canonical type now; otherwise TS types and frontend logic will drift.

- 🟡 CONCERN — **`warnings` are introduced but have no defined persistence path.**  
  `AnalyzerResult.warnings` is introduced (`plan.md` lines 102, 126), but no schema location is defined in `manifest.json` or `analysis.json` (`spec.md` lines 175-236). Without a destination, warnings are likely dropped silently.

### Completeness

- 🟡 CONCERN — **Overview/Stage boundary inconsistency should be resolved before implementation.**  
  Overview Stage 1 says it produces coref heuristics + verb categories (`docs/build/overview.md` line 28), but Stage 2 also says those are produced there (`overview.md` lines 44-45), and Stage 1 detailed plan only includes `nlp/loader.py` (`plan.md` lines 28-30, 173-200). This creates planning ambiguity on what “Stage 1 done” means.

- 🟢 SUGGESTION — **Define slug normalization rules in Stage 1.**  
  `manifest.json` requires `slug` (`spec.md` lines 180, 303-306), but Stage 1 does not specify how it is derived/normalized (kebab-case, stripping punctuation, collision behavior). This should be explicit in Stage 1 since output pathing depends on it.

### Risks

- ℹ️ NOTE — **The listed risks in section 10 are real** (`plan.md` lines 408-417), especially offset mapping and short-text TextTiling behavior.

- 🔴 BLOCKER — **A major missing risk: NLTK `stopwords` dependency for TextTiling.**  
  Stage 1 risk list mentions `punkt_tab` only (`plan.md` line 410), but setup in spec requires both `punkt_tab` and `stopwords` (`spec.md` line 381). Fresh environments will fail with `LookupError` if `stopwords` is missing.

### Interface Design

- 🔴 BLOCKER — **Current `analyze(self, text, config)` signature is too narrow for cross-analyzer aggregation.**  
  Spec requires analyzers like `chapters`/`silence` to aggregate outputs from other analyzers (`spec.md` lines 423-425; `overview.md` line 136). The proposed signature (`plan.md` line 113) has no `context`/`artifacts` input, so downstream analyzers must re-compute or read intermediate files, both fragile. Add a third input (`context` or dependency payloads) now, before all analyzers are built on this interface.

- 🟢 SUGGESTION — **Use typed config models for stability.**  
  `config: dict` (`plan.md` lines 113, 128) keeps things simple short-term but weakens contract clarity. A typed config object (or validated dict schema) will reduce silent key mismatches as analyzers expand.

### Data Integrity (Character Offsets)

- 🔴 BLOCKER — **Current offset mapping plan is not reliable enough for “exact passage” UX.**  
  The proposed mapping (`plan.md` lines 235-249) relies on `find(clean[:50], offset)` and fallback sequential offsets; this will misalign on repeated phrases and formatting deltas. The fallback idea (`plan.md` lines 260-263) is explicitly approximate, but product UX requires precise click-through passage retrieval (`spec.md` lines 9, 497-499).

- 🟢 SUGGESTION — **Use a deterministic formatted-index → original-index map.**  
  Build `formatted_text` plus an index map while duplicating newlines, run TextTiling on `formatted_text`, then map tile spans back through the index map. This preserves exact offsets without fuzzy matching.

### Test Coverage

- 🔴 BLOCKER — **Planned `json_export` snippet contradicts planned tests.**  
  Tests expect auto-creation of output dir (`plan.md` line 400), but `write_manifest`, `write_analysis`, and `copy_manuscript` snippets do not call `os.makedirs(..., exist_ok=True)` (`plan.md` lines 278-320). Either code plan or test plan must change; currently they conflict.

- 🟡 CONCERN — **Missing tests for failure modes that are likely in real usage.**  
  Add tests for:
  1. Missing NLTK resources (`punkt_tab`, `stopwords`) and error messaging/recovery.
  2. Texts that produce 0 valid blocks after filtering (still valid schema output).
  3. Repeated opening substrings across tiles (offset collision case).
  4. Config overrides (e.g., `mattr_window`, `texttiling_w/k`) actually changing output.

### Dependencies

- ℹ️ NOTE — **No major version mismatches against the spec’s dependency list.**  
  Core versions in Stage 1 (`plan.md` lines 57-62, 78-85) align with `spec.md` dependency guidance (`spec.md` lines 369-376), and optional chart deps are sensibly isolated.

- 🟢 SUGGESTION — **Avoid legacy setuptools backend unless required.**  
  `setuptools.backends._legacy:_Backend` (`plan.md` line 49) is usually unnecessary now. Prefer `setuptools.build_meta` for cleaner modern packaging behavior.

### Refactoring Fidelity

- ℹ️ NOTE — **Core TextTiling/MATTR/readability flow is largely preserved.**  
  Stage 1 keeps the main logic from `analyze_psychology()` (newline formatting, TextTiling fallback, word/sentence filtering, MATTR, readability) from `specimen_analysis_v2.py` lines 80-120.

- 🟡 CONCERN — **Define “longest_sentences” metric precisely to avoid silent behavioral drift.**  
  Legacy script ranks by average sentence length (`specimen_analysis_v2.py` lines 151-156), while schema label says `longest_sentences` (`spec.md` line 230), which could be interpreted as max sentence length. Lock this definition now and test it directly.

---

### Section Coverage Summary

- Correctness: issues found (see above).
- Completeness: issues found (see above).
- Risks: issues found (including one missing blocker risk).
- Interface design: issues found (including one blocker).
- Data integrity: issues found (including one blocker).
- Test coverage: issues found (including one blocker).
- Dependencies: no blocker-level version mismatch found.
- Refactoring fidelity: mostly faithful, with one semantic ambiguity to resolve.
