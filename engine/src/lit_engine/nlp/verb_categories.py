"""Semantic verb classification for literary prose."""

VERB_CATEGORIES: dict[str, set[str]] = {
    "perception": {
        "watch", "see", "look", "observe", "notice", "gaze", "stare",
        "glance", "glimpse", "peer", "regard", "eye", "view", "spot",
        "hear", "listen", "smell", "taste", "sense", "perceive", "detect",
    },
    "cognition": {
        "think", "know", "believe", "wonder", "realize", "understand",
        "consider", "imagine", "remember", "forget", "suspect", "recognize",
        "suppose", "decide", "reason", "ponder", "reflect", "muse",
        "contemplate", "reckon", "doubt", "assume", "recall", "hope",
    },
    "emotion": {
        "feel", "want", "wish", "love", "hate", "fear", "dread", "enjoy",
        "desire", "long", "yearn", "ache", "need", "crave", "regret",
        "mourn", "grieve", "suffer", "hurt", "envy", "resent", "admire",
    },
    "speech": {
        "tell", "ask", "answer", "reply", "whisper", "murmur", "call",
        "shout", "cry", "scream", "mutter", "announce", "declare",
        "insist", "suggest", "explain", "demand", "plead", "beg",
        "confess", "admit", "argue", "protest", "interrupt",
    },
    "motion": {
        "walk", "run", "move", "turn", "step", "cross", "enter", "leave",
        "approach", "follow", "lead", "rush", "hurry", "wander", "pace",
        "climb", "descend", "rise", "fall", "sit", "stand", "lean",
        "kneel", "stumble", "flee", "retreat", "advance", "return",
    },
    "physical_action": {
        "take", "hold", "grab", "pull", "push", "touch", "reach",
        "open", "close", "break", "cut", "strike", "throw", "catch",
        "lift", "drop", "place", "set", "press", "squeeze", "grip",
        "release", "shake", "pour", "draw", "write", "tear", "lock",
    },
    "gesture": {
        "nod", "shrug", "wave", "point", "frown", "smile", "wince",
        "blink", "sigh", "laugh", "gasp", "tremble", "shiver", "swallow",
        "bow", "gesture", "clench", "bite",
    },
    "resistance": {
        "resist", "refuse", "deny", "reject", "fight", "struggle",
        "defy", "forbid", "prevent", "stop", "block", "withdraw",
        "avoid", "ignore", "suppress", "repress", "restrain",
    },
}


def build_verb_lookup() -> dict[str, str]:
    """Build inverted lookup: verb lemma -> category name."""
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
