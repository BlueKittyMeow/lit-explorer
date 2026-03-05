"""Tests for analyzer execution order resolution (topological sort)."""

import pytest
from unittest.mock import patch

from lit_engine.analyzers import Analyzer, AnalyzerResult, resolve_execution_order, _REGISTRY


class TestResolveExecutionOrder:
    def test_basic_ordering(self):
        """Dependent analyzers come after their dependencies."""
        order = resolve_execution_order(["silence", "dialogue"])
        assert order.index("dialogue") < order.index("silence")

    def test_chapters_after_deps(self):
        """Chapters comes after all its dependencies."""
        all_names = [
            "texttiling", "agency", "dialogue", "readability",
            "pacing", "sentiment", "silence", "chapters",
        ]
        order = resolve_execution_order(all_names)
        ch_idx = order.index("chapters")
        for dep in ["texttiling", "agency", "dialogue", "sentiment"]:
            assert order.index(dep) < ch_idx, f"{dep} should come before chapters"

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

        class FakeA(Analyzer):
            name = "_cycle_a"
            description = "test"
            def requires(self):
                return ["_cycle_b"]
            def analyze(self, text, config, context=None):
                return AnalyzerResult(analyzer_name=self.name, data={})

        class FakeB(Analyzer):
            name = "_cycle_b"
            description = "test"
            def requires(self):
                return ["_cycle_a"]
            def analyze(self, text, config, context=None):
                return AnalyzerResult(analyzer_name=self.name, data={})

        patched = {**_REGISTRY, "_cycle_a": FakeA, "_cycle_b": FakeB}
        with patch.dict("lit_engine.analyzers._REGISTRY", patched):
            with pytest.raises(ValueError, match="Circular dependency"):
                resolve_execution_order(["_cycle_a", "_cycle_b"])

    def test_full_set_resolves(self):
        """Full analyzer set resolves without false cycle detection."""
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
