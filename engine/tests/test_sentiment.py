"""Tests for the sentiment analyzer."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.sentiment import SentimentAnalyzer
from lit_engine.config import merge_config


SENTIMENT_TEXT = (
    "\n"
    "Chapter 1 - Joy\n"
    + (
        "The sun was shining brightly. Everyone was happy and laughing. "
        "It was a wonderful, beautiful day full of love and warmth. "
        "The children played joyfully in the garden. "
        "Life felt absolutely perfect and magnificent. "
    ) * 8
    + "\n"
    "\n"
    "Chapter 2 - Sorrow\n"
    + (
        "The rain fell heavily on the empty streets. "
        "He felt terrible, alone, and utterly miserable. "
        "Everything was ruined and destroyed. "
        "The darkness consumed all hope and left only despair. "
        "It was the worst day of his entire wretched life. "
    ) * 8
)


@pytest.fixture
def sentiment_result():
    analyzer = SentimentAnalyzer()
    config = merge_config({})
    return analyzer.analyze(SENTIMENT_TEXT, config)


class TestSentimentAnalyzer:
    def test_result_type(self, sentiment_result):
        """Returns AnalyzerResult with name='sentiment'."""
        assert isinstance(sentiment_result, AnalyzerResult)
        assert sentiment_result.analyzer_name == "sentiment"

    def test_output_schema(self, sentiment_result):
        """Data has all required top-level keys."""
        data = sentiment_result.data
        assert data["method"] == "vader"
        assert data["granularity"] == "sentence"
        assert "arc" in data
        assert "smoothed_arc" in data
        assert "chapter_averages" in data
        assert "extremes" in data

    def test_arc_positions_in_range(self, sentiment_result):
        """All arc positions are between 0.0 and 1.0."""
        for entry in sentiment_result.data["arc"]:
            assert 0.0 <= entry["position"] <= 1.0

    def test_arc_entry_schema(self, sentiment_result):
        """Each arc entry has position, compound, pos, neg, neu."""
        for entry in sentiment_result.data["arc"]:
            assert "position" in entry
            assert "compound" in entry
            assert "pos" in entry
            assert "neg" in entry
            assert "neu" in entry

    def test_arc_scores_in_range(self, sentiment_result):
        """VADER compound is in [-1, 1], pos/neg/neu in [0, 1]."""
        for entry in sentiment_result.data["arc"]:
            assert -1.0 <= entry["compound"] <= 1.0
            assert 0.0 <= entry["pos"] <= 1.0
            assert 0.0 <= entry["neg"] <= 1.0
            assert 0.0 <= entry["neu"] <= 1.0

    def test_extremes_found(self, sentiment_result):
        """Extremes has most_positive and most_negative."""
        extremes = sentiment_result.data["extremes"]
        assert "most_positive" in extremes
        assert "most_negative" in extremes
        assert extremes["most_positive"]["score"] > 0
        assert extremes["most_negative"]["score"] < 0
        assert "text_preview" in extremes["most_positive"]
        assert "text_preview" in extremes["most_negative"]

    def test_chapter_averages(self, sentiment_result):
        """Chapter averages detected from chapter headings."""
        avgs = sentiment_result.data["chapter_averages"]
        assert len(avgs) >= 2
        # Chapter 1 (joy) should be more positive than Chapter 2 (sorrow)
        ch1 = next(a for a in avgs if a["chapter"] == 1)
        ch2 = next(a for a in avgs if a["chapter"] == 2)
        assert ch1["compound"] > ch2["compound"]

    def test_smoothed_arc_length(self, sentiment_result):
        """smoothed_arc length <= min(200, len(arc))."""
        arc_len = len(sentiment_result.data["arc"])
        smoothed_len = len(sentiment_result.data["smoothed_arc"])
        expected_max = min(200, arc_len)
        assert smoothed_len <= expected_max

    def test_registers_as_analyzer(self):
        """get_analyzer('sentiment') returns a SentimentAnalyzer."""
        analyzer = get_analyzer("sentiment")
        assert isinstance(analyzer, SentimentAnalyzer)
