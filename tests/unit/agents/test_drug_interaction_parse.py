"""Tests for DrugInteractionCheckerAgent._parse_agent_response with JSON inputs."""

from unittest.mock import patch


class TestDrugInteractionParseWithJson:
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_with_valid_json(self, mock_types, mock_agent_class):
        from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

        agent = DrugInteractionCheckerAgent(api_key="test_key")
        response = """```json
{
    "has_interaction": true,
    "severity": "severe",
    "interactions": [{"drug1": "tacrolimus", "drug2": "grapefruit", "severity": "severe"}],
    "mechanism": "CYP3A4 inhibition",
    "clinical_effect": "Increased tacrolimus levels",
    "recommendation": "Avoid grapefruit",
    "confidence": 0.95
}
```"""

        result = agent._parse_agent_response(response)

        assert result["has_interaction"] is True
        assert result["severity"] == "severe"
        assert result["mechanism"] == "CYP3A4 inhibition"
        assert result["confidence"] == 0.95

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_severity_from_interactions(self, mock_types, mock_agent_class):
        from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

        agent = DrugInteractionCheckerAgent(api_key="test_key")
        response = """```json
{
    "has_interaction": true,
    "interactions": [
        {"severity": "mild", "mechanism": "Minor effect"},
        {"severity": "moderate", "mechanism": "Absorption decrease"},
        {"severity": "severe", "mechanism": "CYP3A4 inhibition"}
    ]
}
```"""

        result = agent._parse_agent_response(response)

        assert result["severity"] == "severe"

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_falls_back_to_first_interaction(self, mock_types, mock_agent_class):
        from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

        agent = DrugInteractionCheckerAgent(api_key="test_key")
        response = """```json
{
    "has_interaction": true,
    "interactions": [
        {
            "severity": "moderate",
            "mechanism": "Decreased absorption",
            "clinical_effect": "Reduced efficacy",
            "recommendation": "Space doses",
            "confidence": 0.88
        }
    ]
}
```"""

        result = agent._parse_agent_response(response)

        assert result["mechanism"] == "Decreased absorption"
        assert result["clinical_effect"] == "Reduced efficacy"
        assert result["recommendation"] == "Space doses"
        assert result["confidence"] == 0.88

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_no_interactions_defaults_none(self, mock_types, mock_agent_class):
        from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

        agent = DrugInteractionCheckerAgent(api_key="test_key")
        response = """```json
{
    "has_interaction": false,
    "interactions": []
}
```"""

        result = agent._parse_agent_response(response)

        assert result["has_interaction"] is False
        assert result["severity"] == "none"

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_with_json_and_srtr(self, mock_types, mock_agent_class):
        from services.agents.medication_advisor_agent import MedicationAdvisorAgent

        agent = MedicationAdvisorAgent(api_key="test_key")
        response = """```json
{
    "recommendation": "Take the dose now",
    "reasoning_steps": ["Step 1", "Step 2"],
    "risk_level": "low",
    "confidence": 0.92,
    "next_steps": ["Monitor", "Follow up"],
    "srtr_data_source": {"source": "SRTR 2023", "organ": "Kidney"}
}
```"""

        result = agent._parse_agent_response(response)

        assert result["recommendation"] == "Take the dose now"
        assert result["risk_level"] == "low"
        assert result["confidence"] == 0.92
        assert result["srtr_data_source"]["source"] == "SRTR 2023"

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_response_rejection_risk_with_json(self, mock_types, mock_agent_class):
        from services.agents.rejection_risk_agent import RejectionRiskAgent

        agent = RejectionRiskAgent(api_key="test_key")
        response = """```json
{
    "rejection_probability": 0.35,
    "urgency": "HIGH",
    "risk_level": "high",
    "recommended_action": "Contact transplant team",
    "reasoning_steps": ["Fever elevated", "Weight gain noted"],
    "similar_cases": [{"symptoms": "fever", "outcome": "treated", "similarity": 0.8}],
    "srtr_data_source": {"source": "SRTR 2023"}
}
```"""

        result = agent._parse_agent_response(response)

        assert result["rejection_probability"] == 0.35
        assert result["urgency"] == "HIGH"
        assert result["risk_level"] == "high"
        assert result["recommended_action"] == "Contact transplant team"
        assert len(result["similar_cases"]) == 1
