"""Unit tests for DrugInteractionCheckerAgent."""

from unittest.mock import MagicMock, patch

import pytest

from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent


class TestDrugInteractionCheckerAgent:
    """Test suite for DrugInteractionCheckerAgent."""

    @patch("services.agents.drug_interaction_agent.Agent")
    @patch("services.agents.drug_interaction_agent.types")
    def test_init_creates_agent_with_correct_config(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that agent is initialized with correct configuration."""
        # Arrange
        mock_generate_config = MagicMock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config

        # Act
        agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Assert
        assert agent.api_key == "test_key"
        mock_agent_class.assert_called_once_with(
            name="DrugInteractionChecker",
            model="gemini-2.0-flash-lite",  # Uses lite model for faster checks
            description="Validates medication safety and identifies drug interactions",
            instruction=pytest.approx("You are the DrugInteractionChecker", abs=5),
            generate_content_config=mock_generate_config,
        )

    @patch("services.agents.drug_interaction_agent.Agent")
    @patch("services.agents.drug_interaction_agent.types")
    def test_check_interaction_calls_agent(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that check_interaction invokes the agent."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "No interactions found"

        agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        result = agent.check_interaction(
            medications=["tacrolimus", "prednisone"],
            foods=["grapefruit juice"],
            supplements=["St. John's Wort"],
        )

        # Assert
        mock_agent_instance.run.assert_called_once()
        call_args = mock_agent_instance.run.call_args[0][0]
        assert "tacrolimus" in call_args
        assert "prednisone" in call_args
        assert "grapefruit juice" in call_args
        assert "St. John's Wort" in call_args

    @patch("services.agents.drug_interaction_agent.Agent")
    @patch("services.agents.drug_interaction_agent.types")
    def test_check_interaction_returns_structured_response(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that check_interaction returns expected structure."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "Response"

        agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        result = agent.check_interaction(medications=["tacrolimus"])

        # Assert
        assert "has_interaction" in result
        assert isinstance(result["has_interaction"], bool)
        assert "severity" in result
        assert result["severity"] in ["none", "mild", "moderate", "severe", "contraindicated"]
        assert "interactions" in result
        assert isinstance(result["interactions"], list)
        assert "mechanism" in result
        assert "clinical_effect" in result
        assert "recommendation" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_get_known_interactions_reference_structure(self) -> None:
        """Test that known interactions reference has correct structure."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        assert "contraindicated" in reference
        assert "severe" in reference
        assert "moderate" in reference
        assert "mild" in reference
        assert "cyp3a4_interactions" in reference

    def test_tacrolimus_grapefruit_interaction(self) -> None:
        """Test tacrolimus + grapefruit interaction data."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        interaction = reference["severe"]["tacrolimus_grapefruit"]
        assert "Tacrolimus" in interaction["combination"]
        assert "Grapefruit" in interaction["combination"]
        assert "CYP3A4" in interaction["mechanism"]
        assert "2-3x" in interaction["effect"]
        assert "Avoid" in interaction["action"]

    def test_tacrolimus_nsaids_interaction(self) -> None:
        """Test tacrolimus + NSAIDs interaction data."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        interaction = reference["moderate"]["tacrolimus_nsaids"]
        assert "Tacrolimus" in interaction["combination"]
        assert "NSAIDs" in interaction["combination"]
        assert "nephrotoxicity" in interaction["mechanism"]
        assert "acetaminophen" in interaction["action"]

    def test_mycophenolate_antacids_interaction(self) -> None:
        """Test mycophenolate + antacids interaction data."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        interaction = reference["moderate"]["mycophenolate_antacids"]
        assert "Mycophenolate" in interaction["combination"]
        assert "Antacids" in interaction["combination"]
        assert "absorption" in interaction["mechanism"]
        assert "2 hours" in interaction["action"]

    def test_contraindicated_interactions(self) -> None:
        """Test contraindicated interactions are present."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        contraindicated = reference["contraindicated"]
        assert "tacrolimus_cyclosporine" in contraindicated
        assert "tacrolimus_st_johns_wort" in contraindicated

        # Verify tacrolimus + cyclosporine
        tac_cyclo = contraindicated["tacrolimus_cyclosporine"]
        assert "calcineurin" in tac_cyclo["mechanism"]
        assert "Never" in tac_cyclo["action"]

    def test_cyp3a4_inhibitors_list(self) -> None:
        """Test CYP3A4 inhibitors list is comprehensive."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        cyp3a4 = reference["cyp3a4_interactions"]
        assert "Ketoconazole" in cyp3a4["strong_inhibitors"]
        assert "Grapefruit juice" in cyp3a4["strong_inhibitors"]
        assert "Erythromycin" in cyp3a4["strong_inhibitors"]

    def test_cyp3a4_inducers_list(self) -> None:
        """Test CYP3A4 inducers list is comprehensive."""
        # Arrange
        with (
            patch("services.agents.drug_interaction_agent.Agent"),
            patch("services.agents.drug_interaction_agent.types"),
        ):
            agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        reference = agent.get_known_interactions_reference()

        # Assert
        cyp3a4 = reference["cyp3a4_interactions"]
        assert "Rifampin" in cyp3a4["strong_inducers"]
        assert "St. John's Wort" in cyp3a4["strong_inducers"]
        assert "Phenytoin" in cyp3a4["strong_inducers"]

    @patch("services.agents.drug_interaction_agent.Agent")
    @patch("services.agents.drug_interaction_agent.types")
    def test_build_interaction_check_prompt_includes_all_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test that prompt includes all provided parameters."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance

        agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        prompt = agent._build_interaction_check_prompt(
            medications=["tacrolimus", "prednisone"],
            foods=["grapefruit"],
            supplements=["vitamin D"],
            patient_id="P123",
            patient_context={"kidney_function": "normal"},
        )

        # Assert
        assert "tacrolimus" in prompt
        assert "prednisone" in prompt
        assert "grapefruit" in prompt
        assert "vitamin D" in prompt
        assert "P123" in prompt
        assert "kidney_function" in prompt
        assert "JSON response" in prompt

    @patch("services.agents.drug_interaction_agent.Agent")
    @patch("services.agents.drug_interaction_agent.types")
    def test_check_interaction_without_optional_params(
        self, mock_types: MagicMock, mock_agent_class: MagicMock
    ) -> None:
        """Test check_interaction works without optional parameters."""
        # Arrange
        mock_agent_instance = MagicMock()
        mock_agent_class.return_value = mock_agent_instance
        mock_agent_instance.run.return_value = "No interactions"

        agent = DrugInteractionCheckerAgent(api_key="test_key")

        # Act
        result = agent.check_interaction(medications=["tacrolimus"])

        # Assert
        mock_agent_instance.run.assert_called_once()
        assert result["has_interaction"] is False
        assert result["severity"] == "none"
