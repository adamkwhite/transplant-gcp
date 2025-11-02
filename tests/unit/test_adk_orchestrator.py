"""Unit tests for ADKOrchestrator."""

from unittest.mock import MagicMock, patch

import pytest

from services.orchestration.adk_orchestrator import ADKOrchestrator


class TestADKOrchestrator:
    """Test suite for ADKOrchestrator."""

    @pytest.fixture
    def mock_agent_class(self):
        """Mock the Agent class from Google ADK."""
        with patch("services.orchestration.adk_orchestrator.Agent") as mock:
            yield mock

    @pytest.fixture
    def mock_types(self):
        """Mock Google genai types."""
        with patch("services.orchestration.adk_orchestrator.types") as mock:
            yield mock

    @pytest.fixture
    def orchestrator(self, mock_agent_class, mock_types):
        """Create an ADKOrchestrator instance with mocked dependencies."""
        return ADKOrchestrator(api_key="test_api_key")

    def test_init_creates_specialist_agents(self, mock_agent_class, mock_types, orchestrator):
        """Test that initialization creates all specialist agents."""
        # Agent should be called 4 times: 3 specialists + 1 coordinator
        assert mock_agent_class.call_count == 4

    def test_init_creates_coordinator_with_sub_agents(
        self, mock_agent_class, mock_types, orchestrator
    ):
        """Test that coordinator is created with specialist sub-agents."""
        # Last call should be coordinator with sub_agents parameter
        coordinator_call = mock_agent_class.call_args_list[-1]
        assert "sub_agents" in coordinator_call[1]
        assert len(coordinator_call[1]["sub_agents"]) == 3

    def test_init_uses_provided_api_key(self, mock_agent_class, mock_types):
        """Test that provided API key is used."""
        orchestrator = ADKOrchestrator(api_key="custom_key")
        assert orchestrator.api_key == "custom_key"

    def test_init_uses_default_api_key(self, mock_agent_class, mock_types):
        """Test that default API key from config is used when not provided."""
        orchestrator = ADKOrchestrator()
        assert orchestrator.api_key is not None

    def test_build_coordinator_instruction(self, orchestrator):
        """Test coordinator instruction building."""
        instruction = orchestrator._build_coordinator_instruction()

        assert "TransplantCoordinator" in instruction
        assert "MedicationAdvisor" in instruction
        assert "SymptomMonitor" in instruction
        assert "DrugInteractionChecker" in instruction
        assert "transfer_to_agent" in instruction

    def test_build_request_with_context_basic(self, orchestrator):
        """Test building request with minimal context."""
        result = orchestrator._build_request_with_context(
            user_request="I missed my dose",
            patient_id=None,
            patient_context=None,
            conversation_history=None,
        )

        assert "I missed my dose" in result
        assert "**Current Request:**" in result

    def test_build_request_with_patient_id(self, orchestrator):
        """Test building request with patient ID."""
        result = orchestrator._build_request_with_context(
            user_request="I missed my dose",
            patient_id="patient_123",
            patient_context=None,
            conversation_history=None,
        )

        assert "patient_123" in result
        assert "**Patient ID:**" in result

    def test_build_request_with_patient_context(self, orchestrator):
        """Test building request with patient context."""
        result = orchestrator._build_request_with_context(
            user_request="I missed my dose",
            patient_id=None,
            patient_context={"medication": "tacrolimus", "dose": "2mg"},
            conversation_history=None,
        )

        assert "tacrolimus" in result
        assert "2mg" in result
        assert "**Patient Context:**" in result

    def test_build_request_with_conversation_history(self, orchestrator):
        """Test building request with conversation history."""
        history = [
            {"role": "user", "content": "I have symptoms"},
            {"role": "assistant", "content": "What symptoms?"},
            {"role": "user", "content": "Fever"},
        ]

        result = orchestrator._build_request_with_context(
            user_request="It's 101F",
            patient_id=None,
            patient_context=None,
            conversation_history=history,
        )

        assert "**Previous Conversation:**" in result
        assert "I have symptoms" in result
        assert "What symptoms?" in result
        assert "Fever" in result

    def test_build_request_limits_conversation_history(self, orchestrator):
        """Test that conversation history is limited to last 3 turns."""
        history = [
            {"role": "user", "content": "Turn 1"},
            {"role": "assistant", "content": "Turn 2"},
            {"role": "user", "content": "Turn 3"},
            {"role": "assistant", "content": "Turn 4"},
            {"role": "user", "content": "Turn 5"},
        ]

        result = orchestrator._build_request_with_context(
            user_request="Current",
            patient_id=None,
            patient_context=None,
            conversation_history=history,
        )

        # Should only include last 3 turns
        assert "Turn 1" not in result
        assert "Turn 2" not in result
        assert "Turn 3" in result
        assert "Turn 4" in result
        assert "Turn 5" in result

    def test_parse_orchestrator_response(self, orchestrator):
        """Test parsing orchestrator response."""
        mock_response = "This is a test response"

        result = orchestrator._parse_orchestrator_response(mock_response)

        assert result["response"] == "This is a test response"
        assert result["orchestrator"] == "ADK"
        assert "agents_consulted" in result
        assert "routing_path" in result
        assert "raw_response" in result

    def test_extract_agents_consulted(self, orchestrator):
        """Test extracting agents consulted from response."""
        mock_response = MagicMock()

        result = orchestrator._extract_agents_consulted(mock_response)

        # Currently returns empty list (placeholder implementation)
        assert isinstance(result, list)

    def test_extract_routing_path(self, orchestrator):
        """Test extracting routing path from response."""
        mock_response = MagicMock()

        result = orchestrator._extract_routing_path(mock_response)

        # Currently returns coordinator only (placeholder implementation)
        assert isinstance(result, list)
        assert "TransplantCoordinator" in result

    def test_get_agent_capabilities(self, orchestrator):
        """Test getting agent capabilities."""
        capabilities = orchestrator.get_agent_capabilities()

        assert capabilities["orchestration_method"] == "ADK Native"
        assert "features" in capabilities
        assert "coordinator" in capabilities
        assert "specialists" in capabilities

    def test_get_agent_capabilities_has_all_specialists(self, orchestrator):
        """Test that capabilities include all specialist agents."""
        capabilities = orchestrator.get_agent_capabilities()
        specialists = capabilities["specialists"]

        assert "MedicationAdvisor" in specialists
        assert "SymptomMonitor" in specialists
        assert "DrugInteractionChecker" in specialists

    def test_get_agent_capabilities_specialist_details(self, orchestrator):
        """Test that specialist details include required fields."""
        capabilities = orchestrator.get_agent_capabilities()
        medication_advisor = capabilities["specialists"]["MedicationAdvisor"]

        assert "name" in medication_advisor
        assert "model" in medication_advisor
        assert "handles" in medication_advisor
        assert len(medication_advisor["handles"]) > 0

    @patch("google.genai.Client")
    def test_process_request_basic(self, mock_client_class, orchestrator):
        """Test processing a basic request."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = orchestrator.process_request(
            user_request="I missed my dose", patient_id="test_patient"
        )

        # Verify
        assert "response" in result
        assert result["response"] == "Test response"
        mock_client.models.generate_content.assert_called_once()

    @patch("google.genai.Client")
    def test_process_request_with_all_context(self, mock_client_class, orchestrator):
        """Test processing request with full context."""
        # Setup mock
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Detailed response"
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = orchestrator.process_request(
            user_request="I have symptoms",
            patient_id="patient_001",
            patient_context={"medication": "tacrolimus"},
            conversation_history=[{"role": "user", "content": "Previous message"}],
        )

        # Verify call was made with enriched context
        call_args = mock_client.models.generate_content.call_args
        request_text = call_args[1]["contents"]

        assert "I have symptoms" in request_text
        assert "patient_001" in request_text
        assert "tacrolimus" in request_text
        assert "Previous message" in request_text

    @patch("google.genai.Client")
    def test_process_request_handles_empty_response(self, mock_client_class, orchestrator):
        """Test handling empty/None response text."""
        # Setup mock with no text
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = None
        mock_client.models.generate_content.return_value = mock_response

        # Execute
        result = orchestrator.process_request(user_request="Test", patient_id="test_patient")

        # Should handle gracefully
        assert "response" in result
        assert result["response"] == ""
