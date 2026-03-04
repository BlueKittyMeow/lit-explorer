"""Tests for the silence analyzer."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.dialogue import DialogueAnalyzer
from lit_engine.analyzers.silence import SilenceAnalyzer
from lit_engine.config import merge_config


SILENCE_TEXT = (
    "The room was quiet for a long time. Nobody spoke. "
    "The clock ticked steadily on the wall. "
    '\u201cFinally,\u201d Emil said. '
    "There was another pause. The wind blew outside. "
    "Rain began to fall against the windows. "
    '\u201cI see,\u201d Clara replied. '
    "The conversation ended there. "
    "Emil turned and left the room without a word. "
    "He walked down the long corridor alone."
)


@pytest.fixture
def silence_result():
    config = merge_config({})
    dialogue = DialogueAnalyzer()
    dialogue_result = dialogue.analyze(SILENCE_TEXT, config)
    context = {"dialogue": dialogue_result}

    analyzer = SilenceAnalyzer()
    return analyzer.analyze(SILENCE_TEXT, config, context=context)


class TestSilenceAnalyzer:
    def test_result_type(self, silence_result):
        """Returns AnalyzerResult with name='silence'."""
        assert isinstance(silence_result, AnalyzerResult)
        assert silence_result.analyzer_name == "silence"

    def test_output_schema(self, silence_result):
        """Data has required keys."""
        data = silence_result.data
        assert "gaps" in data
        assert "longest_silence" in data
        assert "avg_gap_words" in data
        assert "total_gaps" in data

    def test_gaps_detected(self, silence_result):
        """Gaps between dialogue spans are found."""
        assert silence_result.data["total_gaps"] > 0
        assert len(silence_result.data["gaps"]) > 0

    def test_gap_schema(self, silence_result):
        """Each gap has required fields."""
        for gap in silence_result.data["gaps"]:
            assert "start_char" in gap
            assert "end_char" in gap
            assert "word_count" in gap
            assert gap["word_count"] > 0  # 0-word gaps filtered

    def test_longest_silence(self, silence_result):
        """longest_silence has word_count, position, preview."""
        ls = silence_result.data["longest_silence"]
        assert ls is not None
        assert "word_count" in ls
        assert "position" in ls
        assert "preview" in ls
        assert ls["word_count"] > 0

    def test_no_dialogue_edge_case(self):
        """Text with no dialogue returns empty gaps + warning."""
        config = merge_config({})
        dialogue = DialogueAnalyzer()
        dialogue_result = dialogue.analyze("Plain text. No quotes.", config)
        context = {"dialogue": dialogue_result}

        analyzer = SilenceAnalyzer()
        result = analyzer.analyze("Plain text. No quotes.", config, context=context)
        assert result.data["total_gaps"] == 0
        assert result.data["gaps"] == []
        assert result.data["longest_silence"] is None

    def test_registers_as_analyzer(self):
        """get_analyzer('silence') returns a SilenceAnalyzer."""
        analyzer = get_analyzer("silence")
        assert isinstance(analyzer, SilenceAnalyzer)
