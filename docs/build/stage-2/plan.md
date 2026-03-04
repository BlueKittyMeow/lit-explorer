# Stage 2: Agency Analyzer
## Detailed Build Plan

---

## Objective

Build the character agency analyzer: verb profiling with pronoun resolution, passive voice detection, semantic verb categorization, and character auto-detection via spaCy NER. After this stage, `lit-engine analyze manuscript.txt` produces both `analysis.json` (Stage 1) and `characters.json`.

---

## Dependencies

- **Stage 1 complete:** base `Analyzer` class, `AnalyzerResult`, registry, `config.py`, `nlp/loader.py` (lazy spaCy), JSON export
- **spaCy `en_core_web_lg`:** required at runtime for dependency parsing, NER, and lemmatization
- **No dependency on TextTiling results:** agency operates on raw text + spaCy doc independently

---

## 1. New Files

```
engine/src/lit_engine/
├── nlp/
│   ├── coref.py              ← pronoun resolution heuristics
│   └── verb_categories.py    ← semantic verb classification + lookup
├── analyzers/
│   └── agency.py             ← character verb profiling analyzer
```

Plus updates to:
- `analyzers/__init__.py` — add import for `agency` module
- `output/json_export.py` — add `write_characters()` function
- `cli.py` — add `characters.json` output routing
- `config.py` — add `--characters` and gender config support

---

## 2. `nlp/verb_categories.py`

Extract the verb category dictionaries from `specimen_analysis_v2.py` lines 340–369 into a standalone module.

```python
"""Semantic verb classification for literary prose."""

VERB_CATEGORIES: dict[str, set[str]] = {
    "perception": {"watch", "see", "look", "observe", "notice", "gaze", "stare",
                   "glance", "glimpse", "peer", "regard", "eye", "view", "spot",
                   "hear", "listen", "smell", "taste", "sense", "perceive", "detect"},
    "cognition":  {"think", "know", "believe", "wonder", "realize", "understand",
                   "consider", "imagine", "remember", "forget", "suspect", "recognize",
                   "suppose", "decide", "reason", "ponder", "reflect", "muse",
                   "contemplate", "reckon", "doubt", "assume", "recall", "hope"},
    "emotion":    {"feel", "want", "wish", "love", "hate", "fear", "dread", "enjoy",
                   "desire", "long", "yearn", "ache", "need", "crave", "regret",
                   "mourn", "grieve", "suffer", "hurt", "envy", "resent", "admire"},
    "speech":     {"tell", "ask", "answer", "reply", "whisper", "murmur", "call",
                   "shout", "cry", "scream", "mutter", "announce", "declare",
                   "insist", "suggest", "explain", "demand", "plead", "beg",
                   "confess", "admit", "deny", "argue", "protest", "interrupt"},
    "motion":     {"walk", "run", "move", "turn", "step", "cross", "enter", "leave",
                   "approach", "follow", "lead", "rush", "hurry", "wander", "pace",
                   "climb", "descend", "rise", "fall", "sit", "stand", "lean",
                   "kneel", "stumble", "flee", "retreat", "advance", "return"},
    "physical_action": {"take", "hold", "grab", "pull", "push", "touch", "reach",
                        "open", "close", "break", "cut", "strike", "throw", "catch",
                        "lift", "drop", "place", "set", "press", "squeeze", "grip",
                        "release", "shake", "pour", "draw", "write", "tear", "lock"},
    "gesture":    {"nod", "shrug", "wave", "point", "frown", "smile", "wince",
                   "blink", "sigh", "laugh", "gasp", "tremble", "shiver", "swallow",
                   "bow", "gesture", "clench", "bite"},
    "resistance": {"resist", "refuse", "deny", "reject", "fight", "struggle",
                   "defy", "forbid", "prevent", "stop", "block", "withdraw",
                   "avoid", "ignore", "suppress", "repress", "restrain"},
}


def build_verb_lookup() -> dict[str, str]:
    """Build inverted lookup: verb lemma → category name."""
    lookup = {}
    for category, verbs in VERB_CATEGORIES.items():
        for verb in verbs:
            lookup[verb] = category
    return lookup


def categorize_verb(verb_lemma: str, lookup: dict[str, str] | None = None) -> str:
    """Return the semantic category for a verb lemma, or 'other'."""
    if lookup is None:
        lookup = build_verb_lookup()
    return lookup.get(verb_lemma, "other")
```

**Preserved exactly** from `specimen_analysis_v2.py` lines 340–375. No verbs added or removed.

**Note on `deny`:** appears in both `speech` and `resistance` in the existing code. In the inverted lookup, the last write wins. We should pick one. `deny` is more commonly resistance in literary context — assign to `resistance`, remove from `speech`. (The original code has this same shadowing bug.)

---

## 3. `nlp/coref.py`

Pronoun resolution heuristics. Refactored from `resolve_pronouns_simple()` at `specimen_analysis_v2.py` lines 261–301.

```python
"""Heuristic pronoun resolution for literary prose."""

import spacy


MALE_PRONOUNS = frozenset({"he", "him", "his", "himself"})
FEMALE_PRONOUNS = frozenset({"she", "her", "hers", "herself"})


def resolve_pronouns(
    doc: spacy.tokens.Doc,
    characters: dict[str, str],
    skip_ambiguous: bool = True,
) -> dict[int, str]:
    """
    Simple pronoun resolution for literary prose with a small cast.

    Strategy:
    1. Track most recent named character mention per gender per sentence.
    2. For he/him/his → assign to most recent male character.
    3. For she/her/hers → assign to most recent female character.
    4. If skip_ambiguous=True and both male characters are named in the
       same sentence, skip pronoun resolution for that sentence (ambiguous).

    Args:
        doc: spaCy Doc of the full manuscript.
        characters: dict mapping character name (lowercase) → gender
                    e.g. {"emil": "male", "felix": "male"}
        skip_ambiguous: if True, skip pronoun resolution in sentences
                        where multiple characters of the same gender appear.

    Returns:
        dict mapping token index → resolved character name (lowercase).
    """
    resolved: dict[int, str] = {}
    last_male: str | None = None
    last_female: str | None = None

    for sent in doc.sents:
        # Track which characters of each gender appear in this sentence
        males_in_sent: set[str] = set()
        females_in_sent: set[str] = set()

        # First pass: find named character mentions
        for token in sent:
            name = token.text.lower()
            if name in characters:
                gender = characters[name]
                if gender == "male":
                    last_male = name
                    males_in_sent.add(name)
                else:
                    last_female = name
                    females_in_sent.add(name)

        # Determine if this sentence is ambiguous
        male_ambiguous = skip_ambiguous and len(males_in_sent) > 1
        female_ambiguous = skip_ambiguous and len(females_in_sent) > 1

        # Second pass: resolve pronouns
        for token in sent:
            lower = token.text.lower()
            if lower in MALE_PRONOUNS and last_male and not male_ambiguous:
                resolved[token.i] = last_male
            elif lower in FEMALE_PRONOUNS and last_female and not female_ambiguous:
                resolved[token.i] = last_female

    return resolved
```

**Changes from existing code:**
| Existing | New | Why |
|----------|-----|-----|
| Hardcoded `{'emil': 'male', 'felix': 'male'}` | Accepts `characters` dict parameter | Supports any manuscript, not just The Specimen |
| No ambiguity detection | `skip_ambiguous` parameter | Spec requirement #4: skip resolution when both male characters named |
| Returns `dict` keyed by token index | Same | Clean interface for agency analyzer |

---

## 4. Character Auto-Detection

When `--characters` is not provided, detect characters via spaCy NER.

This lives in the agency analyzer itself (not a separate module), since it requires a spaCy Doc:

```python
def auto_detect_characters(
    doc: spacy.tokens.Doc,
    min_mentions: int = 10,
    max_characters: int = 8,
) -> list[str]:
    """
    Detect likely character names from spaCy NER PERSON entities.

    Returns list of character names (lowercase), sorted by frequency.
    """
    from collections import Counter

    person_counts: Counter[str] = Counter()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Normalize: lowercase, strip titles, use first name only
            name = ent.text.lower().strip()
            # Take first token as canonical name (handles "Felix von Braun" → "felix")
            first_name = name.split()[0] if name else name
            person_counts[first_name] += 1

    # Filter by minimum mentions, cap at max
    candidates = [
        name for name, count in person_counts.most_common()
        if count >= min_mentions
    ]
    return candidates[:max_characters]
```

**Gender inference:** Auto-detected characters need gender for pronoun resolution. Strategy:
1. For each detected name, check the pronouns that co-occur with it in nearby sentences
2. If 70%+ of nearby pronouns are he/him → male; she/her → female
3. If uncertain → "unknown" (skip pronoun resolution for this character)

```python
def infer_gender(
    doc: spacy.tokens.Doc,
    character_name: str,
) -> str:
    """
    Infer likely gender of a character by examining co-occurring pronouns.

    Returns "male", "female", or "unknown".
    """
    male_count = 0
    female_count = 0

    for sent in doc.sents:
        has_name = any(
            token.text.lower() == character_name for token in sent
        )
        if not has_name:
            continue

        for token in sent:
            lower = token.text.lower()
            if lower in MALE_PRONOUNS:
                male_count += 1
            elif lower in FEMALE_PRONOUNS:
                female_count += 1

    total = male_count + female_count
    if total < 3:
        return "unknown"
    if male_count / total >= 0.7:
        return "male"
    if female_count / total >= 0.7:
        return "female"
    return "unknown"
```

---

## 5. `analyzers/agency.py`

The main analyzer. Refactored from `extract_character_agency_v2()`.

### Core algorithm (preserved from existing code):

1. Parse text with spaCy (via `nlp/loader.py`)
2. Auto-detect characters (or use `config["characters"]`)
3. Resolve pronouns (via `nlp/coref.py`)
4. Walk every token in the doc:
   - If `dep_ == "nsubj"` and head is VERB → active voice
     - Match token to character (by name or pronoun resolution)
     - Record verb lemma, categorize it, find direct object
   - If `dep_ == "nsubjpass"` and head is VERB → passive voice
     - Record verb, find agent ("by" phrase)
5. Aggregate into `characters.json` schema

### Output schema match:

For each character, produce:
```json
{
  "total_verbs": 744,
  "active_count": 722,
  "passive_count": 22,
  "intransitive_count": 392,
  "via_name": 277,
  "via_pronoun": 620,
  "verb_domains": { "perception": 82, ... },
  "top_verbs": [{"verb": "see", "count": 34, "category": "perception"}, ...],
  "top_actions": [{"action": "shake -> head", "count": 5}, ...],
  "passive_verbs": [{"verb": "make", "count": 2}, ...],
  "passive_agents": [{"agent": "crematory", "count": 1}]
}
```

### Changes from existing code:

| Existing | New | Why |
|----------|-----|-----|
| Reads file directly | Receives `text` via `analyze()` interface | Consistent analyzer pattern |
| Loads spaCy inline | Uses `nlp/loader.py` (cached) | Single load across all analyzers |
| Hardcoded `target_chars = {'emil', 'felix'}` | Uses `config["characters"]` or auto-detection | Any manuscript |
| Verb categories inline | Uses `nlp/verb_categories.py` | Shared module, testable |
| Pronoun resolution inline | Uses `nlp/coref.py` | Shared module, testable |
| Generates charts | Dropped | Explorer handles visualization |
| Returns raw defaultdict | Returns `AnalyzerResult` with schema-matching data | Consistent interface |
| `top_verbs` as Counter | `top_verbs` as list of `{verb, count, category}` dicts | Matches JSON schema |
| `top_actions` as Counter | `top_actions` as list of `{action, count}` dicts | Matches JSON schema |

### Integration with CLI:

The CLI needs to:
1. Route `characters.json` output (like it does `analysis.json`)
2. Pass `--characters emil,felix` → `config["characters"]`
3. Store detected character list in `manifest.json`

---

## 6. Config Updates

Add to `config.py`:

```python
# Characters (existing, expand)
"characters": [],              # empty = auto-detect
"character_genders": {},       # e.g. {"emil": "male", "felix": "male"}
"max_auto_characters": 8,
"min_character_mentions": 10,
"coref_enabled": True,
"coref_method": "heuristic",   # for manifest.json
```

These are mostly already there from Stage 1 scaffolding. Add `coref_method`.

---

## 7. CLI Updates

Add `--characters` option to the `analyze` command:

```python
@click.option("--characters", default=None, help="Comma-separated character names")
```

When provided, parse into `config["characters"]`. The agency analyzer checks this and skips auto-detection if characters are specified.

Add routing for `characters.json` in the output section:

```python
if "agency" in results:
    path = write_characters(output, results["agency"].data)
    click.echo(f"  {path}")
```

Update manifest with detected/specified character list.

---

## 8. Test Plan

### `engine/tests/test_verb_categories.py`
```
test_all_categories_present       — VERB_CATEGORIES has all 8 expected categories
test_no_empty_categories          — every category has at least 1 verb
test_build_lookup                 — inverted lookup maps verbs to categories
test_categorize_known_verb        — "see" → "perception", "think" → "cognition"
test_categorize_unknown_verb      — "flibbertigibbet" → "other"
test_no_duplicate_verbs           — no verb appears in multiple categories
```

### `engine/tests/test_coref.py`
```
test_basic_male_resolution        — "Emil walked. He smiled." → he→emil
test_basic_female_resolution      — "Clara spoke. She laughed." → she→clara
test_most_recent_referent         — "Emil sat. Felix stood. He spoke." → he→felix
test_ambiguous_skipped            — "Emil and Felix sat. He spoke." → he unresolved
test_cross_sentence_persistence   — referent carries across sentences
test_empty_characters             — no characters → no resolutions
test_mixed_gender                 — male and female characters, correct assignment
test_unknown_gender_skipped       — pronouns for "unknown" gender not resolved
```

### `engine/tests/test_agency.py`
```
test_result_type                  — returns AnalyzerResult with name="agency"
test_output_schema                — data has "characters" key with expected structure
test_character_schema             — each character has all required fields
test_active_passive_counts        — active_count + passive_count == total_verbs
test_verb_domains_sum             — sum of verb_domains == active_count (approx, stop verbs excluded)
test_top_verbs_sorted             — top_verbs sorted by count descending
test_top_actions_format           — each action is "verb -> object" format
test_via_name_via_pronoun         — via_name + via_pronoun > 0 for detected characters
test_auto_detect_characters       — fixture text with named characters detects them
test_manual_characters            — config["characters"] overrides auto-detection
test_passive_agents_found         — passive construction "X was given by Y" → Y in passive_agents
test_registers_as_analyzer        — get_analyzer("agency") works
```

### `engine/tests/test_auto_detect.py`
```
test_detects_person_entities      — text with names → detected list
test_min_mentions_filter          — name appearing 2x with min_mentions=10 → not detected
test_max_characters_cap           — >8 names → only top 8 returned
test_first_name_normalization     — "Felix von Braun" → "felix"
test_infer_gender_male            — character with "he" pronouns → "male"
test_infer_gender_female          — character with "she" pronouns → "female"
test_infer_gender_unknown         — character with few pronouns → "unknown"
```

---

## 9. Test Fixture Updates

The existing `sample_text.txt` already has two named characters (Marguerite and Thomas) with dialogue and pronouns. It should work for basic agency tests.

For NER auto-detection tests, we may need a fixture that mentions names enough times (>10) to pass the threshold. If the current fixture is too short, we can either:
- Add a dedicated `agency_fixture.txt` with more character mentions
- Or use a `@pytest.fixture` that generates synthetic text with known characters

**Decision:** Use `conftest.py` fixtures that build synthetic spaCy docs for unit tests (fast, no file I/O). Use `sample_text.txt` for integration tests.

---

## 10. Known Risks

1. **spaCy model size and parse time.** Parsing 240k characters takes 30-60 seconds with `en_core_web_lg`. Tests should use short fixture text. The NLP loader's caching ensures the model loads only once.

2. **NER noise on literary prose.** spaCy may detect place names, titles, or partial names as PERSON entities. The `min_mentions` filter helps, but manual `--characters` is the gold standard.

3. **`nsubjpass` deprecation.** In newer spaCy models, passive subjects may use different dependency labels. Need to verify which labels `en_core_web_lg` uses for passive constructions.

4. **Pronoun resolution accuracy.** The heuristic handles the common case (clear antecedent in previous sentence) but fails on:
   - Long-distance anaphora (pronoun refers to character mentioned paragraphs ago)
   - Nested clauses where the syntactic subject changes
   - Reported speech ("Emil said that he..." — "he" could be Emil or someone else)
   The `via_name` / `via_pronoun` split lets the frontend show how much data is inferred.

5. **`deny` appears in both `speech` and `resistance` categories.** Must resolve this before implementation — pick one canonical category.

6. **Stop verbs vs category verbs overlap.** Some verbs in `stop_verbs` (e.g., `tell`, `ask`, `call`, `leave`, `take`, `set`, `find`) also appear in verb categories. The existing code checks stop verbs first and skips category assignment. Need to verify this is intentional and preserve the behavior.

---

## 11. Definition of Done

- [ ] `nlp/verb_categories.py` — all categories, inverted lookup, no duplicate verbs
- [ ] `nlp/coref.py` — pronoun resolution with ambiguity detection
- [ ] `analyzers/agency.py` — character profiling producing `characters.json` schema
- [ ] Character auto-detection via NER
- [ ] Gender inference for auto-detected characters
- [ ] `characters.json` written to output directory
- [ ] CLI `--characters` flag works
- [ ] All tests pass: `pytest engine/tests/ -v`
- [ ] `lit-engine analyze the_specimen_v2.txt --characters emil,felix` produces valid `characters.json`
- [ ] `lit-engine analyze the_specimen_v2.txt` (no `--characters`) auto-detects emil and felix
- [ ] Emil's verb profile roughly matches existing analysis (~700+ verbs, perception/cognition dominant)
