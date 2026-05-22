"""Unit tests for adk_config module."""

from unittest.mock import patch

from services.config.adk_config import get_agent_config, validate_config


class TestValidateConfig:
    def test_returns_false_when_no_api_key(self):
        with patch("services.config.adk_config.GEMINI_API_KEY", ""):
            assert validate_config() is False

    def test_returns_true_when_api_key_set(self):
        with patch("services.config.adk_config.GEMINI_API_KEY", "test-key"):
            assert validate_config() is True


class TestGetAgentConfig:
    def test_returns_coordinator_config(self):
        config = get_agent_config("TransplantCoordinator")
        assert config["name"] == "TransplantCoordinator"
        assert "model" in config

    def test_returns_medication_advisor_config(self):
        config = get_agent_config("MedicationAdvisor")
        assert config["name"] == "MedicationAdvisor"

    def test_returns_rejection_risk_config(self):
        config = get_agent_config("RejectionRiskAnalyzer")
        assert config["name"] == "RejectionRiskAnalyzer"

    def test_returns_symptom_monitor_config(self):
        config = get_agent_config("SymptomMonitor")
        assert config["name"] == "SymptomMonitor"

    def test_returns_drug_interaction_config(self):
        config = get_agent_config("DrugInteractionChecker")
        assert config["name"] == "DrugInteractionChecker"

    def test_returns_empty_dict_for_unknown_agent(self):
        config = get_agent_config("NonExistentAgent")
        assert config == {}
