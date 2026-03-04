"""Tests for sentence-to-char-offset location utility."""

from lit_engine.nlp.sentence_locate import locate_sentences


class TestLocateSentences:
    def test_basic_mapping(self):
        """Maps sentences to correct char offsets."""
        text = "Hello world. Goodbye world."
        sentences = ["Hello world.", "Goodbye world."]
        offsets = locate_sentences(text, sentences)
        assert offsets[0] == (0, 12)
        assert offsets[1] == (13, 27)

    def test_repeated_sentences(self):
        """Handles repeated sentences via cumulative search_from."""
        text = "Yes. Yes. Yes."
        sentences = ["Yes.", "Yes.", "Yes."]
        offsets = locate_sentences(text, sentences)
        assert offsets[0] == (0, 4)
        assert offsets[1] == (5, 9)
        assert offsets[2] == (10, 14)

    def test_fallback_on_missing_sentence(self):
        """Falls back to search_from when sentence not found in text."""
        text = "Hello world. Goodbye world."
        # Second sentence has been "normalized" by tokenizer and won't match
        sentences = ["Hello world.", "Goodbye  world."]
        offsets = locate_sentences(text, sentences)
        assert offsets[0] == (0, 12)
        # Fallback: starts at search_from (12), length of the normalized sentence
        assert offsets[1][0] == 12

    def test_empty_input(self):
        """Empty sentences list returns empty offsets."""
        offsets = locate_sentences("Hello.", [])
        assert offsets == []

    def test_offsets_monotonically_increase(self):
        """Offsets are always monotonically increasing."""
        text = "One. Two. Three. Four. Five."
        sentences = ["One.", "Two.", "Three.", "Four.", "Five."]
        offsets = locate_sentences(text, sentences)
        for i in range(1, len(offsets)):
            assert offsets[i][0] >= offsets[i - 1][1]
