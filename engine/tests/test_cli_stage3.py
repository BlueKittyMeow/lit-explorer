"""Tests for CLI Stage 3 integration — JSON output routing and enrichment."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from lit_engine.cli import main


# Fixture text with chapters and dialogue for full pipeline
CLI_TEXT = (
    "\n"
    "Chapter 1 - Morning\n"
    + (
        "Emil walked to the window. He opened the door carefully. "
        '\u201cGood morning,\u201d he said. '
        "The morning light was beautiful and warm. "
        "Felix sat at the table reading quietly. "
    ) * 15
    + "\n\n"
    "Chapter 2 - Evening\n"
    + (
        "The evening was dark and cold. Felix sat alone. "
        '\u201cGoodnight,\u201d Felix whispered. '
        "The room fell silent. He closed his eyes. "
        "Everything felt heavy and sad. "
    ) * 15
)


@pytest.fixture
def cli_output():
    """Run full CLI pipeline and return output directory."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = os.path.join(tmpdir, "test_novel.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(CLI_TEXT)

        out_dir = os.path.join(tmpdir, "output")
        result = runner.invoke(main, [
            "analyze", txt_path,
            "--output", out_dir,
            "--characters", "emil,felix",
        ])
        assert result.exit_code == 0, f"CLI failed: {result.output}"

        yield out_dir


class TestCliStage3:
    def test_all_json_files_written(self, cli_output):
        """All 4 JSON files + manifest + manuscript are written."""
        expected = [
            "analysis.json", "characters.json", "chapters.json",
            "sentiment.json", "manifest.json", "manuscript.txt",
        ]
        for fname in expected:
            path = os.path.join(cli_output, fname)
            assert os.path.exists(path), f"Missing: {fname}"

    def test_manifest_chapter_count(self, cli_output):
        """Manifest includes chapter_count from chapters analyzer."""
        with open(os.path.join(cli_output, "manifest.json")) as f:
            manifest = json.load(f)
        assert "chapter_count" in manifest
        assert manifest["chapter_count"] >= 2

    def test_analysis_json_has_chapter_fields(self, cli_output):
        """analysis.json blocks have chapter field populated."""
        with open(os.path.join(cli_output, "analysis.json")) as f:
            data = json.load(f)
        blocks = data["blocks"]
        assert len(blocks) > 0
        for block in blocks:
            assert "chapter" in block
            assert block["chapter"] is not None

    def test_readability_enrichment_applied(self, cli_output):
        """analysis.json blocks have extended readability metrics."""
        with open(os.path.join(cli_output, "analysis.json")) as f:
            data = json.load(f)
        block = data["blocks"][0]
        metrics = block["metrics"]
        # Original 3 from texttiling
        assert "flesch_ease" in metrics
        assert "gunning_fog" in metrics
        # Extended 3 from readability
        assert "coleman_liau" in metrics
        assert "smog" in metrics
        assert "ari" in metrics

    def test_chapters_json_schema(self, cli_output):
        """chapters.json has chapters list with required fields."""
        with open(os.path.join(cli_output, "chapters.json")) as f:
            data = json.load(f)
        assert "chapters" in data
        assert len(data["chapters"]) >= 2
        ch = data["chapters"][0]
        assert "number" in ch
        assert "title" in ch
        assert "word_count" in ch
        assert "dialogue_ratio" in ch

    def test_sentiment_json_schema(self, cli_output):
        """sentiment.json has method, arc, extremes."""
        with open(os.path.join(cli_output, "sentiment.json")) as f:
            data = json.load(f)
        assert data["method"] == "vader"
        assert "arc" in data
        assert "extremes" in data
        assert len(data["arc"]) > 0
