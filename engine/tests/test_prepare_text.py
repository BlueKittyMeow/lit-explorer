"""Tests for text preparation and offset mapping."""

import pytest
from lit_engine.analyzers.texttiling import prepare_text


class TestPrepareText:
    def test_bom_stripped(self):
        """BOM at start is removed, offset map is correct."""
        raw = "\uFEFFHello world"
        clean, formatted, offset_map = prepare_text(raw)
        assert clean == "Hello world"
        assert "\uFEFF" not in clean

    def test_double_bom(self):
        """Multiple BOMs stripped (matches real manuscript pattern)."""
        raw = "\uFEFF\uFEFFHello"
        clean, formatted, offset_map = prepare_text(raw)
        assert clean == "Hello"

    def test_newlines_doubled(self):
        """Single \\n becomes \\n\\n in formatted text."""
        raw = "Line one\nLine two"
        clean, formatted, offset_map = prepare_text(raw)
        assert "\n\n" in formatted
        assert formatted.count("\n") == 2  # original \n + inserted \n

    def test_offset_map_length(self):
        """offset_map length matches len(formatted_text)."""
        raw = "Hello\nWorld\nFoo"
        clean, formatted, offset_map = prepare_text(raw)
        assert len(offset_map) == len(formatted)

    def test_offset_map_identity_no_newlines(self):
        """Text without newlines: map is identity [0,1,2,...]."""
        raw = "Hello world"
        clean, formatted, offset_map = prepare_text(raw)
        assert offset_map == list(range(len(clean)))
        assert formatted == clean  # no newlines, no change

    def test_roundtrip_via_map(self):
        """For each index in formatted, clean[offset_map[i]] is the right character."""
        raw = "\uFEFFHello\nWorld\nFoo bar"
        clean, formatted, offset_map = prepare_text(raw)

        for i, ch in enumerate(formatted):
            clean_idx = offset_map[i]
            # Inserted newlines map to the preceding original position
            # The original char at that index is \n
            if ch == "\n" and i > 0 and formatted[i - 1] == "\n":
                # This is the inserted extra newline
                assert clean[clean_idx] == "\n"
            else:
                assert clean[clean_idx] == ch

    def test_unicode_preserved(self):
        """Smart quotes, accented chars, em dashes survive preparation."""
        raw = "\u201cHello\u201d she said\u2014caf\u00e9"
        clean, formatted, offset_map = prepare_text(raw)
        assert "\u201c" in clean
        assert "\u201d" in clean
        assert "\u2014" in clean
        assert "\u00e9" in clean
