"""Tests for the pacing analyzer."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.pacing import PacingAnalyzer
from lit_engine.analyzers.texttiling import TextTilingAnalyzer
from lit_engine.config import merge_config


# Mix of short and long sentences for rhythm detection
PACING_TEXT = (
    "He stopped. Listened. Nothing. The corridor was empty. "
    "He waited. Silence. Then a sound. Footsteps. Close. "
    "Emil turned and ran through the darkened hallway. "
) * 20 + (
    "The morning brought with it a kind of exhausted peace that settled "
    "over the laboratory like a fine dust, covering every surface with "
    "the residue of the previous night's frantic activity, and Emil sat "
    "at his desk contemplating the strange series of events that had led "
    "him to this particular moment in his otherwise unremarkable career. "
) * 20


@pytest.fixture
def pacing_result():
    config = merge_config({})
    tt = TextTilingAnalyzer()
    tt_result = tt.analyze(PACING_TEXT, config)
    context = {"texttiling": tt_result}

    analyzer = PacingAnalyzer()
    return analyzer.analyze(PACING_TEXT, config, context=context)


class TestPacingAnalyzer:
    def test_result_type(self, pacing_result):
        """Returns AnalyzerResult with name='pacing'."""
        assert isinstance(pacing_result, AnalyzerResult)
        assert pacing_result.analyzer_name == "pacing"

    def test_output_schema(self, pacing_result):
        """Data has required keys."""
        data = pacing_result.data
        assert "sentence_count" in data
        assert "distribution" in data
        assert "staccato_passages" in data
        assert "flowing_passages" in data

    def test_distribution_stats(self, pacing_result):
        """Distribution has mean, median, std_dev, min, max, percentiles."""
        dist = pacing_result.data["distribution"]
        for key in ("mean", "median", "std_dev", "min", "max", "percentiles"):
            assert key in dist, f"Missing distribution key: {key}"

    def test_percentiles(self, pacing_result):
        """Percentiles has the expected keys."""
        pct = pacing_result.data["distribution"]["percentiles"]
        for key in ("10", "25", "50", "75", "90"):
            assert key in pct, f"Missing percentile: {key}"

    def test_staccato_format(self, pacing_result):
        """Staccato passages have required fields."""
        for passage in pacing_result.data["staccato_passages"]:
            assert "block_id" in passage
            assert "avg_sentence_length" in passage
            assert "sentence_count" in passage

    def test_flowing_format(self, pacing_result):
        """Flowing passages have required fields."""
        for passage in pacing_result.data["flowing_passages"]:
            assert "block_id" in passage
            assert "avg_sentence_length" in passage
            assert "sentence_count" in passage

    def test_registers_as_analyzer(self):
        """get_analyzer('pacing') returns a PacingAnalyzer."""
        analyzer = get_analyzer("pacing")
        assert isinstance(analyzer, PacingAnalyzer)
