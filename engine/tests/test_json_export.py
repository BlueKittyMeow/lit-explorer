"""Tests for JSON export and manifest generation."""

import json
import os
from datetime import datetime

import pytest
from lit_engine.output.json_export import (
    build_manifest,
    copy_manuscript,
    slugify,
    write_analysis,
    write_json,
    write_manifest,
    write_silence,
)


class TestSlugify:
    def test_basic(self):
        """Title to slug conversion."""
        assert slugify("The Specimen V2") == "the-specimen-v2"

    def test_special_chars(self):
        """Accented and special characters stripped."""
        result = slugify("Café Union")
        assert result == "caf-union" or result == "cafe-union"

    def test_underscores(self):
        """Underscores become hyphens."""
        assert slugify("the_specimen") == "the-specimen"

    def test_multiple_spaces(self):
        """Multiple spaces collapse to single hyphen."""
        assert slugify("The   Big   Test") == "the-big-test"

    def test_leading_trailing(self):
        """Leading/trailing special chars stripped."""
        assert slugify("--hello--") == "hello"


class TestWriteJson:
    def test_output_dir_created(self, tmp_path):
        """Creates directory if it doesn't exist."""
        output_dir = str(tmp_path / "nested" / "deep" / "dir")
        path = write_json(output_dir, "test.json", {"key": "value"})
        assert os.path.exists(path)
        with open(path) as f:
            assert json.load(f) == {"key": "value"}

    def test_analysis_roundtrip(self, tmp_path):
        """Write then read produces identical data."""
        data = {
            "parameters": {"w": 40, "k": 20},
            "total_blocks": 1,
            "blocks": [{"id": 1, "metrics": {"mattr": 0.75}}],
            "notable": {"longest_sentences": [1]},
        }
        output_dir = str(tmp_path / "analysis")
        path = write_analysis(output_dir, data)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data

    def test_unicode_preserved(self, tmp_path):
        """Unicode characters survive JSON roundtrip."""
        data = {"text": "Caf\u00e9 \u2014 \u201chello\u201d"}
        path = write_json(str(tmp_path), "unicode.json", data)
        with open(path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["text"] == "Caf\u00e9 \u2014 \u201chello\u201d"


class TestManifest:
    def test_manifest_schema(self):
        """All required fields present in built manifest."""
        manifest = build_manifest(
            title="The Specimen",
            slug="the-specimen",
            source_file="/path/to/the_specimen.txt",
            word_count=43000,
            char_count=240000,
            character_list=["emil", "felix"],
            analyzers_run=["texttiling"],
            parameters={"texttiling_w": 40},
        )
        required = {
            "title", "slug", "source_file", "analyzed_at", "engine_version",
            "word_count", "char_count", "chapter_count", "character_list",
            "analyzers_run", "parameters", "warnings",
        }
        assert set(manifest.keys()) >= required

    def test_manifest_timestamp(self):
        """analyzed_at is valid ISO 8601 with timezone."""
        manifest = build_manifest(
            title="Test", slug="test", source_file="test.txt",
            word_count=100, char_count=500, character_list=[],
            analyzers_run=[], parameters={},
        )
        ts = manifest["analyzed_at"]
        # Should parse without error
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo is not None  # timezone-aware

    def test_manifest_warnings(self):
        """Warnings list persisted in manifest."""
        manifest = build_manifest(
            title="Test", slug="test", source_file="test.txt",
            word_count=100, char_count=500, character_list=[],
            analyzers_run=[], parameters={},
            warnings=["Something went wrong"],
        )
        assert manifest["warnings"] == ["Something went wrong"]

    def test_manifest_warnings_default_empty(self):
        """Warnings default to empty list."""
        manifest = build_manifest(
            title="Test", slug="test", source_file="test.txt",
            word_count=100, char_count=500, character_list=[],
            analyzers_run=[], parameters={},
        )
        assert manifest["warnings"] == []

    def test_manifest_source_file_basename(self):
        """source_file stores basename only, not full path."""
        manifest = build_manifest(
            title="Test", slug="test",
            source_file="/home/user/docs/manuscript.txt",
            word_count=100, char_count=500, character_list=[],
            analyzers_run=[], parameters={},
        )
        assert manifest["source_file"] == "manuscript.txt"

    def test_write_manifest(self, tmp_path):
        """write_manifest creates manifest.json on disk."""
        manifest = build_manifest(
            title="Test", slug="test", source_file="test.txt",
            word_count=100, char_count=500, character_list=[],
            analyzers_run=[], parameters={},
        )
        path = write_manifest(str(tmp_path), manifest)
        assert os.path.basename(path) == "manifest.json"
        with open(path) as f:
            loaded = json.load(f)
        assert loaded["title"] == "Test"


class TestWriteSilence:
    def test_silence_roundtrip(self, tmp_path):
        """Write then read produces identical silence data."""
        data = {
            "gaps": [{"start_char": 0, "end_char": 100, "word_count": 15}],
            "longest_silence": {"word_count": 15, "position": 0.0, "preview": "Some text..."},
            "avg_gap_words": 15.0,
            "total_gaps": 1,
        }
        path = write_silence(str(tmp_path), data)
        with open(path) as f:
            loaded = json.load(f)
        assert loaded == data
        assert os.path.basename(path) == "silence.json"


class TestCopyManuscript:
    def test_manuscript_copied(self, tmp_path):
        """copy_manuscript creates manuscript.txt in output dir."""
        # Create a source file
        source = tmp_path / "source.txt"
        source.write_text("Hello, world!")
        output_dir = str(tmp_path / "output")
        dest = copy_manuscript(str(source), output_dir)
        assert os.path.exists(dest)
        assert os.path.basename(dest) == "manuscript.txt"
        with open(dest) as f:
            assert f.read() == "Hello, world!"
