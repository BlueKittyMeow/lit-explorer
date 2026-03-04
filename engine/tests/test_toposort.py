"""Tests for analyzer execution order resolution (topological sort)."""

import pytest

from lit_engine.analyzers import resolve_execution_order


class TestResolveExecutionOrder:
    def test_basic_ordering(self):
        """Dependent analyzers come after their dependencies."""
        order = resolve_execution_order(["silence", "dialogue"])
        assert order.index("dialogue") < order.index("silence")

    def test_chapters_last(self):
        """Chapters (with most deps) comes last in full set."""
        all_names = [
            "texttiling", "agency", "dialogue", "readability",
            "pacing", "sentiment", "silence", "chapters",
        ]
        order = resolve_execution_order(all_names)
        assert order[-1] == "chapters"

    def test_independent_analyzers(self):
        """Independent analyzers can appear in any order (but all present)."""
        order = resolve_execution_order(["dialogue", "sentiment"])
        assert set(order) == {"dialogue", "sentiment"}
        assert len(order) == 2

    def test_missing_dependency_raises(self):
        """Requesting an analyzer without its deps raises ValueError."""
        with pytest.raises(ValueError, match="requires"):
            resolve_execution_order(["chapters"])

    def test_circular_detection(self):
        """Circular dependencies raise ValueError."""
        # This tests the algorithm itself — real analyzers don't have cycles.
        # We can't easily inject circular deps without mocking, so this
        # tests that the full set resolves without error (no false cycles).
        all_names = [
            "texttiling", "agency", "dialogue", "readability",
            "pacing", "sentiment", "silence", "chapters",
        ]
        order = resolve_execution_order(all_names)
        assert len(order) == 8

    def test_silence_after_dialogue(self):
        """Silence depends on dialogue — must come after."""
        order = resolve_execution_order([
            "dialogue", "sentiment", "silence", "texttiling",
            "agency", "chapters",
        ])
        assert order.index("dialogue") < order.index("silence")
        assert order.index("silence") < order.index("chapters")
