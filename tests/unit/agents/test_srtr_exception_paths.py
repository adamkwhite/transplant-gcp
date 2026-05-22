"""Tests for SRTR exception handling in medication_advisor and rejection_risk agents."""

from unittest.mock import patch


class TestMedicationAdvisorSRTRException:
    @patch("services.agents.medication_advisor_agent.get_srtr_data")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_build_prompt_handles_srtr_exception(self, mock_types, mock_agent, mock_get_srtr):
        mock_get_srtr.side_effect = Exception("SRTR unavailable")

        from services.agents.medication_advisor_agent import MedicationAdvisorAgent

        agent = MedicationAdvisorAgent(api_key="test")
        prompt = agent._build_missed_dose_prompt(
            medication="tacrolimus",
            scheduled_time="08:00",
            current_time="12:00",
            patient_id=None,
            patient_context={"organ_type": "kidney"},
        )

        assert "WARNING: SRTR data unavailable" in prompt


class TestRejectionRiskSRTRException:
    @patch("services.agents.rejection_risk_agent.get_srtr_data")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_build_prompt_handles_srtr_exception(self, mock_types, mock_agent, mock_get_srtr):
        mock_get_srtr.side_effect = Exception("SRTR unavailable")

        from services.agents.rejection_risk_agent import RejectionRiskAgent

        agent = RejectionRiskAgent(api_key="test")
        prompt = agent._build_rejection_prompt(
            symptoms={"fever": 101.0},
            patient_id=None,
            patient_context={"organ_type": "kidney"},
        )

        assert "WARNING: SRTR data unavailable" in prompt
