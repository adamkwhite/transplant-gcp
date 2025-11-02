"""Unit tests for MedicationAdvisorAgent."""

from unittest.mock import ANY, MagicMock, patch

from services.agents.medication_advisor_agent import MedicationAdvisorAgent


class TestMedicationAdvisorAgent:
    """Test suite for MedicationAdvisorAgent."""

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_init_creates_agent_with_correct_config(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that agent is initialized with correct configuration."""
        # Arrange
        mock_generate_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config

        # Act
        agent = MedicationAdvisorAgent(api_key="test_key")

        # Assert
        assert agent.api_key == "test_key"
        mock_types.GenerateContentConfig.assert_called_once()
        mock_agent_class.assert_called_once_with(
            name="MedicationAdvisor",
            model="gemini-2.0-flash",
            description="Analyzes missed medication doses for transplant patients",
            instruction=ANY,  # Long instruction string, just verify it's passed
            generate_content_config=mock_generate_config,
        )

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_init_uses_default_api_key(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that default API key is used when none provided."""
        # Act
        agent = MedicationAdvisorAgent()

        # Assert - should use GEMINI_API_KEY from config
        assert agent.api_key is not None

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_analyze_missed_dose_calls_agent(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that analyze_missed_dose invokes the agent with correct prompt."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run_async.return_value = "Agent response"

        agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        result = agent.analyze_missed_dose(
            medication="tacrolimus",
            scheduled_time="8:00 AM",
            current_time="2:00 PM",
            patient_id="P123",
            patient_context={"transplant_date": "2024-01-01"},
        )

        # Assert
        mock_agent_instance.run_async.assert_called_once()
        call_args = mock_agent_instance.run_async.call_args[0][0]
        assert "tacrolimus" in call_args
        assert "8:00 AM" in call_args
        assert "2:00 PM" in call_args
        assert "P123" in call_args

        # Verify result structure
        assert "recommendation" in result
        assert "reasoning_steps" in result
        assert "risk_level" in result
        assert "confidence" in result
        assert "next_steps" in result
        assert "agent_name" in result

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_analyze_missed_dose_without_optional_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test analyze_missed_dose works without optional parameters."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run_async.return_value = "Agent response"

        agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        result = agent.analyze_missed_dose(
            medication="prednisone", scheduled_time="9:00 AM", current_time="3:00 PM"
        )

        # Assert
        mock_agent_instance.run_async.assert_called_once()
        assert result["risk_level"] == "medium"
        assert result["confidence"] == 0.85

    def test_get_therapeutic_window_tacrolimus(self) -> None:
        """Test therapeutic window for tacrolimus."""
        # Arrange
        with (
            patch("services.agents.medication_advisor_agent.Agent"),
            patch("services.agents.medication_advisor_agent.types"),
        ):
            agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        window = agent.get_therapeutic_window("tacrolimus")

        # Assert
        assert window["window_hours"] == 12
        assert window["critical_period"] == 4
        assert "Critical immunosuppressant" in window["guidance"]

    def test_get_therapeutic_window_mycophenolate(self) -> None:
        """Test therapeutic window for mycophenolate."""
        # Arrange
        with (
            patch("services.agents.medication_advisor_agent.Agent"),
            patch("services.agents.medication_advisor_agent.types"),
        ):
            agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        window = agent.get_therapeutic_window("mycophenolate")

        # Assert
        assert window["window_hours"] == 12
        assert window["critical_period"] == 6
        assert "antiproliferative" in window["guidance"]

    def test_get_therapeutic_window_prednisone(self) -> None:
        """Test therapeutic window for prednisone."""
        # Arrange
        with (
            patch("services.agents.medication_advisor_agent.Agent"),
            patch("services.agents.medication_advisor_agent.types"),
        ):
            agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        window = agent.get_therapeutic_window("prednisone")

        # Assert
        assert window["window_hours"] == 24
        assert window["critical_period"] == 12
        assert "corticosteroid" in window["guidance"]

    def test_get_therapeutic_window_unknown_medication(self) -> None:
        """Test therapeutic window for unknown medication returns default."""
        # Arrange
        with (
            patch("services.agents.medication_advisor_agent.Agent"),
            patch("services.agents.medication_advisor_agent.types"),
        ):
            agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        window = agent.get_therapeutic_window("unknown_drug")

        # Assert
        assert window["window_hours"] == 24
        assert window["critical_period"] == 12
        assert "Consult prescribing information" in window["guidance"]

    def test_get_therapeutic_window_case_insensitive(self) -> None:
        """Test that medication names are case-insensitive."""
        # Arrange
        with (
            patch("services.agents.medication_advisor_agent.Agent"),
            patch("services.agents.medication_advisor_agent.types"),
        ):
            agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        window1 = agent.get_therapeutic_window("TACROLIMUS")
        window2 = agent.get_therapeutic_window("Tacrolimus")
        window3 = agent.get_therapeutic_window("tacrolimus")

        # Assert
        assert window1 == window2 == window3
        assert window1["window_hours"] == 12

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_build_missed_dose_prompt_includes_all_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that prompt builder includes all provided parameters."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        prompt = agent._build_missed_dose_prompt(
            medication="tacrolimus",
            scheduled_time="8:00 AM",
            current_time="2:00 PM",
            patient_id="P123",
            patient_context={"transplant_date": "2024-01-01"},
        )

        # Assert
        assert "tacrolimus" in prompt
        assert "8:00 AM" in prompt
        assert "2:00 PM" in prompt
        assert "P123" in prompt
        assert "transplant_date" in prompt
        assert "JSON response" in prompt

    @patch("services.agents.medication_advisor_agent.Agent")
    @patch("services.agents.medication_advisor_agent.types")
    def test_parse_agent_response_returns_structured_format(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that response parser returns expected structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = MedicationAdvisorAgent(api_key="test_key")

        # Act
        result = agent._parse_agent_response("Test agent response")

        # Assert
        assert isinstance(result, dict)
        assert "recommendation" in result
        assert "reasoning_steps" in result
        assert isinstance(result["reasoning_steps"], list)
        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high", "critical"]
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
        assert "next_steps" in result
        assert isinstance(result["next_steps"], list)
        assert "agent_name" in result
        assert "raw_response" in result
