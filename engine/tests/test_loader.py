"""Tests for spaCy model loading and document parsing."""

from unittest.mock import MagicMock, patch

import pytest

from lit_engine.nlp.loader import load_spacy, parse_document


# load_spacy is cached — we need to clear the cache between tests
@pytest.fixture(autouse=True)
def clear_cache():
    load_spacy.cache_clear()
    yield
    load_spacy.cache_clear()


class TestLoadSpacy:
    @patch("lit_engine.nlp.loader.spacy.load")
    def test_loads_requested_model(self, mock_load):
        """Loads the requested model when available."""
        mock_nlp = MagicMock()
        mock_load.return_value = mock_nlp
        result = load_spacy("en_core_web_lg")
        mock_load.assert_called_once_with("en_core_web_lg")
        assert result is mock_nlp

    @patch("lit_engine.nlp.loader.spacy.load")
    def test_fallback_to_sm(self, mock_load):
        """Falls back to en_core_web_sm when requested model is missing."""
        mock_nlp_sm = MagicMock()
        mock_load.side_effect = [OSError("not found"), mock_nlp_sm]
        result = load_spacy("en_core_web_lg")
        assert mock_load.call_count == 2
        mock_load.assert_any_call("en_core_web_lg")
        mock_load.assert_any_call("en_core_web_sm")
        assert result is mock_nlp_sm

    @patch("lit_engine.nlp.loader.spacy.load")
    def test_raises_if_no_model(self, mock_load):
        """Raises RuntimeError when no model can be loaded."""
        mock_load.side_effect = OSError("not found")
        with pytest.raises(RuntimeError, match="No spaCy model available"):
            load_spacy("en_core_web_lg")

    @patch("lit_engine.nlp.loader.spacy.load")
    def test_cache_returns_same_instance(self, mock_load):
        """Cached result returns same object on second call."""
        mock_nlp = MagicMock()
        mock_load.return_value = mock_nlp
        first = load_spacy("en_core_web_lg")
        second = load_spacy("en_core_web_lg")
        assert first is second
        mock_load.assert_called_once()


class TestParseDocument:
    @patch("lit_engine.nlp.loader.load_spacy")
    def test_returns_doc(self, mock_load_spacy):
        """parse_document returns result of nlp(text)."""
        mock_nlp = MagicMock()
        mock_nlp.max_length = 1_000_000
        mock_doc = MagicMock()
        mock_nlp.return_value = mock_doc
        mock_load_spacy.return_value = mock_nlp
        result = parse_document("Hello world.")
        mock_nlp.assert_called_once_with("Hello world.")
        assert result is mock_doc

    @patch("lit_engine.nlp.loader.load_spacy")
    def test_adjusts_max_length_for_long_text(self, mock_load_spacy):
        """max_length is increased for text longer than default."""
        mock_nlp = MagicMock()
        mock_nlp.max_length = 100  # artificially low
        mock_nlp.return_value = MagicMock()
        mock_load_spacy.return_value = mock_nlp
        long_text = "x" * 500
        parse_document(long_text)
        assert mock_nlp.max_length >= len(long_text) + 100_000
