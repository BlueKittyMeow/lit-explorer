"""Tests for Stage 4 CLI additions: rerun command and error handling."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from lit_engine.cli import main, _expand_with_deps


# Fixture text — enough for full pipeline
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
def txt_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(CLI_TEXT)
        path = f.name
    yield path
    os.unlink(path)


class TestExpandWithDeps:
    def test_no_deps(self):
        """Analyzer with no deps returns just itself."""
        result = _expand_with_deps("texttiling")
        assert "texttiling" in result
        assert len(result) == 1

    def test_transitive_deps(self):
        """chapters expands to include all transitive deps."""
        result = _expand_with_deps("chapters")
        expected = {"texttiling", "agency", "dialogue", "sentiment", "chapters"}
        assert set(result) == expected

    def test_unknown_analyzer_raises(self):
        """Unknown analyzer name raises ClickException."""
        import click
        with pytest.raises(click.exceptions.ClickException, match="Unknown analyzer"):
            _expand_with_deps("nonexistent")


class TestRerunCommand:
    def test_rerun_single_analyzer(self, txt_file):
        """rerun texttiling produces analysis.json."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            result = runner.invoke(main, [
                "rerun", "texttiling", txt_file,
                "--output", out_dir,
            ])
            assert result.exit_code == 0, f"Failed: {result.output}"
            assert os.path.exists(os.path.join(out_dir, "analysis.json"))

    def test_rerun_with_deps(self, txt_file):
        """rerun chapters runs all 6 required analyzers."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            result = runner.invoke(main, [
                "rerun", "chapters", txt_file,
                "--output", out_dir,
                "--characters", "emil,felix",
            ])
            assert result.exit_code == 0, f"Failed: {result.output}"
            # chapters + its deps should produce all output files
            assert os.path.exists(os.path.join(out_dir, "chapters.json"))
            assert os.path.exists(os.path.join(out_dir, "analysis.json"))
            assert os.path.exists(os.path.join(out_dir, "sentiment.json"))

    def test_rerun_unknown_analyzer(self, txt_file):
        """rerun with unknown analyzer exits with error."""
        runner = CliRunner()
        result = runner.invoke(main, ["rerun", "nonexistent", txt_file])
        assert result.exit_code != 0

    def test_rerun_produces_manifest(self, txt_file):
        """rerun writes manifest.json with correct analyzers_run."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            result = runner.invoke(main, [
                "rerun", "readability", txt_file,
                "--output", out_dir,
            ])
            assert result.exit_code == 0, f"Failed: {result.output}"
            with open(os.path.join(out_dir, "manifest.json")) as f:
                manifest = json.load(f)
            # readability requires texttiling
            assert "texttiling" in manifest["analyzers_run"]
            assert "readability" in manifest["analyzers_run"]


class TestAnalyzerErrorHandling:
    def test_analyzer_exception_skipped(self, txt_file):
        """Pipeline continues when an analyzer raises an exception."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            # Monkeypatch readability to raise
            with patch(
                "lit_engine.analyzers.readability.ReadabilityAnalyzer.analyze",
                side_effect=RuntimeError("test failure"),
            ):
                result = runner.invoke(main, [
                    "analyze", txt_file,
                    "--output", out_dir,
                    "--characters", "emil,felix",
                ])
            assert result.exit_code == 0, f"CLI crashed: {result.output}"
            # analysis.json should still exist (from texttiling)
            assert os.path.exists(os.path.join(out_dir, "analysis.json"))

    def test_failed_analyzer_in_warnings(self, txt_file):
        """Manifest warnings include the failure message."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            with patch(
                "lit_engine.analyzers.readability.ReadabilityAnalyzer.analyze",
                side_effect=RuntimeError("test failure"),
            ):
                result = runner.invoke(main, [
                    "analyze", txt_file,
                    "--output", out_dir,
                    "--characters", "emil,felix",
                ])
            with open(os.path.join(out_dir, "manifest.json")) as f:
                manifest = json.load(f)
            warning_text = " ".join(manifest["warnings"])
            assert "readability" in warning_text.lower()
            assert "test failure" in warning_text

    def test_downstream_runs_after_failure(self, txt_file):
        """If dialogue fails, sentiment (independent) still runs."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            with patch(
                "lit_engine.analyzers.dialogue.DialogueAnalyzer.analyze",
                side_effect=RuntimeError("dialogue broken"),
            ):
                result = runner.invoke(main, [
                    "analyze", txt_file,
                    "--output", out_dir,
                    "--only", "texttiling,dialogue,sentiment",
                ])
            assert result.exit_code == 0, f"CLI crashed: {result.output}"
            # sentiment should still run (no dependency on dialogue)
            assert os.path.exists(os.path.join(out_dir, "sentiment.json"))

    def test_all_analyzers_fail_exits_nonzero(self, txt_file):
        """Exit code 1 when every requested analyzer fails."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            with patch(
                "lit_engine.analyzers.texttiling.TextTilingAnalyzer.analyze",
                side_effect=RuntimeError("total failure"),
            ):
                result = runner.invoke(main, [
                    "analyze", txt_file,
                    "--output", out_dir,
                    "--only", "texttiling",
                ])
            assert result.exit_code != 0
            assert "All analyzers failed" in result.output

    def test_error_message_printed(self, txt_file):
        """Error message appears in CLI output."""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = os.path.join(tmpdir, "output")
            with patch(
                "lit_engine.analyzers.readability.ReadabilityAnalyzer.analyze",
                side_effect=RuntimeError("kaboom"),
            ):
                result = runner.invoke(main, [
                    "analyze", txt_file,
                    "--output", out_dir,
                    "--only", "texttiling,readability",
                ])
            assert "ERROR" in result.output
            assert "kaboom" in result.output
