"""Tests for heuristic pronoun resolution."""

import pytest
import spacy

from lit_engine.nlp.coref import FEMALE_PRONOUNS, MALE_PRONOUNS, resolve_pronouns


@pytest.fixture(scope="module")
def nlp():
    """Load a small spaCy model for fast test parses."""
    return spacy.load("en_core_web_sm")


def _token_text_at(doc, index):
    """Helper: get the text of the token whose .i matches `index`."""
    return doc[index].text.lower()


class TestResolvePronouns:
    def test_basic_male_resolution(self, nlp):
        """'He' resolves to most recent male character."""
        doc = nlp("Emil walked to the door. He smiled.")
        characters = {"emil": "male"}
        resolved = resolve_pronouns(doc, characters)
        # Find the "He" token
        he_indices = [t.i for t in doc if t.text.lower() == "he"]
        assert len(he_indices) == 1
        assert resolved[he_indices[0]] == "emil"

    def test_basic_female_resolution(self, nlp):
        """'She' resolves to most recent female character."""
        doc = nlp("Clara spoke softly. She laughed.")
        characters = {"clara": "female"}
        resolved = resolve_pronouns(doc, characters)
        she_indices = [t.i for t in doc if t.text.lower() == "she"]
        assert len(she_indices) == 1
        assert resolved[she_indices[0]] == "clara"

    def test_most_recent_referent(self, nlp):
        """Most recent named male becomes the referent."""
        doc = nlp("Emil sat down. Felix stood up. He spoke.")
        characters = {"emil": "male", "felix": "male"}
        resolved = resolve_pronouns(doc, characters)
        he_indices = [t.i for t in doc if t.text.lower() == "he"]
        assert len(he_indices) == 1
        assert resolved[he_indices[0]] == "felix"

    def test_ambiguous_skipped(self, nlp):
        """When two males appear in same sentence, pronouns are unresolved."""
        doc = nlp("Emil and Felix walked together. He smiled.")
        characters = {"emil": "male", "felix": "male"}
        resolved = resolve_pronouns(doc, characters, skip_ambiguous=True)
        # "He" should NOT be resolved because both males are in the
        # first sentence (which sets ambiguity) — but "He smiled" is
        # a separate sentence. The ambiguity flag is per-sentence, so
        # if spaCy splits these into two sentences, "He" in sentence 2
        # would resolve to whichever was last_male. Let's test the
        # case where both names are in THE SAME sentence as the pronoun.
        doc2 = nlp("Emil and Felix said he was tired.")
        resolved2 = resolve_pronouns(doc2, characters, skip_ambiguous=True)
        he_indices = [t.i for t in doc2 if t.text.lower() == "he"]
        for idx in he_indices:
            assert idx not in resolved2, "Pronoun should be unresolved in ambiguous sentence"

    def test_cross_sentence_persistence(self, nlp):
        """Referent carries from sentence 1 through sentence 3."""
        doc = nlp("Emil entered the room. The room was dark. He sat down.")
        characters = {"emil": "male"}
        resolved = resolve_pronouns(doc, characters)
        he_indices = [t.i for t in doc if t.text.lower() == "he"]
        assert len(he_indices) >= 1
        assert resolved[he_indices[0]] == "emil"

    def test_empty_characters(self, nlp):
        """No characters dict → empty resolution."""
        doc = nlp("He walked. She spoke.")
        resolved = resolve_pronouns(doc, {})
        assert resolved == {}

    def test_mixed_gender(self, nlp):
        """Male and female characters resolve independently."""
        doc = nlp("Emil entered. Clara followed. He turned. She smiled.")
        characters = {"emil": "male", "clara": "female"}
        resolved = resolve_pronouns(doc, characters)
        he_indices = [t.i for t in doc if t.text.lower() == "he"]
        she_indices = [t.i for t in doc if t.text.lower() == "she"]
        assert len(he_indices) >= 1
        assert len(she_indices) >= 1
        assert resolved[he_indices[0]] == "emil"
        assert resolved[she_indices[0]] == "clara"

    def test_unknown_gender_skipped(self, nlp):
        """Character with 'unknown' gender is never used as a referent."""
        doc = nlp("Jordan entered the room. He sat down.")
        characters = {"jordan": "unknown"}
        resolved = resolve_pronouns(doc, characters)
        he_indices = [t.i for t in doc if t.text.lower() == "he"]
        for idx in he_indices:
            assert idx not in resolved, "Unknown-gender character should not resolve pronouns"
