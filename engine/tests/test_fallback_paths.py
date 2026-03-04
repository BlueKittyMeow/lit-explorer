"""Tests for analyzer fallback / edge-case paths."""

import pytest

from lit_engine.analyzers import AnalyzerResult
from lit_engine.analyzers.pacing import PacingAnalyzer
from lit_engine.analyzers.sentiment import SentimentAnalyzer
from lit_engine.config import merge_config
from lit_engine.nlp.dialogue_extract import extract_dialogue


class TestSentimentEmptyResult:
    """Sentiment analyzer with no-sentence text returns empty result."""

    def test_empty_text(self):
        analyzer = SentimentAnalyzer()
        config = merge_config({})
        result = analyzer.analyze("", config)
        assert isinstance(result, AnalyzerResult)
        assert result.data["arc"] == []
        assert result.data["smoothed_arc"] == []
        assert result.data["chapter_averages"] == []
        assert result.data["extremes"]["most_positive"] is None
        assert result.data["extremes"]["most_negative"] is None

    def test_whitespace_only_text(self):
        analyzer = SentimentAnalyzer()
        config = merge_config({})
        result = analyzer.analyze("   \n\n   ", config)
        assert result.data["arc"] == []
        assert len(result.warnings) > 0


class TestPacingEmptyData:
    """Pacing analyzer with no sentence data returns empty result."""

    def test_no_context(self):
        analyzer = PacingAnalyzer()
        config = merge_config({})
        result = analyzer.analyze("Some text.", config, context=None)
        assert result.data["sentence_count"] == 0
        assert result.data["distribution"]["mean"] == 0.0
        assert result.data["staccato_passages"] == []
        assert result.data["flowing_passages"] == []
        assert len(result.warnings) > 0

    def test_empty_blocks(self):
        """Texttiling result with no sentence_lengths in blocks."""
        analyzer = PacingAnalyzer()
        config = merge_config({})
        tt_result = AnalyzerResult(
            analyzer_name="texttiling",
            data={"blocks": [{"id": 1, "sentence_lengths": []}]},
        )
        result = analyzer.analyze("Some text.", config, context={"texttiling": tt_result})
        assert result.data["sentence_count"] == 0
        assert len(result.warnings) > 0


class TestDialogueCrossParagraph:
    """Dialogue extraction handles multi-paragraph continued dialogue."""

    def test_cross_paragraph_continuation(self):
        """Opening quote in next paragraph continues the span."""
        text = (
            '\u201cHello there,\n\n'
            '\u201cI continued speaking,\u201d he said.'
        )
        spans = extract_dialogue(text)
        assert len(spans) == 1
        # The span should include text from both paragraphs
        assert "Hello" in spans[0].text
        assert "continued" in spans[0].text

    def test_paragraph_break_terminates_without_continuation(self):
        """Paragraph break without re-opened quote terminates span."""
        text = (
            '\u201cHello there,\n\n'
            'He walked away.'
        )
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert "Hello" in spans[0].text
        # Span should end at the paragraph break
        assert "walked" not in spans[0].text

    def test_eof_terminates_unclosed_quote(self):
        """EOF terminates an unclosed quote without crash."""
        text = '\u201cThis never closes'
        spans = extract_dialogue(text)
        assert len(spans) == 1
        assert "never closes" in spans[0].text
