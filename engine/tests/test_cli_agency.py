"""Tests for CLI agency integration and spaCy label compatibility."""

import json
import os

import pytest
import spacy
from click.testing import CliRunner

from lit_engine.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_text_path():
    return os.path.join(os.path.dirname(__file__), "fixtures", "sample_text.txt")


class TestCliCharactersFlag:
    def test_characters_flag_parsed(self, runner, sample_text_path, tmp_path):
        """--characters 'marguerite,thomas' runs without error."""
        output_dir = str(tmp_path / "output")
        result = runner.invoke(main, [
            "analyze", sample_text_path,
            "--output", output_dir,
            "--characters", "marguerite,thomas",
            "--only", "agency",
        ])
        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_characters_json_written(self, runner, sample_text_path, tmp_path):
        """Running agency analyzer writes characters.json."""
        output_dir = str(tmp_path / "output")
        result = runner.invoke(main, [
            "analyze", sample_text_path,
            "--output", output_dir,
            "--characters", "marguerite,thomas",
            "--only", "agency",
        ])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        characters_path = os.path.join(output_dir, "characters.json")
        assert os.path.exists(characters_path), "characters.json not created"
        with open(characters_path) as f:
            data = json.load(f)
        # Must match spec schema: top-level "characters" key only
        assert "characters" in data
        assert "character_list" not in data, "Metadata should not leak into characters.json"

    def test_manifest_character_list(self, runner, sample_text_path, tmp_path):
        """Manifest includes character_list when agency runs."""
        output_dir = str(tmp_path / "output")
        result = runner.invoke(main, [
            "analyze", sample_text_path,
            "--output", output_dir,
            "--characters", "marguerite,thomas",
            "--only", "agency",
        ])
        assert result.exit_code == 0, f"CLI failed: {result.output}"
        manifest_path = os.path.join(output_dir, "manifest.json")
        assert os.path.exists(manifest_path)
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "marguerite" in manifest["character_list"]
        assert "thomas" in manifest["character_list"]


class TestSpacyLabelCompatibility:
    def test_passive_label_compatibility(self):
        """en_core_web_lg parser labels include nsubjpass."""
        try:
            nlp = spacy.load("en_core_web_lg")
        except OSError:
            pytest.skip("en_core_web_lg not installed")
        parser = nlp.get_pipe("parser")
        labels = parser.labels
        assert "nsubjpass" in labels, (
            f"nsubjpass not in parser labels: {sorted(labels)}"
        )
        assert "agent" in labels, (
            f"agent not in parser labels: {sorted(labels)}"
        )
