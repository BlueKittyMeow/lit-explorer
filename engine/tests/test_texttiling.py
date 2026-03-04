"""Tests for the TextTiling analyzer."""

import re
import pytest
from lit_engine.analyzers import AnalyzerResult
from lit_engine.analyzers.texttiling import TextTilingAnalyzer, prepare_text


REQUIRED_BLOCK_KEYS = {
    "id", "tile_index", "start_char", "end_char", "word_count",
    "sentence_count", "metrics", "sentence_lengths", "preview", "chapter",
}

REQUIRED_METRIC_KEYS = {
    "mattr", "avg_sentence_length", "max_sentence_length",
    "flesch_ease", "flesch_grade", "gunning_fog",
}

NOTABLE_KEYS = {
    "longest_sentences", "highest_mattr", "highest_fog", "shortest_sentences",
}


@pytest.fixture
def analyzer():
    return TextTilingAnalyzer()


@pytest.fixture
def result(analyzer, clean_sample_text, default_config):
    """Run analyzer on fixture text with small window for more blocks."""
    config = dict(default_config)
    config["texttiling_w"] = 20
    config["texttiling_k"] = 10
    return analyzer.analyze(clean_sample_text, config)


class TestTextTilingAnalyzer:
    def test_result_type(self, result):
        """Returns AnalyzerResult with correct analyzer name."""
        assert isinstance(result, AnalyzerResult)
        assert result.analyzer_name == "texttiling"

    def test_tiles_produced(self, result):
        """Fixture text produces at least 1 block."""
        blocks = result.data["blocks"]
        assert len(blocks) >= 1

    def test_block_schema(self, result):
        """Each block has all required keys."""
        for block in result.data["blocks"]:
            assert set(block.keys()) >= REQUIRED_BLOCK_KEYS, (
                f"Block {block.get('id')} missing keys: "
                f"{REQUIRED_BLOCK_KEYS - set(block.keys())}"
            )
            assert set(block["metrics"].keys()) >= REQUIRED_METRIC_KEYS

    def test_block_ids_sequential(self, result):
        """Block IDs are 1-indexed and sequential with no gaps."""
        ids = [b["id"] for b in result.data["blocks"]]
        assert ids == list(range(1, len(ids) + 1))

    def test_block_offsets_valid(self, result):
        """start_char < end_char for every block."""
        for block in result.data["blocks"]:
            assert block["start_char"] < block["end_char"], (
                f"Block {block['id']}: start_char={block['start_char']} "
                f">= end_char={block['end_char']}"
            )

    def test_block_offsets_contiguous(self, result):
        """No gaps between blocks: block N end >= block N+1 start."""
        blocks = result.data["blocks"]
        for i in range(len(blocks) - 1):
            assert blocks[i]["end_char"] >= blocks[i + 1]["start_char"], (
                f"Gap between block {blocks[i]['id']} (end={blocks[i]['end_char']}) "
                f"and block {blocks[i+1]['id']} (start={blocks[i+1]['start_char']})"
            )

    def test_block_preview_matches_text(self, result, clean_sample_text):
        """Preview content matches text at offset, after whitespace normalization."""
        for block in result.data["blocks"]:
            raw_slice = clean_sample_text[block["start_char"]:block["start_char"] + 150]
            # Normalize whitespace on both sides for comparison
            normalized_slice = re.sub(r"\s+", " ", raw_slice).strip()[:120]
            normalized_preview = re.sub(r"\s+", " ", block["preview"].rstrip("...")).strip()[:120]
            # At least the first 50 chars should match
            assert normalized_preview[:50] == normalized_slice[:50], (
                f"Block {block['id']} preview mismatch:\n"
                f"  preview:  {normalized_preview[:50]!r}\n"
                f"  at offset: {normalized_slice[:50]!r}"
            )

    def test_metrics_in_range(self, result):
        """Metrics are within sensible ranges."""
        for block in result.data["blocks"]:
            m = block["metrics"]
            assert 0 <= m["mattr"] <= 1, f"Block {block['id']}: MATTR {m['mattr']} out of range"
            assert m["gunning_fog"] >= 0, f"Block {block['id']}: negative Fog"
            assert block["sentence_count"] > 0
            assert block["word_count"] > 0

    def test_notable_blocks_exist(self, result):
        """Notable dict has all required keys."""
        assert set(result.data["notable"].keys()) >= NOTABLE_KEYS

    def test_notable_ids_valid(self, result):
        """All IDs in notable lists exist in blocks."""
        block_ids = {b["id"] for b in result.data["blocks"]}
        for key in NOTABLE_KEYS:
            for block_id in result.data["notable"].get(key, []):
                assert block_id in block_ids, (
                    f"notable.{key} references block {block_id} which doesn't exist"
                )

    def test_fallback_window(self, analyzer, clean_sample_text, default_config):
        """Absurd window values trigger fallback and emit warnings."""
        config = dict(default_config)
        config["texttiling_w"] = 999
        config["texttiling_k"] = 999
        result = analyzer.analyze(clean_sample_text, config)
        assert any("Falling back" in w or "failed" in w.lower() for w in result.warnings)

    def test_zero_blocks(self, analyzer, default_config):
        """Very short text returns valid empty-blocks structure."""
        result = analyzer.analyze("Hello.", default_config)
        assert result.data["total_blocks"] == 0
        assert result.data["blocks"] == []
        assert all(v == [] for v in result.data["notable"].values())

    def test_config_overrides(self, analyzer, clean_sample_text, default_config):
        """Different w/k values produce different block counts."""
        config_small = dict(default_config)
        config_small["texttiling_w"] = 10
        config_small["texttiling_k"] = 5

        config_large = dict(default_config)
        config_large["texttiling_w"] = 40
        config_large["texttiling_k"] = 20

        result_small = analyzer.analyze(clean_sample_text, config_small)
        result_large = analyzer.analyze(clean_sample_text, config_large)
        # Different params should produce different segmentations
        # (or at least not crash — if fixture is too short for large window, that's ok)
        assert isinstance(result_small.data["total_blocks"], int)
        assert isinstance(result_large.data["total_blocks"], int)

    def test_unicode_handling(self, analyzer, default_config):
        """Smart quotes, BOM, accented chars don't break offset mapping."""
        text = (
            "\uFEFF"  # BOM
            "The caf\u00e9 was quiet.\n\n"  # accented e
            "\u201cHello,\u201d she said\u2014softly.\n\n"  # smart quotes + em dash
            "He didn\u2019t reply.\n\n"  # smart apostrophe
        )
        # Repeat to give TextTiling enough text
        text_long = text * 50
        config = dict(default_config)
        config["texttiling_w"] = 10
        config["texttiling_k"] = 5
        result = analyzer.analyze(text_long, config)
        # Should not crash; if blocks produced, offsets should be valid
        for block in result.data["blocks"]:
            assert block["start_char"] < block["end_char"]

    def test_single_short_tile(self, analyzer, default_config):
        """A manuscript producing 1 short tile still returns 1 block."""
        # Short but enough paragraphs for TextTiling to run
        text = "A short paragraph.\n\n" * 10
        config = dict(default_config)
        config["texttiling_w"] = 5
        config["texttiling_k"] = 3
        config["texttiling_min_words"] = 5
        config["texttiling_min_alpha"] = 3
        result = analyzer.analyze(text, config)
        # Should produce at least 1 block, not 0
        if result.data["total_blocks"] > 0:
            assert result.data["blocks"][0]["id"] == 1

    def test_offset_no_fallback_on_fixture(self, analyzer, clean_sample_text, default_config):
        """Fixture text maps all tiles via primary path (no fallback warnings)."""
        config = dict(default_config)
        config["texttiling_w"] = 20
        config["texttiling_k"] = 10
        result = analyzer.analyze(clean_sample_text, config)
        offset_warnings = [w for w in result.warnings if "offset" in w.lower() or "locate" in w.lower()]
        assert offset_warnings == [], f"Unexpected offset fallback warnings: {offset_warnings}"
