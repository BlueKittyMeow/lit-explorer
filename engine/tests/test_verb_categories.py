"""Tests for semantic verb classification."""

from lit_engine.nlp.verb_categories import (
    VERB_CATEGORIES,
    build_verb_lookup,
    categorize_verb,
)

EXPECTED_CATEGORIES = {
    "perception",
    "cognition",
    "emotion",
    "speech",
    "motion",
    "physical_action",
    "gesture",
    "resistance",
}


class TestVerbCategories:
    def test_all_categories_present(self):
        """VERB_CATEGORIES has exactly the 8 expected keys."""
        assert set(VERB_CATEGORIES.keys()) == EXPECTED_CATEGORIES

    def test_no_empty_categories(self):
        """Every category set is non-empty."""
        for cat, verbs in VERB_CATEGORIES.items():
            assert len(verbs) > 0, f"Category {cat!r} is empty"

    def test_no_duplicate_verbs(self):
        """No verb appears in more than one category."""
        seen: dict[str, str] = {}
        for cat, verbs in VERB_CATEGORIES.items():
            for verb in verbs:
                assert verb not in seen, (
                    f"Verb {verb!r} in both {seen[verb]!r} and {cat!r}"
                )
                seen[verb] = cat

    def test_deny_not_in_speech(self):
        """'deny' is only in 'resistance', not in 'speech' (controlled deviation)."""
        assert "deny" not in VERB_CATEGORIES["speech"]
        assert "deny" in VERB_CATEGORIES["resistance"]


class TestBuildLookup:
    def test_lookup_coverage(self):
        """Inverted lookup has an entry for every verb in every category."""
        lookup = build_verb_lookup()
        for cat, verbs in VERB_CATEGORIES.items():
            for verb in verbs:
                assert verb in lookup, f"Verb {verb!r} missing from lookup"
                assert lookup[verb] == cat

    def test_lookup_size(self):
        """Lookup has exactly as many entries as total verbs across categories."""
        lookup = build_verb_lookup()
        total_verbs = sum(len(v) for v in VERB_CATEGORIES.values())
        assert len(lookup) == total_verbs


class TestCategorizeVerb:
    def test_categorize_known_verbs(self):
        """Known verbs map to their expected categories."""
        lookup = build_verb_lookup()
        assert categorize_verb("see", lookup) == "perception"
        assert categorize_verb("think", lookup) == "cognition"
        assert categorize_verb("deny", lookup) == "resistance"
        assert categorize_verb("walk", lookup) == "motion"
        assert categorize_verb("nod", lookup) == "gesture"
        assert categorize_verb("feel", lookup) == "emotion"
        assert categorize_verb("tell", lookup) == "speech"
        assert categorize_verb("take", lookup) == "physical_action"

    def test_categorize_unknown_verb(self):
        """Unknown verb returns 'other'."""
        lookup = build_verb_lookup()
        assert categorize_verb("flibbertigibbet", lookup) == "other"
