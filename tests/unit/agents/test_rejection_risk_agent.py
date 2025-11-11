"""Unit tests for RejectionRiskAgent."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

from services.agents.rejection_risk_agent import RejectionRiskAgent


def _async_generator_mock(text: str):
    """Helper to create async generator mock for Runner.run_async()."""

    async def _generator():
        # Yield event with text content
        event = MagicMock()
        event.content = MagicMock()
        event.content.parts = [MagicMock()]
        event.content.parts[0].text = text
        yield event

    return _generator()


class TestRejectionRiskAgent:
    """Test suite for RejectionRiskAgent."""

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_init_creates_agent_with_correct_config(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that agent is initialized with correct configuration."""
        # Arrange
        mock_generate_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config

        # Act
        agent = RejectionRiskAgent(api_key="test_key")

        # Assert
        assert agent.api_key == "test_key"
        mock_types.GenerateContentConfig.assert_called_once()
        mock_agent_class.assert_called_once_with(
            name="RejectionRiskAnalyzer",
            model="gemini-2.0-flash",
            description="Analyzes transplant rejection symptoms using SRTR population data",
            instruction=ANY,  # Long instruction string, just verify it's passed
            generate_content_config=mock_generate_config,
        )

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_init_uses_default_api_key(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that default API key is used when none provided."""
        # Act
        agent = RejectionRiskAgent()

        # Assert - should use GEMINI_API_KEY from config
        assert agent.api_key is not None

    @patch("services.agents.rejection_risk_agent.get_srtr_data")
    @patch("services.agents.base_adk_agent.Runner")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_analyze_rejection_risk_calls_agent(
        self,
        mock_types: MagicMock,
        mock_agent_class: MagicMock,
        mock_runner_class: MagicMock,
        mock_get_srtr: MagicMock,
    ) -> None:
        """Test that analyze_rejection_risk invokes the agent with correct prompt."""
        # Arrange
        # Mock SRTR data
        mock_srtr = MagicMock()
        mock_srtr.format_for_prompt.return_value = "Population stats: 6.19% rejection rate"
        mock_srtr.get_acute_rejection_rate.return_value = 6.19
        mock_srtr._summary = {"total_records": 11709}
        mock_get_srtr.return_value = mock_srtr

        mock_runner_instance = MagicMock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.app_name = "RejectionRiskAnalyzer"

        # Mock session service
        mock_session_service = AsyncMock()
        mock_session_service.get_session.return_value = MagicMock()
        mock_runner_instance.session_service = mock_session_service

        # Mock run_async to return async generator
        mock_runner_instance.run_async.side_effect = lambda **_: _async_generator_mock(
            "Agent response"
        )

        agent = RejectionRiskAgent(api_key="test_key")

        # Act
        result = agent.analyze_rejection_risk(
            symptoms={
                "fever": 99.5,
                "weight_gain": 3,
                "fatigue": "moderate",
                "urine_output": "decreased",
            },
            patient_id="P123",
            patient_context={
                "organ_type": "kidney",
                "age_group": "35-49",
                "months_post_transplant": 6,
            },
        )

        # Assert
        mock_runner_instance.run_async.assert_called_once()

        # Verify result structure
        assert "rejection_probability" in result
        assert "urgency" in result
        assert "risk_level" in result
        assert "recommended_action" in result
        assert "reasoning_steps" in result
        assert "similar_cases" in result
        assert "agent_name" in result

    @patch("services.agents.base_adk_agent.Runner")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_analyze_rejection_risk_without_optional_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock, mock_runner_class: MagicMock
    ) -> None:
        """Test analyze_rejection_risk works without optional parameters."""
        # Arrange
        mock_runner_instance = MagicMock()
        mock_runner_class.return_value = mock_runner_instance
        mock_runner_instance.app_name = "RejectionRiskAnalyzer"

        # Mock session service
        mock_session_service = AsyncMock()
        mock_session_service.get_session.return_value = MagicMock()
        mock_runner_instance.session_service = mock_session_service

        # Mock run_async to return async generator
        mock_runner_instance.run_async.side_effect = lambda **_: _async_generator_mock(
            "Agent response"
        )

        agent = RejectionRiskAgent(api_key="test_key")

        # Act
        result = agent.analyze_rejection_risk(
            symptoms={"fever": 100.5, "weight_gain": 4, "fatigue": "high"}
        )

        # Assert
        mock_runner_instance.run_async.assert_called_once()
        # Since mock returns unparseable response, expect fallback values
        assert result["urgency"] == "MEDIUM"
        assert result["risk_level"] == "medium"

    @patch("services.agents.rejection_risk_agent.get_srtr_data")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_build_rejection_prompt_includes_all_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock, mock_get_srtr: MagicMock
    ) -> None:
        """Test that prompt builder includes all provided parameters."""
        # Arrange
        # Mock SRTR data
        mock_srtr = MagicMock()
        mock_srtr.format_for_prompt.return_value = "Population stats: 6.19% rejection rate"
        mock_srtr.get_acute_rejection_rate.return_value = 6.19
        mock_srtr._summary = {"total_records": 11709}
        mock_get_srtr.return_value = mock_srtr

        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = RejectionRiskAgent(api_key="test_key")

        # Act
        prompt = agent._build_rejection_prompt(
            symptoms={
                "fever": 99.5,
                "weight_gain": 3,
                "fatigue": "moderate",
                "urine_output": "decreased",
            },
            patient_id="P123",
            patient_context={
                "organ_type": "kidney",
                "age_group": "35-49",
                "months_post_transplant": 6,
            },
        )

        # Assert
        assert "99.5" in prompt
        assert "3" in prompt
        assert "moderate" in prompt
        assert "decreased" in prompt
        assert "P123" in prompt
        assert "kidney" in prompt
        assert "JSON response" in prompt or "SRTR" in prompt

    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_parse_agent_response_returns_structured_format(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that response parser returns expected structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = RejectionRiskAgent(api_key="test_key")

        # Act
        result = agent._parse_agent_response("Test agent response")

        # Assert
        assert isinstance(result, dict)
        assert "rejection_probability" in result
        assert isinstance(result["rejection_probability"], float)
        assert 0.0 <= result["rejection_probability"] <= 1.0
        assert "urgency" in result
        assert result["urgency"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert "risk_level" in result
        assert result["risk_level"] in ["low", "medium", "high", "critical"]
        assert "recommended_action" in result
        assert "reasoning_steps" in result
        assert isinstance(result["reasoning_steps"], list)
        assert "similar_cases" in result
        assert isinstance(result["similar_cases"], list)
        assert "agent_name" in result
        assert "raw_response" in result
