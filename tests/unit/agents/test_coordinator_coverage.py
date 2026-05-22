"""Coverage tests for TransplantCoordinatorAgent — sequential consult, parallel consult,
session-creation branches, classify general_inquiry, and _synthesize_response."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def _async_generator_mock(text: str):
    async def _generator():
        event = MagicMock()
        event.content = MagicMock()
        event.content.parts = [MagicMock()]
        event.content.parts[0].text = text
        yield event

    return _generator()


class TestSessionCreationBranch:
    @patch("services.agents.coordinator_agent.Runner")
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_analyze_routing_creates_session_when_none(
        self, mock_types, mock_agent_class, mock_runner_class
    ):
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        mock_runner.app_name = "TransplantCoordinator"

        mock_session_svc = AsyncMock()
        mock_session_svc.get_session.return_value = None
        mock_runner.session_service = mock_session_svc
        mock_runner.run_async.side_effect = lambda **_: _async_generator_mock("Routing")

        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test")
        agent._analyze_routing("I missed my dose")

        mock_session_svc.create_session.assert_called()


class TestClassifyGeneralInquiry:
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_classify_empty_list(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test")
        assert agent._classify_request_type([]) == "general_inquiry"


class TestDefaultRouting:
    @patch("services.agents.coordinator_agent.Runner")
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_defaults_to_medication_advisor_for_unclear_request(
        self, mock_types, mock_agent_class, mock_runner_class
    ):
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        mock_runner.app_name = "TransplantCoordinator"

        mock_session_svc = AsyncMock()
        mock_session_svc.get_session.return_value = MagicMock()
        mock_runner.session_service = mock_session_svc
        mock_runner.run_async.side_effect = lambda **_: _async_generator_mock("Routing")

        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test")
        routing = agent._analyze_routing("hello there")

        assert "MedicationAdvisor" in routing["agents_needed"]


class TestSequentialConsult:
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_consult_all_specialists_sequential(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(
            api_key="test",
            medication_advisor=MagicMock(),
            symptom_monitor=MagicMock(),
            drug_interaction_checker=MagicMock(),
        )

        routing = {
            "agents_needed": ["MedicationAdvisor", "SymptomMonitor", "DrugInteractionChecker"]
        }
        responses = agent._consult_specialists(
            routing_decision=routing,
            _request="test",
            _patient_id=None,
            _patient_context=None,
            parallel=False,
        )

        assert "MedicationAdvisor" in responses
        assert "SymptomMonitor" in responses
        assert "DrugInteractionChecker" in responses
        assert responses["MedicationAdvisor"]["status"] == "success"
        assert responses["SymptomMonitor"]["status"] == "success"
        assert responses["DrugInteractionChecker"]["status"] == "success"


class TestParallelConsult:
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_consult_specialists_parallel(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(
            api_key="test",
            medication_advisor=MagicMock(),
            symptom_monitor=MagicMock(),
            drug_interaction_checker=MagicMock(),
        )

        result = asyncio.run(
            agent._consult_specialists_parallel(
                ["MedicationAdvisor", "SymptomMonitor", "DrugInteractionChecker"]
            )
        )

        assert "MedicationAdvisor" in result
        assert "SymptomMonitor" in result
        assert "DrugInteractionChecker" in result

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_async_medication_advisor(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test", medication_advisor=MagicMock())
        result = asyncio.run(agent._consult_medication_advisor_async())
        assert result["agent"] == "MedicationAdvisor"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_async_symptom_monitor(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test", symptom_monitor=MagicMock())
        result = asyncio.run(agent._consult_symptom_monitor_async())
        assert result["agent"] == "SymptomMonitor"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_async_drug_interaction(self, mock_types, mock_agent_class):
        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test", drug_interaction_checker=MagicMock())
        result = asyncio.run(agent._consult_drug_interaction_async())
        assert result["agent"] == "DrugInteractionChecker"


class TestSynthesizeResponse:
    @patch("services.agents.coordinator_agent.Runner")
    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_synthesize_with_specialist_responses(
        self, mock_types, mock_agent_class, mock_runner_class
    ):
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        mock_runner.app_name = "TransplantCoordinator"

        mock_session_svc = AsyncMock()
        mock_session_svc.get_session.return_value = None
        mock_runner.session_service = mock_session_svc
        mock_runner.run_async.side_effect = lambda **_: _async_generator_mock("Synthesized")

        from services.agents.coordinator_agent import TransplantCoordinatorAgent

        agent = TransplantCoordinatorAgent(api_key="test")
        result = agent._synthesize_response(
            request="I missed my dose",
            routing_decision={"reasoning": "test reason", "request_type": "missed_dose"},
            specialist_responses={
                "MedicationAdvisor": {
                    "response": "Take dose now",
                    "status": "success",
                }
            },
        )

        assert "agents_consulted" in result
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert result["request_type"] == "missed_dose"
        assert result["confidence"] == 0.85
        mock_session_svc.create_session.assert_called()
