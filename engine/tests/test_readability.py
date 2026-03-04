"""Tests for the readability analyzer."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.readability import ReadabilityAnalyzer
from lit_engine.analyzers.texttiling import TextTilingAnalyzer
from lit_engine.config import merge_config


# Build a text long enough for TextTiling to produce blocks
READABILITY_TEXT = (
    "The morning light streamed through the laboratory windows. "
    "Emil stood at the bench, arranging instruments with careful precision. "
    "Each tool had its proper place, each specimen its designated shelf. "
    "The work demanded absolute concentration and unwavering patience. "
) * 50  # ~200 sentences


@pytest.fixture
def readability_result():
    """Run texttiling first, then readability with context."""
    config = merge_config({})
    tt = TextTilingAnalyzer()
    tt_result = tt.analyze(READABILITY_TEXT, config)
    context = {"texttiling": tt_result}

    analyzer = ReadabilityAnalyzer()
    return analyzer.analyze(READABILITY_TEXT, config, context=context)


class TestReadabilityAnalyzer:
    def test_result_type(self, readability_result):
        """Returns AnalyzerResult with name='readability'."""
        assert isinstance(readability_result, AnalyzerResult)
        assert readability_result.analyzer_name == "readability"

    def test_output_schema(self, readability_result):
        """Data has per_block and whole_text keys."""
        data = readability_result.data
        assert "per_block" in data
        assert "whole_text" in data
        assert isinstance(data["per_block"], list)
        assert isinstance(data["whole_text"], dict)

    def test_per_block_metrics(self, readability_result):
        """Each per_block entry has required extended metrics."""
        for entry in readability_result.data["per_block"]:
            assert "block_id" in entry
            assert "coleman_liau" in entry
            assert "smog" in entry
            assert "ari" in entry

    def test_whole_text_metrics(self, readability_result):
        """Whole-text summary has all 6 readability metrics."""
        wt = readability_result.data["whole_text"]
        for key in ("flesch_ease", "flesch_grade", "gunning_fog",
                     "coleman_liau", "smog", "ari"):
            assert key in wt, f"Missing whole_text metric: {key}"

    def test_registers_as_analyzer(self):
        """get_analyzer('readability') returns a ReadabilityAnalyzer."""
        analyzer = get_analyzer("readability")
        assert isinstance(analyzer, ReadabilityAnalyzer)
