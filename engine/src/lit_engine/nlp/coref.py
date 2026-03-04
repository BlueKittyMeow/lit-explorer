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

    Strategy (two-pass per sentence, matching existing code):
    1. Track most recent named character mention per gender per sentence.
    2. For he/him/his -> assign to most recent male character.
    3. For she/her/hers -> assign to most recent female character.
    4. If skip_ambiguous and multiple characters of the same gender appear
       in one sentence, skip pronoun resolution for that gender.

    Args:
        doc: spaCy Doc of the full manuscript.
        characters: dict mapping character name (lowercase) -> gender
                    e.g. {"emil": "male", "felix": "male"}
        skip_ambiguous: if True, skip pronoun resolution in sentences
                        where multiple characters of the same gender appear.

    Returns:
        dict mapping token index -> resolved character name (lowercase).
    """
    resolved: dict[int, str] = {}
    last_male: str | None = None
    last_female: str | None = None

    for sent in doc.sents:
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
                elif gender == "female":
                    last_female = name
                    females_in_sent.add(name)
                # "unknown" gender: skip, do not track as referent

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
