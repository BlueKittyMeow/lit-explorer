"""Tests for the dialogue analyzer."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.dialogue import DialogueAnalyzer
from lit_engine.config import merge_config


DIALOGUE_TEXT = (
    '\u201cGood morning,\u201d Emil said. '
    'He walked to the window and looked outside. '
    '\u201cThe weather is fine today,\u201d he continued. '
    'Clara entered the room silently. '
    '\u201cI agree,\u201d she replied. '
    'The room fell quiet.'
)


@pytest.fixture
def dialogue_result():
    analyzer = DialogueAnalyzer()
    config = merge_config({})
    return analyzer.analyze(DIALOGUE_TEXT, config)


class TestDialogueAnalyzer:
    def test_result_type(self, dialogue_result):
        """Returns AnalyzerResult with name='dialogue'."""
        assert isinstance(dialogue_result, AnalyzerResult)
        assert dialogue_result.analyzer_name == "dialogue"

    def test_output_schema(self, dialogue_result):
        """Data has required keys."""
        data = dialogue_result.data
        assert "total_dialogue_words" in data
        assert "total_narrative_words" in data
        assert "overall_dialogue_ratio" in data
        assert "span_count" in data
        assert "spans" in data

    def test_dialogue_ratio_range(self, dialogue_result):
        """Dialogue ratio is between 0 and 1."""
        ratio = dialogue_result.data["overall_dialogue_ratio"]
        assert 0.0 <= ratio <= 1.0

    def test_spans_detected(self, dialogue_result):
        """At least one dialogue span found."""
        assert dialogue_result.data["span_count"] > 0
        assert len(dialogue_result.data["spans"]) > 0

    def test_no_dialogue_text(self):
        """Text with no dialogue returns zero ratio."""
        analyzer = DialogueAnalyzer()
        config = merge_config({})
        result = analyzer.analyze("Plain text with no quotes at all.", config)
        assert result.data["span_count"] == 0
        assert result.data["overall_dialogue_ratio"] == 0.0

    def test_registers_as_analyzer(self):
        """get_analyzer('dialogue') returns a DialogueAnalyzer."""
        analyzer = get_analyzer("dialogue")
        assert isinstance(analyzer, DialogueAnalyzer)
