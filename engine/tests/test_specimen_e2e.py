"""End-to-end validation against The Specimen manuscript."""

import json
import os

import pytest
from click.testing import CliRunner

from lit_engine.cli import main

SPECIMEN_PATH = os.path.expanduser("~/Documents/lit-analysis/the_specimen.txt")
SPECIMEN_EXISTS = os.path.exists(SPECIMEN_PATH)


@pytest.mark.slow
@pytest.mark.skipif(not SPECIMEN_EXISTS, reason="Specimen manuscript not found")
class TestSpecimenE2E:
    """Full pipeline validation against The Specimen."""

    @pytest.fixture(scope="class")
    def specimen_output(self, tmp_path_factory):
        """Run full pipeline once, share output across all tests in class."""
        tmpdir = tmp_path_factory.mktemp("specimen")
        out_dir = str(tmpdir / "output")
        runner = CliRunner()
        result = runner.invoke(main, [
            "analyze", SPECIMEN_PATH,
            "--output", out_dir,
        ])
        assert result.exit_code == 0, f"Pipeline failed:\n{result.output}"
        return out_dir

    def test_all_output_files_exist(self, specimen_output):
        """All 6 output files are written."""
        expected = [
            "analysis.json", "characters.json", "chapters.json",
            "sentiment.json", "manifest.json", "manuscript.txt",
        ]
        for fname in expected:
            path = os.path.join(specimen_output, fname)
            assert os.path.exists(path), f"Missing: {fname}"

    def test_all_json_valid(self, specimen_output):
        """All JSON files parse without error."""
        for fname in ["analysis.json", "characters.json", "chapters.json",
                       "sentiment.json", "manifest.json"]:
            path = os.path.join(specimen_output, fname)
            with open(path) as f:
                data = json.load(f)
            assert isinstance(data, dict), f"{fname} is not a dict"

    def test_chapter_count(self, specimen_output):
        """The Specimen has 16 chapters."""
        with open(os.path.join(specimen_output, "manifest.json")) as f:
            manifest = json.load(f)
        assert manifest["chapter_count"] == 16

    def test_characters_detected(self, specimen_output):
        """Auto-detection finds Emil and Felix."""
        with open(os.path.join(specimen_output, "characters.json")) as f:
            data = json.load(f)
        character_names = list(data["characters"].keys())
        assert "emil" in character_names
        assert "felix" in character_names

    def test_sentiment_arc_length(self, specimen_output):
        """Sentiment arc has a reasonable number of points."""
        with open(os.path.join(specimen_output, "sentiment.json")) as f:
            data = json.load(f)
        arc = data["arc"]
        assert len(arc) > 100
        assert len(arc) < 10000

    def test_block_count_reasonable(self, specimen_output):
        """Analysis produces a reasonable number of blocks."""
        with open(os.path.join(specimen_output, "analysis.json")) as f:
            data = json.load(f)
        blocks = data["blocks"]
        assert len(blocks) > 50
        assert len(blocks) < 1000

    def test_manifest_analyzers_complete(self, specimen_output):
        """All 8 analyzers recorded in manifest."""
        with open(os.path.join(specimen_output, "manifest.json")) as f:
            manifest = json.load(f)
        expected_analyzers = {
            "texttiling", "agency", "dialogue", "readability",
            "pacing", "sentiment", "silence", "chapters",
        }
        assert set(manifest["analyzers_run"]) == expected_analyzers

    def test_chapters_have_titles(self, specimen_output):
        """All chapters have non-empty titles."""
        with open(os.path.join(specimen_output, "chapters.json")) as f:
            data = json.load(f)
        for ch in data["chapters"]:
            assert ch["title"], f"Chapter {ch['number']} has no title"
