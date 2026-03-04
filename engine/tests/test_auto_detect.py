"""Tests for character auto-detection and gender inference."""

import pytest
import spacy
from spacy.tokens import Doc

from lit_engine.analyzers.agency import (
    HONORIFICS,
    auto_detect_characters,
    infer_gender,
)


@pytest.fixture(scope="module")
def nlp():
    """Load a small spaCy model for test parses."""
    return spacy.load("en_core_web_sm")


def _make_doc_with_entities(nlp, text, entity_spans):
    """
    Create a spaCy Doc with manually set entity spans.

    entity_spans: list of (start_char, end_char, label) tuples
    """
    doc = nlp.make_doc(text)
    spans = []
    for start_char, end_char, label in entity_spans:
        span = doc.char_span(start_char, end_char, label=label)
        if span is not None:
            spans.append(span)
    doc.ents = spans
    return doc


class TestAutoDetectCharacters:
    def test_detects_person_entities(self, nlp):
        """Text with repeated names detects them."""
        # Build text with "Emil" appearing 12 times
        sentences = [f"Emil walked to the door." for _ in range(12)]
        text = " ".join(sentences)
        doc = nlp(text)
        # Manually set entities: find each "Emil" occurrence
        entity_spans = []
        start = 0
        for _ in range(12):
            idx = text.index("Emil", start)
            entity_spans.append((idx, idx + 4, "PERSON"))
            start = idx + 4
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "emil" in result

    def test_min_mentions_filter(self, nlp):
        """Name appearing 5x with min_mentions=10 is not detected (> not >=)."""
        sentences = [f"Alice walked." for _ in range(5)]
        text = " ".join(sentences)
        entity_spans = []
        start = 0
        for _ in range(5):
            idx = text.index("Alice", start)
            entity_spans.append((idx, idx + 5, "PERSON"))
            start = idx + 5
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "alice" not in result

    def test_min_mentions_boundary(self, nlp):
        """Name appearing exactly 10x with min_mentions=10 is NOT detected (strictly >)."""
        sentences = [f"Bob sat quietly." for _ in range(10)]
        text = " ".join(sentences)
        entity_spans = []
        start = 0
        for _ in range(10):
            idx = text.index("Bob", start)
            entity_spans.append((idx, idx + 3, "PERSON"))
            start = idx + 3
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "bob" not in result, "Exactly 10 mentions should NOT pass (> not >=)"

    def test_max_characters_cap(self, nlp):
        """More than max_characters names → only top N returned."""
        # Create 10 distinct names, each appearing 15 times
        names = ["alice", "bob", "clara", "david", "elena",
                 "frank", "greta", "hans", "irene", "james"]
        parts = []
        entity_spans = []
        offset = 0
        for name in names:
            for _ in range(15):
                sentence = f"{name.title()} walked. "
                parts.append(sentence)
                entity_spans.append((offset, offset + len(name), "PERSON"))
                offset += len(sentence)
        text = "".join(parts)
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10, max_characters=8)
        assert len(result) <= 8

    def test_first_name_normalization(self, nlp):
        """Multi-token name uses first non-honorific token."""
        text = " ".join([f"Felix von Braun entered." for _ in range(12)])
        entity_spans = []
        start = 0
        for _ in range(12):
            idx = text.index("Felix von Braun", start)
            entity_spans.append((idx, idx + len("Felix von Braun"), "PERSON"))
            start = idx + len("Felix von Braun")
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "felix" in result

    def test_title_stripping(self, nlp):
        """Honorific titles are stripped before name extraction."""
        text = " ".join([f"Dr. Watson examined the patient." for _ in range(12)])
        entity_spans = []
        start = 0
        for _ in range(12):
            idx = text.index("Dr. Watson", start)
            entity_spans.append((idx, idx + len("Dr. Watson"), "PERSON"))
            start = idx + len("Dr. Watson")
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "watson" in result
        assert "dr" not in result

    def test_noble_particle_stripping(self, nlp):
        """'Herr von Braun' strips both honorific and particle → 'braun'."""
        text = " ".join(["Herr von Braun entered the room." for _ in range(12)])
        entity_spans = []
        start = 0
        for _ in range(12):
            idx = text.index("Herr von Braun", start)
            entity_spans.append((idx, idx + len("Herr von Braun"), "PERSON"))
            start = idx + len("Herr von Braun")
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "braun" in result
        assert "herr" not in result
        assert "von" not in result

    def test_overlapping_names(self, nlp):
        """'Emil' and 'Emily' should remain separate characters."""
        parts = []
        entity_spans = []
        offset = 0
        for _ in range(12):
            s = "Emil walked. "
            parts.append(s)
            entity_spans.append((offset, offset + 4, "PERSON"))
            offset += len(s)
        for _ in range(12):
            s = "Emily spoke. "
            parts.append(s)
            entity_spans.append((offset, offset + 5, "PERSON"))
            offset += len(s)
        text = "".join(parts)
        doc = _make_doc_with_entities(nlp, text, entity_spans)
        result = auto_detect_characters(doc, min_mentions=10)
        assert "emil" in result
        assert "emily" in result
        assert len([n for n in result if n.startswith("emil")]) == 2


class TestInferGender:
    def test_infer_gender_male(self, nlp):
        """Character co-occurring with 'he' pronouns → male."""
        # Name and pronouns must co-occur in the SAME sentence for counting
        doc = nlp(
            "Emil walked to the door and he opened it carefully. "
            "When Emil sat down he looked around the room. "
            "Emil smiled and he nodded to himself."
        )
        result = infer_gender(doc, "emil")
        assert result == "male"

    def test_infer_gender_female(self, nlp):
        """Character co-occurring with 'she' pronouns → female."""
        # Name and pronouns must co-occur in the SAME sentence for counting
        doc = nlp(
            "Clara entered the hall and she looked around. "
            "When Clara spoke she nodded slowly. "
            "Clara smiled and she waved goodbye."
        )
        result = infer_gender(doc, "clara")
        assert result == "female"

    def test_infer_gender_unknown(self, nlp):
        """Character with few or no pronouns → unknown."""
        doc = nlp("Jordan entered. Jordan sat down. Jordan left.")
        result = infer_gender(doc, "jordan")
        assert result == "unknown"
