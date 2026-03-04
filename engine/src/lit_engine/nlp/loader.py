"""Lazy spaCy model loading with caching."""

from functools import lru_cache

import spacy


@lru_cache(maxsize=1)
def load_spacy(model_name: str = "en_core_web_lg") -> spacy.Language:
    """
    Load a spaCy model, caching the result.

    Falls back to en_core_web_sm if the requested model isn't installed.
    Raises RuntimeError if no model can be loaded.
    """
    try:
        return spacy.load(model_name)
    except OSError:
        pass

    fallback = "en_core_web_sm"
    try:
        return spacy.load(fallback)
    except OSError:
        raise RuntimeError(
            f"No spaCy model available. Install one with: "
            f"python -m spacy download {model_name}"
        )


def parse_document(
    text: str,
    model_name: str = "en_core_web_lg",
) -> "spacy.tokens.Doc":
    """Parse text into a spaCy Doc, handling max_length for long manuscripts."""
    nlp = load_spacy(model_name)
    nlp.max_length = max(nlp.max_length, len(text) + 100_000)
    return nlp(text)
