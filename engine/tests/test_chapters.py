"""Tests for the chapters analyzer (aggregator)."""

import pytest

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.chapters import ChaptersAnalyzer
from lit_engine.analyzers.dialogue import DialogueAnalyzer
from lit_engine.analyzers.sentiment import SentimentAnalyzer
from lit_engine.analyzers.silence import SilenceAnalyzer
from lit_engine.analyzers.texttiling import TextTilingAnalyzer
from lit_engine.analyzers.agency import AgencyAnalyzer
from lit_engine.config import merge_config


# Text with 2 chapters, dialogue, named characters
CHAPTERS_TEXT = (
    "\n"
    "Chapter 1 - Morning\n"
    + (
        "Emil walked to the window. He opened the door carefully. "
        '\u201cGood morning,\u201d Emil said to Felix. '
        "Felix nodded and smiled. Emil looked around the room. "
        "He shook his head slowly. The morning was cold. "
        "Emil felt the chill in the air. It was a beautiful day. "
    ) * 8
    + "\n\n"
    "Chapter 2 - Evening\n"
    + (
        "Felix sat alone in the dark room. The evening was terrible. "
        "He felt miserable and cold. The silence was oppressive. "
        '\u201cWhere is everyone?\u201d Felix asked. '
        "Nobody answered. Felix closed his eyes in despair. "
    ) * 8
)


@pytest.fixture
def full_context():
    """Run all prerequisite analyzers to build context for chapters."""
    config = merge_config({
        "characters": ["emil", "felix"],
        "character_genders": {"emil": "male", "felix": "male"},
        "coref_enabled": False,
    })

    results = {}

    tt = TextTilingAnalyzer()
    results["texttiling"] = tt.analyze(CHAPTERS_TEXT, config)

    agency = AgencyAnalyzer()
    results["agency"] = agency.analyze(CHAPTERS_TEXT, config)

    dialogue = DialogueAnalyzer()
    results["dialogue"] = dialogue.analyze(CHAPTERS_TEXT, config)

    sentiment = SentimentAnalyzer()
    results["sentiment"] = sentiment.analyze(CHAPTERS_TEXT, config)

    silence = SilenceAnalyzer()
    results["silence"] = silence.analyze(CHAPTERS_TEXT, config, context=results)

    return config, results


@pytest.fixture
def chapters_result(full_context):
    config, context = full_context
    analyzer = ChaptersAnalyzer()
    return analyzer.analyze(CHAPTERS_TEXT, config, context=context)


class TestChaptersAnalyzer:
    def test_result_type(self, chapters_result):
        """Returns AnalyzerResult with name='chapters'."""
        assert isinstance(chapters_result, AnalyzerResult)
        assert chapters_result.analyzer_name == "chapters"

    def test_chapters_found(self, chapters_result):
        """Finds both chapters."""
        chapters = chapters_result.data["chapters"]
        assert len(chapters) == 2

    def test_chapter_schema(self, chapters_result):
        """Each chapter has all required fields."""
        required = {
            "number", "title", "word_count", "sentence_count",
            "dialogue_ratio", "avg_sentence_length", "mattr",
            "flesch_ease", "fog", "character_mentions",
            "dominant_character", "sentiment", "block_range",
        }
        for chapter in chapters_result.data["chapters"]:
            for field in required:
                assert field in chapter, f"Chapter {chapter.get('number')} missing {field!r}"

    def test_chapter_numbers_and_titles(self, chapters_result):
        """Chapter numbers and titles are correct."""
        chapters = chapters_result.data["chapters"]
        assert chapters[0]["number"] == 1
        assert chapters[0]["title"] == "Morning"
        assert chapters[1]["number"] == 2
        assert chapters[1]["title"] == "Evening"

    def test_block_to_chapter_mapping(self, chapters_result):
        """block_to_chapter mapping is present and covers blocks."""
        mapping = chapters_result.data.get("block_to_chapter", {})
        assert len(mapping) > 0
        # All values should be chapter numbers
        for block_id, chapter_num in mapping.items():
            assert chapter_num in (1, 2)

    def test_block_range_valid(self, chapters_result):
        """block_range is [first_id, last_id] with first <= last."""
        for chapter in chapters_result.data["chapters"]:
            br = chapter["block_range"]
            assert len(br) == 2
            assert br[0] <= br[1]

    def test_character_mentions(self, chapters_result):
        """Character mentions are counted per chapter."""
        ch1 = chapters_result.data["chapters"][0]
        assert "emil" in ch1["character_mentions"]
        assert "felix" in ch1["character_mentions"]
        assert ch1["character_mentions"]["emil"] > 0

    def test_dominant_character(self, chapters_result):
        """dominant_character is a string."""
        for chapter in chapters_result.data["chapters"]:
            assert isinstance(chapter["dominant_character"], str)

    def test_sentiment_per_chapter(self, chapters_result):
        """Each chapter has sentiment dict with compound."""
        for chapter in chapters_result.data["chapters"]:
            sent = chapter["sentiment"]
            assert "compound" in sent

    def test_single_chapter_fallback(self):
        """Text with no chapter markers → single chapter spanning all."""
        text = "Just some text. " * 100
        config = merge_config({
            "characters": [],
            "coref_enabled": False,
        })
        results = {}
        tt = TextTilingAnalyzer()
        results["texttiling"] = tt.analyze(text, config)
        results["agency"] = AgencyAnalyzer().analyze(text, config)
        results["dialogue"] = DialogueAnalyzer().analyze(text, config)
        results["sentiment"] = SentimentAnalyzer().analyze(text, config)
        results["silence"] = SilenceAnalyzer().analyze(text, config, context=results)

        analyzer = ChaptersAnalyzer()
        result = analyzer.analyze(text, config, context=results)
        chapters = result.data["chapters"]
        assert len(chapters) == 1

    def test_registers_as_analyzer(self):
        """get_analyzer('chapters') returns a ChaptersAnalyzer."""
        analyzer = get_analyzer("chapters")
        assert isinstance(analyzer, ChaptersAnalyzer)
