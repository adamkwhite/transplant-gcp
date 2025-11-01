"""Unit tests for TransplantCoordinatorAgent."""

from unittest.mock import MagicMock, patch

import pytest

from services.agents.coordinator_agent import TransplantCoordinatorAgent


class TestTransplantCoordinatorAgent:
    """Test suite for TransplantCoordinatorAgent."""

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_init_creates_agent_with_correct_config(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that agent is initialized with correct configuration."""
        # Arrange
        mock_generate_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config

        # Act
        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Assert
        assert agent.api_key == "test_key"
        mock_agent_class.assert_called_once_with(
            name="TransplantCoordinator",
            model="gemini-2.0-flash",
            description="Routes patient requests to appropriate specialist agents",
            instruction=pytest.approx("You are the TransplantCoordinator", abs=5),
            generate_content_config=mock_generate_config,
        )

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_init_stores_specialist_agents(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that specialist agent references are stored."""
        # Arrange
        mock_med_advisor = MagicMock()
        mock_symptom_monitor = MagicMock()
        mock_drug_checker = MagicMock()

        # Act
        agent = TransplantCoordinatorAgent(
            api_key="test_key",
            medication_advisor=mock_med_advisor,
            symptom_monitor=mock_symptom_monitor,
            drug_interaction_checker=mock_drug_checker,
        )

        # Assert
        assert agent.medication_advisor == mock_med_advisor
        assert agent.symptom_monitor == mock_symptom_monitor
        assert agent.drug_interaction_checker == mock_drug_checker

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_route_request_calls_agent(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that route_request invokes the coordinator agent."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing analysis"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        result = agent.route_request(
            request="I missed my tacrolimus dose",
            patient_id="P123",
        )

        # Assert
        # Should call agent.run at least once for routing analysis
        assert mock_agent_instance.run.call_count >= 1

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_route_request_returns_structured_response(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that route_request returns expected structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing complete"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        result = agent.route_request(request="I have a fever")

        # Assert
        assert "agents_consulted" in result
        assert isinstance(result["agents_consulted"], list)
        assert "recommendations" in result
        assert "specialist_responses" in result
        assert isinstance(result["specialist_responses"], dict)
        assert "coordinator_analysis" in result
        assert "request_type" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_analyze_routing_identifies_medication_advisor(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that routing correctly identifies medication-related requests."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        routing = agent._analyze_routing("I missed my dose this morning")

        # Assert
        assert "agents_needed" in routing
        assert "MedicationAdvisor" in routing["agents_needed"]
        assert routing["request_type"] == "missed_dose"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_analyze_routing_identifies_symptom_monitor(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that routing correctly identifies symptom-related requests."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        routing = agent._analyze_routing("I have a fever and decreased urine output")

        # Assert
        assert "agents_needed" in routing
        assert "SymptomMonitor" in routing["agents_needed"]

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_analyze_routing_identifies_drug_interaction_checker(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that routing correctly identifies interaction-related requests."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        routing = agent._analyze_routing("Can I take ibuprofen with my tacrolimus?")

        # Assert
        assert "agents_needed" in routing
        assert "DrugInteractionChecker" in routing["agents_needed"]

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_analyze_routing_identifies_multi_concern(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that routing identifies requests needing multiple agents."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Routing"

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        routing = agent._analyze_routing("I missed my dose and now I have a fever")

        # Assert
        assert "agents_needed" in routing
        assert len(routing["agents_needed"]) > 1
        assert routing["request_type"] == "multi_concern"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_classify_request_type_missed_dose(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test request type classification for missed dose."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        request_type = agent._classify_request_type(["MedicationAdvisor"])

        # Assert
        assert request_type == "missed_dose"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_classify_request_type_symptom_check(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test request type classification for symptom check."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        request_type = agent._classify_request_type(["SymptomMonitor"])

        # Assert
        assert request_type == "symptom_check"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_classify_request_type_interaction_check(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test request type classification for interaction check."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        request_type = agent._classify_request_type(["DrugInteractionChecker"])

        # Assert
        assert request_type == "interaction_check"

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_get_agent_capabilities_structure(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that get_agent_capabilities returns correct structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        capabilities = agent.get_agent_capabilities()

        # Assert
        assert "coordinator" in capabilities
        assert "specialists" in capabilities
        assert "MedicationAdvisor" in capabilities["specialists"]
        assert "SymptomMonitor" in capabilities["specialists"]
        assert "DrugInteractionChecker" in capabilities["specialists"]

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_get_agent_capabilities_medication_advisor(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test MedicationAdvisor capabilities data."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = TransplantCoordinatorAgent(api_key="test_key")

        # Act
        capabilities = agent.get_agent_capabilities()

        # Assert
        med_advisor = capabilities["specialists"]["MedicationAdvisor"]
        assert "Missed dose analysis" in med_advisor["role"]
        assert "handles" in med_advisor
        assert len(med_advisor["handles"]) > 0

    @patch("services.agents.coordinator_agent.Agent")
    @patch("services.agents.coordinator_agent.types")
    def test_consult_specialists_with_medication_advisor(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test consulting MedicationAdvisor specialist."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_med_advisor = MagicMock()

        agent = TransplantCoordinatorAgent(api_key="test_key", medication_advisor=mock_med_advisor)

        # Act
        routing_decision = {"agents_needed": ["MedicationAdvisor"]}
        responses = agent._consult_specialists(
            routing_decision=routing_decision,
            _request="test",
            _patient_id=None,
            _patient_context=None,
        )

        # Assert
        assert "MedicationAdvisor" in responses
        assert responses["MedicationAdvisor"]["status"] == "consulted"
