"""Unit tests for SymptomMonitorAgent."""

from unittest.mock import ANY, MagicMock, patch

from services.agents.symptom_monitor_agent import SymptomMonitorAgent


class TestSymptomMonitorAgent:
    """Test suite for SymptomMonitorAgent."""

    @patch("services.agents.symptom_monitor_agent.Agent")
    @patch("services.agents.symptom_monitor_agent.types")
    def test_init_creates_agent_with_correct_config(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that agent is initialized with correct configuration."""
        # Arrange
        mock_generate_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config

        # Act
        agent = SymptomMonitorAgent(api_key="test_key")

        # Assert
        assert agent.api_key == "test_key"
        mock_agent_class.assert_called_once_with(
            name="SymptomMonitor",
            model="gemini-2.0-flash",
            description="Detects transplant rejection symptoms and assesses urgency",
            instruction=ANY,  # Long instruction string, just verify it's passed
            generate_content_config=mock_generate_config,
        )

    @patch("services.agents.symptom_monitor_agent.Agent")
    @patch("services.agents.symptom_monitor_agent.types")
    def test_analyze_symptoms_calls_agent(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that analyze_symptoms invokes the agent."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Agent response"

        agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        result = agent.analyze_symptoms(
            symptoms=["fever", "decreased urine"],
            patient_id="P123",
            vital_signs={"temperature": 101.5, "weight": 160},
        )

        # Assert
        mock_agent_instance.run.assert_called_once()
        call_args = mock_agent_instance.run.call_args[0][0]
        assert "fever" in call_args
        assert "decreased urine" in call_args
        assert "P123" in call_args

    @patch("services.agents.symptom_monitor_agent.Agent")
    @patch("services.agents.symptom_monitor_agent.types")
    def test_analyze_symptoms_returns_structured_response(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that analyze_symptoms returns expected structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Agent response"

        agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        result = agent.analyze_symptoms(symptoms=["fever", "fatigue"])

        # Assert
        assert "rejection_risk" in result
        assert result["rejection_risk"] in ["low", "medium", "high", "critical"]
        assert "urgency" in result
        assert result["urgency"] in ["routine", "same_day", "urgent", "emergency"]
        assert "reasoning" in result
        assert "actions" in result
        assert isinstance(result["actions"], list)
        assert "differential" in result
        assert isinstance(result["differential"], list)
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_get_rejection_symptoms_reference_structure(self) -> None:
        """Test that rejection symptoms reference has correct structure."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        assert "critical_symptoms" in reference
        assert "warning_symptoms" in reference
        assert "monitoring_guidelines" in reference

    def test_get_rejection_symptoms_fever_data(self) -> None:
        """Test fever symptom data in reference."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        fever = reference["critical_symptoms"]["fever"]
        assert "threshold" in fever
        assert "100" in fever["threshold"]
        assert fever["urgency"] == "urgent"
        assert "rejection" in fever["significance"].lower()

    def test_get_rejection_symptoms_decreased_urine_data(self) -> None:
        """Test decreased urine symptom data."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        decreased_urine = reference["critical_symptoms"]["decreased_urine"]
        assert "500ml" in decreased_urine["threshold"]
        assert decreased_urine["urgency"] == "urgent"

    def test_get_rejection_symptoms_weight_gain_data(self) -> None:
        """Test weight gain symptom data."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        weight_gain = reference["critical_symptoms"]["weight_gain"]
        assert "2 lbs" in weight_gain["threshold"]
        assert weight_gain["urgency"] == "same_day"

    def test_get_rejection_symptoms_elevated_creatinine_data(self) -> None:
        """Test elevated creatinine symptom data."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        creatinine = reference["critical_symptoms"]["elevated_creatinine"]
        assert "20%" in creatinine["threshold"]
        assert creatinine["urgency"] == "urgent"

    def test_get_rejection_symptoms_monitoring_guidelines(self) -> None:
        """Test monitoring guidelines are present."""
        # Arrange
        with (
            patch("services.agents.symptom_monitor_agent.Agent"),
            patch("services.agents.symptom_monitor_agent.types"),
        ):
            agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        reference = agent.get_rejection_symptoms_reference()

        # Assert
        guidelines = reference["monitoring_guidelines"]
        assert "temperature" in guidelines
        assert "weight" in guidelines
        assert "blood_pressure" in guidelines
        assert "urine_output" in guidelines
        assert "Daily" in guidelines["temperature"]

    @patch("services.agents.symptom_monitor_agent.Agent")
    @patch("services.agents.symptom_monitor_agent.types")
    def test_build_symptom_analysis_prompt_includes_all_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that prompt includes all provided parameters."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = SymptomMonitorAgent(api_key="test_key")

        # Act
        prompt = agent._build_symptom_analysis_prompt(
            symptoms=["fever", "fatigue"],
            patient_id="P123",
            patient_context={"transplant_date": "2024-01-01"},
            vital_signs={"temperature": 101.5},
        )

        # Assert
        assert "fever" in prompt
        assert "fatigue" in prompt
        assert "P123" in prompt
        assert "transplant_date" in prompt
        assert "temperature" in prompt
        assert "JSON response" in prompt
