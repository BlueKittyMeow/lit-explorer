"""Tests for the extract CLI command."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from lit_engine.cli import main


# Needs enough text for TextTiling to produce blocks
EXTRACT_TEXT = (
    "\n"
    "Chapter 1 - Morning\n"
    + (
        "Emil walked to the window and opened it wide. "
        "The morning light streamed through the glass. "
        "He looked around the room and shook his head slowly. "
        "Felix sat at the table reading quietly. "
        "They stood there looking at one another. "
    ) * 20
    + "\n\n"
    "Chapter 2 - Evening\n"
    + (
        "The evening was dark and cold. Felix sat alone. "
        "The room fell silent. He closed his eyes. "
        "Everything felt heavy and sad. "
        "The wind blew through the empty corridor. "
        "Nobody spoke for a long time. "
    ) * 20
)


@pytest.fixture
def txt_file():
    """Create a temporary manuscript file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(EXTRACT_TEXT)
        path = f.name
    yield path
    os.unlink(path)


class TestExtractCommand:
    def test_extract_valid_block(self, txt_file):
        """Extracting block 1 prints block content."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "--- Block 1 ---" in result.output
        assert "Words:" in result.output
        assert "Sentences:" in result.output
        assert "--- Full text ---" in result.output
        assert "--- Sentence breakdown ---" in result.output

    def test_extract_out_of_range_high(self, txt_file):
        """Block ID exceeding total exits with error."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "9999",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code != 0
        assert "out of range" in result.output

    def test_extract_out_of_range_zero(self, txt_file):
        """Block 0 exits with error (1-based)."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "0",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code != 0
        assert "out of range" in result.output

    def test_extract_negative_block(self, txt_file):
        """Negative block ID exits with error."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "-1",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code != 0

    def test_extract_json_flag(self, txt_file):
        """--json produces valid JSON output."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1", "--json",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_extract_json_structure(self, txt_file):
        """JSON output has all required keys."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1", "--json",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        data = json.loads(result.output)
        assert data["block_id"] == 1
        assert "word_count" in data
        assert "sentence_count" in data
        assert "avg_words_per_sentence" in data
        assert "text" in data
        assert "sentences" in data
        assert "parameters" in data
        assert "total_blocks" in data
        assert data["total_blocks"] >= 1

    def test_extract_sentence_breakdown(self, txt_file):
        """Human-readable output shows numbered sentences."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        assert result.exit_code == 0
        # Should have at least [1] in the breakdown
        assert "[1]" in result.output
        assert "words)" in result.output

    def test_extract_json_sentences_have_word_count(self, txt_file):
        """JSON sentences include index and word_count."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1", "--json",
            "--tt-window", "20", "--tt-smoothing", "10",
        ])
        data = json.loads(result.output)
        assert len(data["sentences"]) > 0
        s = data["sentences"][0]
        assert "index" in s
        assert "word_count" in s
        assert "text" in s
        assert s["index"] == 1

    def test_extract_analyze_boundary_equivalence(self, txt_file):
        """Extract block text must match the block boundaries from analyze."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as out_dir:
            # Run analyze to get analysis.json
            result = runner.invoke(main, [
                "analyze", txt_file, "-o", out_dir,
                "--tt-window", "20", "--tt-smoothing", "10",
                "--only", "texttiling",
            ])
            assert result.exit_code == 0, f"analyze failed: {result.output}"

            with open(os.path.join(out_dir, "analysis.json"), "r") as f:
                analysis = json.load(f)

            blocks = analysis["blocks"]
            assert len(blocks) >= 2, "Need at least 2 blocks for meaningful test"

            # Read the manuscript text the same way the CLI does
            with open(os.path.join(out_dir, "manuscript.txt"), "r") as f:
                ms_text = f.read().lstrip("\uFEFF")

            # Check block 1 and last block via extract --json
            for block_id in [1, len(blocks)]:
                ext_result = runner.invoke(main, [
                    "extract", txt_file, "--block", str(block_id), "--json",
                    "--tt-window", "20", "--tt-smoothing", "10",
                ])
                assert ext_result.exit_code == 0, f"extract block {block_id} failed"
                ext_data = json.loads(ext_result.output)

                # Block ID must match
                assert ext_data["block_id"] == block_id

                # Total blocks must agree
                assert ext_data["total_blocks"] == len(blocks)

                # Word count from extract must match analysis.json block
                analysis_block = blocks[block_id - 1]
                assert ext_data["word_count"] == analysis_block["word_count"], (
                    f"Block {block_id}: extract word_count={ext_data['word_count']} "
                    f"!= analysis word_count={analysis_block['word_count']}"
                )

                # Extracted text must match manuscript at analysis.json offsets
                expected_text = ms_text[analysis_block["start_char"]:analysis_block["end_char"]]
                assert ext_data["text"] == expected_text, (
                    f"Block {block_id}: extracted text does not match "
                    f"manuscript[{analysis_block['start_char']}:{analysis_block['end_char']}]"
                )

    def test_extract_custom_parameters(self, txt_file):
        """Custom --tt-window and --tt-smoothing are reflected in JSON output."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "extract", txt_file, "--block", "1", "--json",
            "--tt-window", "15", "--tt-smoothing", "8",
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        data = json.loads(result.output)
        assert data["parameters"]["tt_window"] == 15
        assert data["parameters"]["tt_smoothing"] == 8
