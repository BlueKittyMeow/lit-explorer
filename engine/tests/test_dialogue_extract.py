"""Tests for dialogue span extraction utility."""

import pytest

from lit_engine.nlp.dialogue_extract import DialogueSpan, extract_dialogue


class TestExtractDialogue:
    def test_curly_quotes(self):
        """Extracts dialogue in curly double quotes."""
        text = 'He said, \u201cHello there.\u201d She nodded.'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert spans[0].text == "Hello there."

    def test_multiple_spans(self):
        """Extracts multiple dialogue spans."""
        text = '\u201cFirst,\u201d he said. \u201cSecond,\u201d she replied.'
        spans = extract_dialogue(text)
        assert len(spans) == 2
        assert spans[0].text == "First,"
        assert spans[1].text == "Second,"

    def test_german_quotes(self):
        """Extracts dialogue in German low-high quotes."""
        text = 'Er sagte, \u201eHallo dort.\u201c Sie nickte.'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert spans[0].text == "Hallo dort."

    def test_straight_quotes(self):
        """Falls back to straight double quotes."""
        text = 'He said, "Hello there." She nodded.'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert spans[0].text == "Hello there."

    def test_unclosed_quote_at_eof(self):
        """Unclosed quote extends to end of text."""
        text = 'He said, \u201cThis never ends'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert "This never ends" in spans[0].text

    def test_unclosed_quote_at_paragraph(self):
        """Unclosed quote terminates at paragraph break (if no continuation)."""
        text = 'He said, \u201cStarting here\n\nNew paragraph without quote.'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        # Span should terminate before the new paragraph
        assert spans[0].end_char <= text.index("\n\n") + 2

    def test_empty_text(self):
        """Empty text returns no spans."""
        spans = extract_dialogue("")
        assert spans == []

    def test_no_dialogue(self):
        """Text without quotes returns no spans."""
        text = "Plain narrative text with no dialogue at all."
        spans = extract_dialogue(text)
        assert spans == []

    def test_span_offsets_valid(self):
        """Span char offsets are within text bounds."""
        text = 'Before \u201cHello\u201d after \u201cWorld\u201d end.'
        spans = extract_dialogue(text)
        for span in spans:
            assert 0 <= span.start_char < len(text)
            assert 0 < span.end_char <= len(text)
            assert span.start_char < span.end_char

    def test_empty_quotes_filtered(self):
        """Dialogue with nothing between quotes is filtered out."""
        text = 'He said, \u201c\u201d quietly.'
        spans = extract_dialogue(text)
        assert len(spans) == 0
