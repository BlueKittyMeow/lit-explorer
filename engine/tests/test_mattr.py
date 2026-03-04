"""Tests for the MATTR (Moving Average Type-Token Ratio) function."""

import pytest
from lit_engine.analyzers.texttiling import mattr


class TestMATTR:
    def test_basic(self):
        """Known input/output for a small token list."""
        tokens = ["a", "b", "a", "b"]
        # window=2: positions [a,b]=1.0, [b,a]=1.0, [a,b]=1.0 → mean 1.0
        result = mattr(tokens, window_length=2)
        assert result == pytest.approx(1.0)

    def test_empty(self):
        """Empty token list returns 0.0."""
        assert mattr([], window_length=50) == 0.0

    def test_uniform(self):
        """All same token returns low value (1/window for each position)."""
        tokens = ["the"] * 100
        result = mattr(tokens, window_length=50)
        assert result == pytest.approx(1 / 50, abs=0.001)

    def test_all_unique(self):
        """All unique tokens returns value close to 1.0."""
        tokens = [f"word{i}" for i in range(100)]
        result = mattr(tokens, window_length=50)
        assert result == pytest.approx(1.0)

    def test_short_text(self):
        """Text shorter than window returns naive TTR."""
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        result = mattr(tokens, window_length=50)
        # 5 unique / 6 total = 0.833...
        assert result == pytest.approx(5 / 6, abs=0.001)

    def test_window_equals_length(self):
        """When len(tokens) == window, returns single TTR value."""
        tokens = ["a", "b", "c", "d", "e"]
        result = mattr(tokens, window_length=5)
        # Only one window position: 5 unique / 5 = 1.0
        assert result == pytest.approx(1.0)
