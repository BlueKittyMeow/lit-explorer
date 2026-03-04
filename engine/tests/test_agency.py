"""Tests for the agency analyzer."""

import pytest
import spacy

from lit_engine.analyzers import AnalyzerResult, get_analyzer
from lit_engine.analyzers.agency import AgencyAnalyzer
from lit_engine.config import merge_config


# --- Fixtures ---

AGENCY_TEXT = (
    "Emil walked to the window. He opened the door carefully. "
    "He looked around the room. He shook his head slowly. "
    "Emil saw the garden. He took a deep breath. "
    "Emil felt the cold air. He whispered something softly. "
    "Clara entered the room. She smiled at Emil. "
    "She noticed the open window. She closed it quickly. "
    "Emil was struck by the sudden silence. "
    "Emil was pushed by Clara."
)


@pytest.fixture
def agency_config():
    """Config with manual characters for deterministic testing."""
    return merge_config({
        "characters": ["emil", "clara"],
        "character_genders": {"emil": "male", "clara": "female"},
        "coref_enabled": True,
    })


@pytest.fixture
def agency_result(agency_config):
    """Run the agency analyzer on test text."""
    analyzer = AgencyAnalyzer()
    return analyzer.analyze(AGENCY_TEXT, agency_config)


# --- Tests ---

class TestAgencyAnalyzerBasics:
    def test_result_type(self, agency_result):
        """Returns AnalyzerResult with name='agency'."""
        assert isinstance(agency_result, AnalyzerResult)
        assert agency_result.analyzer_name == "agency"

    def test_output_schema(self, agency_result):
        """Data has 'characters' and 'character_list' keys."""
        assert "characters" in agency_result.data
        assert "character_list" in agency_result.data
        assert isinstance(agency_result.data["characters"], dict)
        assert isinstance(agency_result.data["character_list"], list)

    def test_detection_method(self, agency_result):
        """Manual characters → detection_method is 'manual'."""
        assert agency_result.data["detection_method"] == "manual"

    def test_character_list_matches(self, agency_result):
        """character_list contains the specified characters."""
        assert "emil" in agency_result.data["character_list"]
        assert "clara" in agency_result.data["character_list"]


class TestCharacterSchema:
    """Each character entry has all required fields."""

    REQUIRED_FIELDS = {
        "total_verbs", "active_count", "passive_count",
        "intransitive_count", "via_name", "via_pronoun",
        "verb_domains", "top_verbs", "top_actions",
        "passive_verbs", "passive_agents",
    }

    def test_character_schema(self, agency_result):
        """Each character has all required fields."""
        characters = agency_result.data["characters"]
        for name, data in characters.items():
            for field in self.REQUIRED_FIELDS:
                assert field in data, f"Character {name!r} missing field {field!r}"

    def test_active_passive_sum(self, agency_result):
        """active_count + passive_count == total_verbs for each character."""
        for name, data in agency_result.data["characters"].items():
            assert data["active_count"] + data["passive_count"] == data["total_verbs"], (
                f"Count mismatch for {name}: "
                f"{data['active_count']} + {data['passive_count']} != {data['total_verbs']}"
            )

    def test_verb_domains_sum(self, agency_result):
        """sum(verb_domains.values()) == active_count for each character."""
        for name, data in agency_result.data["characters"].items():
            domain_sum = sum(data["verb_domains"].values())
            assert domain_sum == data["active_count"], (
                f"Domain sum mismatch for {name}: {domain_sum} != {data['active_count']}"
            )


class TestVerbDetails:
    def test_top_verbs_sorted(self, agency_result):
        """top_verbs sorted by count descending."""
        for name, data in agency_result.data["characters"].items():
            counts = [v["count"] for v in data["top_verbs"]]
            assert counts == sorted(counts, reverse=True), (
                f"top_verbs not sorted for {name}"
            )

    def test_top_verbs_have_category(self, agency_result):
        """Each top_verb entry has verb, count, and category."""
        for name, data in agency_result.data["characters"].items():
            for entry in data["top_verbs"]:
                assert "verb" in entry
                assert "count" in entry
                assert "category" in entry

    def test_top_actions_format(self, agency_result):
        """Each action contains ' -> ' separator."""
        for name, data in agency_result.data["characters"].items():
            for entry in data["top_actions"]:
                assert "action" in entry
                assert " -> " in entry["action"], (
                    f"Action {entry['action']!r} missing ' -> ' for {name}"
                )

    def test_via_name_via_pronoun(self, agency_result):
        """via_name + via_pronoun > 0 for characters with verbs."""
        emil = agency_result.data["characters"]["emil"]
        assert emil["via_name"] + emil["via_pronoun"] > 0


class TestPassiveVoice:
    def test_passive_agents_found(self, agency_result):
        """'Emil was given a letter by Clara' → Clara in passive_agents."""
        emil = agency_result.data["characters"]["emil"]
        assert emil["passive_count"] > 0
        agent_names = [a["agent"] for a in emil["passive_agents"]]
        assert "clara" in agent_names, (
            f"Expected 'clara' in passive agents, got {agent_names}"
        )

    def test_passive_without_agent(self):
        """Passive voice without 'by' phrase still records the verb."""
        config = merge_config({
            "characters": ["emil"],
            "character_genders": {"emil": "male"},
            "coref_enabled": True,
        })
        text = "Emil was struck. Emil was pushed."
        analyzer = AgencyAnalyzer()
        result = analyzer.analyze(text, config)
        emil = result.data["characters"]["emil"]
        assert emil["passive_count"] > 0
        # passive_agents might be empty (no "by" phrase)
        passive_verb_names = [v["verb"] for v in emil["passive_verbs"]]
        assert len(passive_verb_names) > 0


class TestStopVerbs:
    def test_stop_verbs_excluded_from_domains(self):
        """Stop verbs (tell, ask, call) don't increment verb_domains."""
        config = merge_config({
            "characters": ["emil"],
            "character_genders": {"emil": "male"},
            "coref_enabled": False,
        })
        # All verbs here are stop verbs
        text = (
            "Emil said something. Emil told a story. "
            "Emil asked a question. Emil called out."
        )
        analyzer = AgencyAnalyzer()
        result = analyzer.analyze(text, config)
        emil = result.data["characters"]["emil"]
        # Stop verbs should NOT appear in verb_domains counts
        domain_sum = sum(emil["verb_domains"].values())
        assert domain_sum == emil["active_count"]
        # via_name should still count (stop verbs are counted for attribution)
        assert emil["via_name"] > 0 or emil["via_pronoun"] > 0


class TestEdgeCases:
    def test_manual_characters(self):
        """config['characters'] overrides auto-detection."""
        config = merge_config({
            "characters": ["emil"],
            "character_genders": {"emil": "male"},
        })
        text = "Emil walked. Clara spoke. Felix ran."
        analyzer = AgencyAnalyzer()
        result = analyzer.analyze(text, config)
        # Only "emil" should be in character_list
        assert result.data["character_list"] == ["emil"]
        assert "clara" not in result.data["characters"]

    def test_zero_verb_character(self):
        """Character with no verbs gets full schema with zeroes."""
        config = merge_config({
            "characters": ["emil", "ghost"],
            "character_genders": {"emil": "male", "ghost": "unknown"},
            "coref_enabled": True,
        })
        text = "Emil walked to the door."
        analyzer = AgencyAnalyzer()
        result = analyzer.analyze(text, config)
        ghost = result.data["characters"]["ghost"]
        assert ghost["total_verbs"] == 0
        assert ghost["active_count"] == 0
        assert ghost["passive_count"] == 0
        assert ghost["intransitive_count"] == 0
        assert ghost["via_name"] == 0
        assert ghost["via_pronoun"] == 0
        assert ghost["verb_domains"] == {}
        assert ghost["top_verbs"] == []
        assert ghost["top_actions"] == []
        assert ghost["passive_verbs"] == []
        assert ghost["passive_agents"] == []

    def test_registers_as_analyzer(self):
        """get_analyzer('agency') returns an AgencyAnalyzer."""
        analyzer = get_analyzer("agency")
        assert isinstance(analyzer, AgencyAnalyzer)
