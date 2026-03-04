"""Character agency analyzer — verb profiling with pronoun resolution."""

from collections import Counter

import spacy

from lit_engine.analyzers import Analyzer, AnalyzerResult, register
from lit_engine.nlp.coref import FEMALE_PRONOUNS, MALE_PRONOUNS, resolve_pronouns
from lit_engine.nlp.loader import parse_document
from lit_engine.nlp.verb_categories import build_verb_lookup

HONORIFICS = frozenset({
    # English
    "mr", "mrs", "ms", "miss", "dr", "sir", "lord", "lady",
    "professor", "prof", "father", "mother", "brother", "sister",
    "captain", "colonel", "general", "sergeant", "reverend", "rev",
    "king", "queen", "prince", "princess", "count", "countess",
    "baron", "baroness", "duke", "duchess", "saint", "st",
    # German
    "herr", "frau", "fräulein", "doktor",
    # French
    "monsieur", "madame", "mademoiselle",
    # Academic (German)
    "ordinarius", "extraordinarius",
    # Noble/patronymic particles (stripped like titles so "Herr von Braun" → "braun")
    "von", "van", "de", "di", "du", "del", "della", "dos", "das",
})


def auto_detect_characters(
    doc: spacy.tokens.Doc,
    min_mentions: int = 10,
    max_characters: int = 8,
) -> list[str]:
    """
    Detect likely character names from spaCy NER PERSON entities.

    Returns list of character names (lowercase), sorted by frequency.
    Uses strictly greater-than threshold (> min_mentions).
    """
    person_counts: Counter[str] = Counter()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Normalize: lowercase, strip whitespace
            name = ent.text.lower().strip()
            # Tokenize by whitespace
            tokens = name.split()
            # Strip trailing punctuation from each token before comparison
            tokens = [t.rstrip(".") for t in tokens]
            # Strip leading tokens that are honorifics
            while tokens and tokens[0] in HONORIFICS:
                tokens = tokens[1:]
            # Take first remaining token as canonical name
            if tokens:
                canonical = tokens[0]
                if canonical:
                    person_counts[canonical] += 1

    # Filter by minimum mentions (strictly greater than), cap at max
    candidates = [
        name for name, count in person_counts.most_common()
        if count > min_mentions
    ]
    return candidates[:max_characters]


def infer_gender(
    doc: spacy.tokens.Doc,
    character_name: str,
) -> str:
    """
    Infer likely gender of a character by examining co-occurring pronouns
    in the same sentence.

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


def _empty_character_data() -> dict:
    """Return a full character schema with all fields set to zero/empty."""
    return {
        "total_verbs": 0,
        "active_count": 0,
        "passive_count": 0,
        "intransitive_count": 0,
        "via_name": 0,
        "via_pronoun": 0,
        "verb_domains": {},
        "top_verbs": [],
        "top_actions": [],
        "passive_verbs": [],
        "passive_agents": [],
    }


def _build_character_output(acc: dict) -> dict:
    """Convert internal accumulators to the output schema."""
    active_count = len(acc["active_verbs"])
    passive_count = len(acc["passive_verbs"])

    # verb_domains: count by category
    verb_domains = dict(acc["verb_categories"])

    # top_verbs: top 20 by frequency with category
    verb_counter = Counter(acc["active_verbs"])
    lookup = acc["_verb_lookup"]
    top_verbs = [
        {"verb": verb, "count": count, "category": lookup.get(verb, "other")}
        for verb, count in verb_counter.most_common(20)
    ]

    # top_actions: top 20 by frequency
    action_counter = Counter(acc["active_actions"])
    top_actions = [
        {"action": action, "count": count}
        for action, count in action_counter.most_common(20)
    ]

    # passive_verbs: all unique with counts
    passive_verb_counter = Counter(acc["passive_verbs"])
    passive_verbs = [
        {"verb": verb, "count": count}
        for verb, count in passive_verb_counter.most_common()
    ]

    # passive_agents: all unique with counts
    passive_agent_counter = Counter(acc["passive_agents"])
    passive_agents = [
        {"agent": agent, "count": count}
        for agent, count in passive_agent_counter.most_common()
    ]

    return {
        "total_verbs": active_count + passive_count,
        "active_count": active_count,
        "passive_count": passive_count,
        "intransitive_count": acc["intransitive"],
        "via_name": acc["via_name"],
        "via_pronoun": acc["via_pronoun"],
        "verb_domains": verb_domains,
        "top_verbs": top_verbs,
        "top_actions": top_actions,
        "passive_verbs": passive_verbs,
        "passive_agents": passive_agents,
    }


@register
class AgencyAnalyzer(Analyzer):
    """Character verb profiling with pronoun resolution."""

    name = "agency"
    description = "Character verb profiling with pronoun resolution"

    def analyze(
        self,
        text: str,
        config: dict,
        context: dict | None = None,
    ) -> AnalyzerResult:
        warnings: list[str] = []

        # 1. Parse text with spaCy
        doc = parse_document(text, config.get("spacy_model", "en_core_web_lg"))

        # 2. Resolve character list
        character_names: list[str] = config.get("characters", [])
        if character_names:
            detection_method = "manual"
        else:
            min_mentions = config.get("min_character_mentions", 10)
            max_chars = config.get("max_auto_characters", 8)
            character_names = auto_detect_characters(doc, min_mentions, max_chars)
            detection_method = "auto"
            if not character_names:
                warnings.append("No characters detected via NER auto-detection.")

        # 3. Resolve character genders
        configured_genders: dict[str, str] = config.get("character_genders", {})
        characters_with_genders: dict[str, str] = {}
        for name in character_names:
            if name in configured_genders:
                characters_with_genders[name] = configured_genders[name]
            else:
                characters_with_genders[name] = infer_gender(doc, name)

        # 4. Run pronoun resolution
        coref_enabled = config.get("coref_enabled", True)
        if coref_enabled:
            pronoun_map = resolve_pronouns(doc, characters_with_genders)
            coref_method = "heuristic"
        else:
            pronoun_map = {}
            coref_method = "disabled"

        # 5. Build verb lookup and stop verbs
        verb_lookup = build_verb_lookup()
        stop_verbs = config.get("stop_verbs", frozenset())

        # 6. Initialize per-character accumulators
        accumulators: dict[str, dict] = {}
        for name in character_names:
            accumulators[name] = {
                "active_verbs": [],
                "active_actions": [],
                "passive_verbs": [],
                "passive_agents": [],
                "intransitive": 0,
                "verb_categories": Counter(),
                "via_name": 0,
                "via_pronoun": 0,
                "_verb_lookup": verb_lookup,
            }

        # 7. Walk every token
        target_chars = set(character_names)

        for token in doc:
            resolved_name = None

            # Active voice: character as subject
            if token.dep_ == "nsubj" and token.head.pos_ == "VERB":
                name = token.text.lower()
                if name in target_chars:
                    resolved_name = name
                    accumulators[name]["via_name"] += 1
                elif token.i in pronoun_map:
                    resolved_name = pronoun_map[token.i]
                    if resolved_name in accumulators:
                        accumulators[resolved_name]["via_pronoun"] += 1
                    else:
                        resolved_name = None

                if resolved_name:
                    verb = token.head.lemma_.lower()
                    if verb not in stop_verbs:
                        acc = accumulators[resolved_name]
                        acc["active_verbs"].append(verb)

                        # Categorize
                        cat = verb_lookup.get(verb, "other")
                        acc["verb_categories"][cat] += 1

                        # Find direct object
                        dobjs = [
                            child.lemma_.lower()
                            for child in token.head.children
                            if child.dep_ == "dobj"
                        ]
                        if dobjs:
                            acc["active_actions"].append(f"{verb} -> {dobjs[0]}")
                        else:
                            acc["intransitive"] += 1

            # Passive voice: character as passive subject
            elif token.dep_ == "nsubjpass" and token.head.pos_ == "VERB":
                name = token.text.lower()
                if name in target_chars:
                    resolved_name = name
                elif token.i in pronoun_map:
                    resolved_name = pronoun_map[token.i]
                    if resolved_name not in accumulators:
                        resolved_name = None

                if resolved_name:
                    verb = token.head.lemma_.lower()
                    accumulators[resolved_name]["passive_verbs"].append(verb)

                    # Find agent ("by" phrase)
                    for child in token.head.children:
                        if child.dep_ == "agent":
                            for grandchild in child.children:
                                if grandchild.dep_ == "pobj":
                                    accumulators[resolved_name]["passive_agents"].append(
                                        grandchild.lemma_.lower()
                                    )

        # 8. Aggregate into output schema
        characters_output: dict[str, dict] = {}
        for name in character_names:
            characters_output[name] = _build_character_output(accumulators[name])

        return AnalyzerResult(
            analyzer_name="agency",
            data={
                "characters": characters_output,
                "character_list": character_names,
                "detection_method": detection_method,
                "coref_method": coref_method,
            },
            warnings=warnings,
        )
