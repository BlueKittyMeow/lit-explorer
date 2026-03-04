# Stage 2: Agency Analyzer — Implementation Document

**Rev 2** — incorporates all findings from Codex review, Gemini review, verification research, and final review patches.

---

## Review Resolutions

### Blockers Fixed

| # | Source | Finding | Resolution |
|---|--------|---------|------------|
| B1 | Codex | `resolve_pronouns()` routes `"unknown"` gender into female branch | Make if/elif explicit: `if gender == "male"` / `elif gender == "female"` / else: pass. Unknown-gender characters are never tracked as referents. |
| B2 | Codex | "strip titles" comment but code takes `split()[0]`, so `"Dr. Emil"` → `"dr."` | Add `HONORIFICS` frozenset and strip before first-name extraction. Also confirmed: spaCy usually excludes titles from PERSON entity spans, so this is a safety net. |
| B3 | Gemini | Stop-verb filtering missing from section 5 algorithm steps | Made explicit in algorithm: step 4a filters stop verbs before categorization. |
| B4 | Gemini | Intransitive must be mutually exclusive with transitive | Already handled by if/else branch in original code. Documented explicitly. |

### Concerns Accepted

| # | Source | Finding | Resolution |
|---|--------|---------|------------|
| C1 | Codex | Spec says `> N times`, plan uses `>= min_mentions` | Changed to `count > min_mentions` to match spec literally. Default 10 means 11+ occurrences. |
| C2 | Codex | "Preserved exactly" contradicts removing `deny` from `speech` | Reworded: "Preserved from existing code with one controlled deviation." |
| C3 | Codex | Manifest character_list can lose zero-verb characters | Analyzer returns explicit `character_list` field. Zero-verb characters get full schema with zeroes. |
| C4 | Codex | No CLI/integration tests | Added: `--characters` parsing, `characters.json` output, manifest character_list. |
| C5 | Codex | No passive-label compatibility test | Added: test verifying `nsubjpass` in model label set. |
| C6 | Codex | First-token normalization can merge distinct people | Documented as known limitation. `--characters` is the escape hatch. |
| C7 | Gemini | "Nearby sentences" window for gender inference is vague | Clarified: same-sentence co-occurrence only. |
| C8 | Codex | Ambiguous sentence overwrites global referent | Known heuristic limitation matching original code. Documented. |
| C9 | Gemini | Memory/performance — don't re-parse | Not a concern: Stage 1 uses NLTK, agency is the first spaCy consumer. Loader caches model. |

### Suggestions Accepted

| # | Source | Finding | Resolution |
|---|--------|---------|------------|
| S1 | Codex | Lock stop-verb behavior with unit test | Added `test_stop_verbs_excluded_from_domains`. |
| S2 | Codex | At least one real-spaCy integration test | Added `test_real_spacy_smoke` (marked `@pytest.mark.slow`). |
| S3 | Gemini | `test_passive_voice_without_agent` | Added to test_agency.py. |
| S4 | Gemini | `test_overlapping_names` (Emil vs Emily) | Added to test_auto_detect.py. |
| S5 | Gemini | Check for other verb overlaps beyond `deny` | Verified: `deny` is the only cross-category duplicate. |
| S6 | Gemini | Register agency in `__init__.py` | Already planned (section 9). Confirmed. |

### Suggestions Deferred

| # | Source | Finding | Why |
|---|--------|---------|-----|
| D1 | Codex | Stronger normalization with alias merging | v2 improvement. First-name + title stripping sufficient for now. |
| D2 | Codex | Zero-activity characters: sparse `{}` vs full object | Going with full schema + zeroes. Easier for frontend TypeScript typing. |

### Key Verification Results

| Finding | Detail |
|---------|--------|
| `nsubjpass` is safe | spaCy English models use CLEAR-style labels (OntoNotes), not UD. Label confirmed in `en_core_web_lg` 3.7.x and 3.8.x meta.json. |
| `deny` is the only duplicate | Set intersection of all verb categories confirmed. |
| 6 stop-verb/category overlaps | `ask`, `call`, `tell` (speech), `take`, `set` (physical_action), `leave` (motion). These are dead entries — stop-verb check runs first. Intentional: these verbs are too common. |
| `via_name + via_pronoun ≠ total_verbs` | These count ALL active nsubj character-resolution events (including stop verbs). `total_verbs = active_count + passive_count` where `active_count` excludes stop verbs. Passive voice does not track attribution method in original code. Preserved. |
| `intransitive_count` ⊂ `active_count` | Active non-stop verbs with no dobj child. Already mutually exclusive via if/else. |
| NER on literary prose ~81% F1 | Acceptable for frequency-filtered auto-detect. Titles usually excluded from PERSON spans. |

---

## 1. File Plan

### New files
```
engine/src/lit_engine/
├── nlp/
│   ├── coref.py              ← pronoun resolution heuristics
│   └── verb_categories.py    ← semantic verb classification + lookup
├── analyzers/
│   └── agency.py             ← character verb profiling analyzer
```

### Modified files
```
engine/src/lit_engine/
├── analyzers/__init__.py     ← add agency import
├── config.py                 ← add coref_method key
├── cli.py                    ← add --characters flag, characters.json routing
├── output/json_export.py     ← add write_characters()
```

### New test files
```
engine/tests/
├── test_verb_categories.py
├── test_coref.py
├── test_agency.py
├── test_auto_detect.py
```

---

## 2. `nlp/verb_categories.py`

Extracted from `specimen_analysis_v2.py` lines 340–375.

### `VERB_CATEGORIES: dict[str, set[str]]`

All 8 categories preserved from existing code:
- `perception` (21 verbs)
- `cognition` (24 verbs)
- `emotion` (22 verbs)
- `speech` (24 verbs — `deny` REMOVED, controlled deviation)
- `motion` (28 verbs)
- `physical_action` (28 verbs)
- `gesture` (18 verbs)
- `resistance` (17 verbs — `deny` stays here)

**Controlled deviation from existing code:** `deny` removed from `speech`, kept in `resistance` only. The original code has `deny` in both sets; in the inverted lookup the last category to contain a verb overwrites earlier entries (`resistance` comes after `speech` in insertion order, so `deny` silently maps to `resistance` anyway in Python 3.7+). We make this explicit by removing the duplicate.

### `build_verb_lookup() -> dict[str, str]`

Inverted lookup: verb lemma → category name. Built from `VERB_CATEGORIES`. No verb appears in multiple categories after the `deny` fix.

### `categorize_verb(verb_lemma: str, lookup: dict[str, str] | None = None) -> str`

Returns the semantic category for a verb lemma, or `"other"`.

---

## 3. `nlp/coref.py`

Refactored from `resolve_pronouns_simple()` at `specimen_analysis_v2.py` lines 261–301.

### Constants

```python
MALE_PRONOUNS = frozenset({"he", "him", "his", "himself"})
FEMALE_PRONOUNS = frozenset({"she", "her", "hers", "herself"})
```

### `resolve_pronouns(doc, characters, skip_ambiguous=True) -> dict[int, str]`

**Algorithm (two-pass per sentence, matching existing code):**

1. For each sentence in `doc.sents`:
   - **First pass** — scan tokens for named character mentions:
     - If `token.text.lower()` is in `characters` dict:
       - If gender is `"male"` → update `last_male`, add to `males_in_sent`
       - Elif gender is `"female"` → update `last_female`, add to `females_in_sent`
       - Else (gender is `"unknown"`) → **skip, do not track as referent** [FIX B1]
   - Compute ambiguity flags:
     - `male_ambiguous = skip_ambiguous and len(males_in_sent) > 1`
     - `female_ambiguous = skip_ambiguous and len(females_in_sent) > 1`
   - **Second pass** — resolve pronouns:
     - If token is male pronoun and `last_male` exists and not `male_ambiguous` → resolve
     - If token is female pronoun and `last_female` exists and not `female_ambiguous` → resolve

2. Return `dict[int, str]` mapping token index → resolved character name (lowercase).

**Heuristic limitations (documented, not fixed):**
- `last_male`/`last_female` carry across sentence boundaries (intentional — matches original code)
- In ambiguous sentences, the last name from the first pass still updates the global referent for future sentences
- Intra-sentence pronoun position relative to multiple names is not handled (pronouns always resolve to last name from first pass)
- Long-distance anaphora, nested clauses, reported speech are not handled

---

## 4. Character Auto-Detection

Lives in `analyzers/agency.py` (requires spaCy Doc).

### Constants

```python
HONORIFICS = frozenset({
    "mr", "mrs", "ms", "miss", "dr", "sir", "lord", "lady",
    "professor", "prof", "father", "mother", "brother", "sister",
    "captain", "colonel", "general", "sergeant", "reverend", "rev",
    "king", "queen", "prince", "princess", "count", "countess",
    "baron", "baroness", "duke", "duchess", "saint", "st",
})
```

### `auto_detect_characters(doc, min_mentions=10, max_characters=8) -> list[str]`

```
1. For each entity in doc.ents where ent.label_ == "PERSON":
   a. Normalize: lowercase, strip whitespace
   b. Tokenize by whitespace
   c. Strip trailing punctuation from each token (`.rstrip(".")`) before comparison  [FIX: final review punctuation concern]
   d. Strip leading tokens that are in HONORIFICS (handles "Dr. Emil" → "Emil")  [FIX B2]
   e. Take first remaining token as canonical name (handles "Felix von Braun" → "felix")
   e. Increment person_counts[canonical_name]
2. Filter: keep names where count > min_mentions  [FIX C1: strictly greater than]
3. Sort by frequency descending
4. Cap at max_characters
5. Return list of canonical names
```

**Known limitation (C6):** First-token normalization can merge distinct people ("John Smith" and "John Brown" → both "john"). The `--characters` manual override is the escape hatch.

### `infer_gender(doc, character_name) -> str`

```
1. For each sentence in doc.sents:
   a. Check if character_name appears as any token (case-insensitive)
   b. If yes: count male and female pronouns in THAT SENTENCE ONLY [FIX C7]
2. If total pronoun count < 3: return "unknown"
3. If male_count / total >= 0.7: return "male"
4. If female_count / total >= 0.7: return "female"
5. Else: return "unknown"
```

---

## 5. `analyzers/agency.py` — Core Algorithm

### `AgencyAnalyzer(Analyzer)`

- `name = "agency"`
- `description = "Character verb profiling with pronoun resolution"`
- `requires() -> []` (no dependency on texttiling)

### `analyze(text, config, context=None) -> AnalyzerResult`

```
1. Parse text with spaCy via parse_document(text, config["spacy_model"])

2. Resolve character list:
   a. If config["characters"] is non-empty → use those
   b. Else → auto_detect_characters(doc, config["min_character_mentions"], config["max_auto_characters"])

3. Resolve character genders:
   a. If config["character_genders"] has entries → use those
   b. For any character without a gender entry → infer_gender(doc, name)

4. Build characters dict: {name: gender} for all characters

5. Run pronoun resolution:
   a. If config["coref_enabled"] → resolve_pronouns(doc, characters_with_genders)
   b. Else → empty dict

6. Build verb lookup from verb_categories.build_verb_lookup()
   Load stop_verbs from config["stop_verbs"]

7. Initialize per-character accumulators:
   - active_verbs: list[str]
   - active_actions: list[str]   (format: "verb -> object")
   - passive_verbs: list[str]
   - passive_agents: list[str]
   - intransitive: int = 0
   - verb_categories: Counter
   - via_name: int = 0
   - via_pronoun: int = 0

8. Walk every token in doc:

   IF token.dep_ == "nsubj" AND token.head.pos_ == "VERB":
     a. Try to resolve to a character:
        - If token.text.lower() in character names → resolved_name, increment via_name
        - Elif token.i in pronoun_map → resolved_name, increment via_pronoun
     b. If resolved_name found:
        - verb = token.head.lemma_.lower()
        - IF verb NOT in stop_verbs:                    [FIX B3: explicit stop-verb gate]
          - Append verb to active_verbs
          - Categorize: cat = verb_lookup.get(verb, "other")
          - Increment verb_categories[cat]
          - Find dobj children of token.head:
            - IF dobj found → append "verb -> dobj_lemma" to active_actions
            - ELSE → increment intransitive                [B4: mutually exclusive by if/else]

   ELIF token.dep_ == "nsubjpass" AND token.head.pos_ == "VERB":
     a. Try to resolve to a character (same name/pronoun logic)
        NOTE: via_name/via_pronoun NOT incremented for passive voice
              (matches original code — passive attribution is not tracked)
     b. If resolved_name found:
        - verb = token.head.lemma_.lower()
        - Append verb to passive_verbs (no stop-verb filter for passive)
        - Find agent phrase:
          - For each child of token.head where child.dep_ == "agent":
            - For each grandchild where grandchild.dep_ == "pobj":
              - Append grandchild.lemma_.lower() to passive_agents

9. Aggregate into output schema for each character:
```

### Output schema

For each character:
```json
{
  "total_verbs": "<active_count + passive_count>",
  "active_count": "<len(active_verbs)>",
  "passive_count": "<len(passive_verbs)>",
  "intransitive_count": "<intransitive counter>",
  "via_name": "<via_name counter (active voice only, includes stop verbs)>",
  "via_pronoun": "<via_pronoun counter (active voice only, includes stop verbs)>",
  "verb_domains": {"perception": N, "cognition": N, ...},
  "top_verbs": [{"verb": "see", "count": 34, "category": "perception"}, ...],
  "top_actions": [{"action": "shake -> head", "count": 5}, ...],
  "passive_verbs": [{"verb": "make", "count": 2}, ...],
  "passive_agents": [{"agent": "crematory", "count": 1}]
}
```

**Counting invariants:**
- `total_verbs = active_count + passive_count`
- `intransitive_count` ⊂ `active_count` (active verbs with no dobj)
- `active_count` = non-stop active verbs (the verbs that get categorized)
- `via_name + via_pronoun` ≠ `total_verbs` — these count ALL active nsubj resolution events including stop verbs, and exclude passive voice
- `sum(verb_domains.values()) = active_count` (every non-stop active verb gets a category, including "other")
- `top_verbs`: top 20 by count, descending. Built from Counter over `active_verbs`.
- `top_actions`: top 20 by count, descending. Built from Counter over `active_actions`.
- `passive_verbs`: all unique passive verbs with counts, descending.
- `passive_agents`: all unique passive agents with counts, descending.

**Zero-verb characters [C3]:** Characters in the character list with zero captured verbs get the full schema with all fields set to 0 / empty lists / empty dicts. Not `{}`.

### AnalyzerResult structure

```python
AnalyzerResult(
    analyzer_name="agency",
    data={
        "characters": { ... per-character data ... },
        "character_list": ["emil", "felix"],  # [C3] explicit list, never derived from metrics keys
        "detection_method": "auto" | "manual",
        "coref_method": "heuristic" | "disabled",
    },
    warnings=[...]
)
```

The `character_list` field is the canonical source for `manifest.json`. It includes all characters regardless of verb count.

### File output vs internal data [FIX: final review schema drift]

The AnalyzerResult `.data` dict carries metadata (`character_list`, `detection_method`, `coref_method`) for internal use by the CLI. However, `characters.json` on disk must match the spec schema: `{"characters": {...}}` only.

The CLI extracts the `"characters"` key for file output and routes metadata to `manifest.json`:

```python
# Write characters.json — spec-compliant, characters dict only
write_characters(output, {"characters": results["agency"].data["characters"]})

# Route metadata to manifest
character_list = results["agency"].data.get("character_list", [])
detection_method = results["agency"].data.get("detection_method", "auto")
coref_method = results["agency"].data.get("coref_method", "heuristic")
```

---

## 6. Config Updates

Add to `config.py` `DEFAULT_CONFIG`:

```python
"coref_method": "heuristic",   # for manifest tracking
```

All other Stage 2 keys already scaffolded in Stage 1:
- `coref_enabled`: True
- `characters`: []
- `character_genders`: {}
- `max_auto_characters`: 8
- `min_character_mentions`: 10
- `stop_verbs`: frozenset({...})

---

## 7. `output/json_export.py` Update

Add one function:

### `write_characters(output_dir: str, data: dict) -> str`

```python
def write_characters(output_dir: str, data: dict) -> str:
    """Write characters.json."""
    return write_json(output_dir, "characters.json", data)
```

Follows same pattern as `write_analysis()`.

---

## 8. CLI Updates

### New option on `analyze` command

```python
@click.option("--characters", default=None, help="Comma-separated character names (e.g., emil,felix)")
```

When provided:
- Parse: `[name for name in (n.strip().lower() for n in characters.split(",")) if name]`
- Dedupe while preserving order: `list(dict.fromkeys(parsed_list))`  [FIX: final review sanitization]
- Set `config["characters"] = parsed_list`

### Output routing

After the texttiling output block, add:

```python
if "agency" in results:
    # Write only the spec-compliant characters dict, not internal metadata
    characters_payload = {"characters": results["agency"].data["characters"]}
    path = write_characters(output, characters_payload)
    click.echo(f"  {path}")
```

### Manifest update

Replace `character_list=config["characters"]` with:

```python
# Use agency-detected character list if available, else config
if "agency" in results:
    character_list = results["agency"].data.get("character_list", [])
else:
    character_list = config["characters"]
```

### Registry import

In `analyzers/__init__.py`, add at the bottom:

```python
from lit_engine.analyzers import agency  # noqa: F401, E402
```

---

## 9. Test Plan

### `test_verb_categories.py` (7 tests)

```
test_all_categories_present       — VERB_CATEGORIES has exactly 8 keys
test_no_empty_categories          — every category set is non-empty
test_build_lookup_coverage        — inverted lookup has entry for every verb in every category
test_no_duplicate_verbs           — no verb appears in more than one category
test_categorize_known_verbs       — "see" → "perception", "think" → "cognition", "deny" → "resistance"
test_categorize_unknown_verb      — "flibbertigibbet" → "other"
test_deny_not_in_speech           — "deny" only in "resistance", not in "speech" [C2 controlled deviation]
```

### `test_coref.py` (8 tests)

Uses synthetic spaCy Docs built via `nlp.make_doc()` + manual sentence boundaries, or short real parses.

```
test_basic_male_resolution        — "Emil walked. He smiled." → he→emil
test_basic_female_resolution      — "Clara spoke. She laughed." → she→clara
test_most_recent_referent         — "Emil sat. Felix stood. He spoke." → he→felix
test_ambiguous_skipped            — Two males in same sentence → male pronouns unresolved
test_cross_sentence_persistence   — Referent carries from sentence 1 to sentence 3
test_empty_characters             — No characters → empty dict
test_mixed_gender                 — Male and female characters, correct assignment
test_unknown_gender_skipped       — Character with gender "unknown" → never used as referent [B1]
```

### `test_agency.py` (14 tests)

```
test_result_type                  — Returns AnalyzerResult with name="agency"
test_output_schema                — data has "characters" and "character_list" keys
test_character_schema             — Each character has all required fields (total_verbs, active_count, etc.)
test_active_passive_sum           — active_count + passive_count == total_verbs
test_verb_domains_sum             — sum(verb_domains.values()) == active_count
test_top_verbs_sorted             — top_verbs sorted by count descending
test_top_actions_format           — Each action contains " -> "
test_via_name_via_pronoun         — via_name + via_pronoun > 0 for detected characters
test_manual_characters            — config["characters"] overrides auto-detection
test_passive_agents_found         — "X was given by Y" → Y in passive_agents
test_passive_without_agent        — "X was struck." → passive verb recorded, no agent [S3]
test_stop_verbs_excluded          — tell/ask/call increment via_name but NOT verb_domains [S1]
test_zero_verb_character          — Character in list with no verbs → full schema with zeroes [C3]
test_registers_as_analyzer        — get_analyzer("agency") works
```

### `test_auto_detect.py` (8 tests)

```
test_detects_person_entities      — Text with names → detected list
test_min_mentions_filter          — Name appearing 5x with min_mentions=10 → not detected (> not >=) [C1]
test_max_characters_cap           — >8 names → only top 8 returned
test_first_name_normalization     — "Felix von Braun" → "felix"
test_title_stripping              — "Dr. Watson" → "watson", not "dr." [B2]
test_overlapping_names            — "Emil" and "Emily" stay separate [S4]
test_infer_gender_male            — Character co-occurring with "he" → "male"
test_infer_gender_female          — Character co-occurring with "she" → "female"
test_infer_gender_unknown         — Character with few pronouns → "unknown"
```

### `test_cli_agency.py` (4 tests)

```
test_characters_flag_parsed       — --characters "emil,felix" → config list
test_characters_json_written      — analyze with agency → characters.json exists
test_manifest_character_list      — manifest.json character_list populated
test_passive_label_compatibility  — en_core_web_lg parser labels include nsubjpass [C5]
```

### Integration test (1 test, marked slow)

```
test_real_spacy_smoke             — Parse a short literary paragraph with real en_core_web_lg,
                                    verify at least one verb attributed to a character [S2]
```

**Total: 42 tests**

---

## 10. Test Fixture Strategy

- **Unit tests (verb_categories, coref, most of agency, auto_detect):** Use `conftest.py` fixtures that build synthetic spaCy Docs. Fast, no disk I/O, deterministic.
- **Integration tests (cli_agency, real_spacy_smoke):** Use existing `sample_text.txt` fixture (Marguerite and Thomas, ~1016 words).
- **Auto-detect threshold tests:** The existing fixture may not have enough character mentions (>10) for threshold testing. Use a `@pytest.fixture` that generates synthetic text with known name counts.

---

## 11. Implementation Order

1. `nlp/verb_categories.py` + `test_verb_categories.py` — standalone, no dependencies
2. `nlp/coref.py` + `test_coref.py` — depends on spaCy only
3. `output/json_export.py` update — add `write_characters()` (trivial)
4. `config.py` update — add `coref_method` key
5. `analyzers/agency.py` (auto-detect + agency) + `test_auto_detect.py` + `test_agency.py`
6. `analyzers/__init__.py` — add agency import
7. `cli.py` updates + `test_cli_agency.py`
8. End-to-end validation against The Specimen v2

---

## 12. Definition of Done

- [ ] `nlp/verb_categories.py` — all categories, no duplicate verbs, `deny` only in `resistance`
- [ ] `nlp/coref.py` — pronoun resolution with ambiguity detection, unknown gender skipped
- [ ] `analyzers/agency.py` — character profiling producing `characters.json` schema
- [ ] Character auto-detection via NER with title stripping
- [ ] Gender inference for auto-detected characters (same-sentence co-occurrence)
- [ ] `characters.json` written to output directory
- [ ] `character_list` in AnalyzerResult data, propagated to manifest
- [ ] CLI `--characters` flag works
- [ ] All tests pass: `pytest engine/tests/ -v` (42 new + 44 existing = 86 total)
- [ ] `lit-engine analyze the_specimen_v2.txt --characters emil,felix` produces valid `characters.json`
- [ ] `lit-engine analyze the_specimen_v2.txt` (no `--characters`) auto-detects emil and felix
- [ ] Emil's verb profile roughly matches existing analysis (~700+ verbs, perception/cognition dominant)
- [ ] `via_name + via_pronoun` for Emil ≈ 897 (matching existing output)
- [ ] Zero-verb characters produce full schema with zeroes

---

## 13. Spec Updates (deferred to post-implementation)

These should be applied to `spec.md` after Stage 2 is validated:

1. Document that `via_name + via_pronoun ≠ total_verbs` (they count all active nsubj resolutions including stop verbs)
2. Document that `intransitive_count ⊂ active_count`
3. Clarify that `> N` means strictly greater than (11+ occurrences at default N=10)
4. Note that zero-verb characters use full schema with zeroes, not `{}`
5. Document the `deny` assignment to `resistance` (resolving the original code's shadowing bug)
