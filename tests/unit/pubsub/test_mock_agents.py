"""Unit tests for mock_agents module."""

from services.pubsub.mock_agents import (
    MockDrugInteractionCheckerAgent,
    MockMedicationAdvisorAgent,
    MockSymptomMonitorAgent,
)


class TestMockMedicationAdvisorAgent:
    def test_analyze_missed_dose_basic(self):
        agent = MockMedicationAdvisorAgent()
        result = agent.analyze_missed_dose(
            medication="tacrolimus",
            scheduled_time="08:00",
            current_time="12:00",
        )

        assert "recommendation" in result
        assert "tacrolimus" in result["recommendation"]
        assert result["risk_level"] == "moderate"
        assert result["confidence"] == 0.85

    def test_analyze_missed_dose_with_patient_context(self):
        agent = MockMedicationAdvisorAgent()
        result = agent.analyze_missed_dose(
            medication="mycophenolate",
            scheduled_time="09:00",
            current_time="15:00",
            patient_id="P123",
            patient_context={"transplant_type": "liver"},
        )

        assert "P123" in result["recommendation"]
        assert "liver" in result["reasoning_steps"][0]


class TestMockSymptomMonitorAgent:
    def test_analyze_symptoms_with_fever(self):
        agent = MockSymptomMonitorAgent()
        result = agent.analyze_symptoms(
            symptoms=["fever", "fatigue"],
        )

        assert result["rejection_risk"] == "moderate"
        assert result["urgency"] == "same_day"

    def test_analyze_symptoms_without_fever(self):
        agent = MockSymptomMonitorAgent()
        result = agent.analyze_symptoms(
            symptoms=["fatigue"],
        )

        assert result["rejection_risk"] == "low"
        assert result["urgency"] == "routine"

    def test_analyze_symptoms_with_vital_signs(self):
        agent = MockSymptomMonitorAgent()
        result = agent.analyze_symptoms(
            symptoms=["fever"],
            vital_signs={"temperature": 101.5},
        )

        assert "101.5" in result["reasoning"]

    def test_analyze_symptoms_with_patient_context(self):
        agent = MockSymptomMonitorAgent()
        result = agent.analyze_symptoms(
            symptoms=["fever"],
            patient_id="P456",
            patient_context={"transplant_type": "heart"},
        )

        assert "P456" in result["reasoning"]
        assert "heart" in result["reasoning"]


class TestMockDrugInteractionCheckerAgent:
    def test_no_interaction(self):
        agent = MockDrugInteractionCheckerAgent()
        result = agent.check_interaction(
            medications=["tacrolimus", "prednisone"],
        )

        assert result["has_interaction"] is False
        assert result["severity"] == "none"

    def test_ibuprofen_interaction(self):
        agent = MockDrugInteractionCheckerAgent()
        result = agent.check_interaction(
            medications=["tacrolimus", "ibuprofen"],
        )

        assert result["has_interaction"] is True
        assert result["severity"] == "severe"
        assert len(result["interactions"]) > 0

    def test_grapefruit_interaction(self):
        agent = MockDrugInteractionCheckerAgent()
        result = agent.check_interaction(
            medications=["tacrolimus"],
            foods=["grapefruit"],
        )

        assert result["has_interaction"] is True

    def test_supplement_interaction(self):
        agent = MockDrugInteractionCheckerAgent()
        result = agent.check_interaction(
            medications=["tacrolimus"],
            supplements=["st john's wort"],
        )

        assert result["has_interaction"] is True
        assert result["severity"] == "severe"

    def test_with_patient_context(self):
        agent = MockDrugInteractionCheckerAgent()
        result = agent.check_interaction(
            medications=["tacrolimus", "ibuprofen"],
            patient_id="P789",
            patient_context={"transplant_type": "lung"},
        )

        assert "P789" in result["clinical_effect"]
        assert "lung" in result["clinical_effect"]
