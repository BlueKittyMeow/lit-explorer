"""Shared test fixtures and NLTK data setup."""

import os
import pytest
import nltk


def pytest_configure(config):
    """Ensure NLTK data is available before any tests run."""
    for resource in ("punkt_tab", "stopwords"):
        try:
            nltk.data.find(
                f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}"
            )
        except LookupError:
            nltk.download(resource, quiet=True)


@pytest.fixture
def sample_text():
    """Load the test fixture text."""
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_text.txt")
    with open(fixture_path, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def clean_sample_text(sample_text):
    """Load fixture text with BOM stripped."""
    return sample_text.lstrip("\uFEFF")


@pytest.fixture
def default_config():
    """Return default config for testing."""
    from lit_engine.config import DEFAULT_CONFIG

    return dict(DEFAULT_CONFIG)
