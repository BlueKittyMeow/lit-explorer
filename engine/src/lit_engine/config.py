"""Default configuration for lit-engine analyzers."""

DEFAULT_CONFIG: dict = {
    # TextTiling
    "texttiling_w": 40,
    "texttiling_k": 20,
    "texttiling_fallback_w": 20,
    "texttiling_fallback_k": 10,
    "texttiling_min_words": 30,
    "texttiling_min_alpha": 20,

    # MATTR
    "mattr_window": 50,

    # spaCy
    "spacy_model": "en_core_web_lg",

    # Coreference
    "coref_enabled": True,
    "coref_method": "heuristic",

    # Characters (used in Stage 2)
    "characters": [],
    "character_genders": {},
    "max_auto_characters": 8,
    "min_character_mentions": 10,

    # Stop verbs (shared concern — used by agency and chapter analyzers)
    "stop_verbs": frozenset({
        "be", "have", "do", "say", "go", "get", "seem", "make", "let",
        "come", "take", "give", "keep", "put", "set", "find", "tell",
        "become", "leave", "show", "try", "call", "ask", "use", "may",
        "will", "would", "could", "should", "might", "shall", "must", "can",
    }),

    # Chapter detection
    "chapter_pattern": None,           # None = DEFAULT_CHAPTER_PATTERN
    "min_chapter_words": 100,          # reject detected "chapters" shorter than this

    # Dialogue
    "dialogue_quote_pairs": None,      # None = QUOTE_PAIRS default

    # Pacing
    "pacing_staccato_threshold": 8,    # avg_sentence_length below = staccato
    "pacing_flowing_threshold": 25,    # avg_sentence_length above = flowing

    # Sentiment
    "sentiment_method": "vader",
    "smoothed_arc_points": 200,        # number of points in smoothed_arc
}


def merge_config(overrides: dict | None = None) -> dict:
    """Merge user overrides into default config. Returns a new dict."""
    config = dict(DEFAULT_CONFIG)
    if overrides:
        config.update(overrides)
    return config
