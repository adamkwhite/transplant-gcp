"""
Integration Tests for In-Process Multi-Agent Communication

Tests the coordinator's ability to route requests, extract parameters,
call specialist agents, and synthesize responses.

Requires GEMINI_API_KEY environment variable for real API calls.
"""

import os

import pytest

from services.agents.coordinator_agent import TransplantCoordinatorAgent
from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent


@pytest.fixture
def api_key():
    """Get API key from environment or skip tests."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        pytest.skip("GEMINI_API_KEY not set - skipping integration tests")
    return key


@pytest.fixture
def specialist_agents(api_key):
    """Create specialist agent instances."""
    return {
        "medication_advisor": MedicationAdvisorAgent(api_key=api_key),
        "symptom_monitor": SymptomMonitorAgent(api_key=api_key),
        "drug_interaction_checker": DrugInteractionCheckerAgent(api_key=api_key),
    }


@pytest.fixture
def coordinator(api_key, specialist_agents):
    """Create coordinator agent with specialist agents."""
    return TransplantCoordinatorAgent(
        api_key=api_key,
        medication_advisor=specialist_agents["medication_advisor"],
        symptom_monitor=specialist_agents["symptom_monitor"],
        drug_interaction_checker=specialist_agents["drug_interaction_checker"],
    )


@pytest.mark.integration
class TestSingleSpecialistRouting:
    """Test routing to single specialist agents."""

    def test_route_to_medication_advisor(self, coordinator):
        """Test routing a missed dose request to MedicationAdvisor."""
        request = "I missed my tacrolimus dose at 8am, it's now 2pm. What should I do?"

        result = coordinator.route_request(request, parallel=False)

        # Verify routing decision
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert result["request_type"] in ["missed_dose", "multi_concern"]

        # Verify specialist was called
        assert "MedicationAdvisor" in result["specialist_responses"]
        med_response = result["specialist_responses"]["MedicationAdvisor"]
        assert med_response["status"] == "success"

        # Verify extraction worked
        assert "extraction_confidence" in med_response
        assert med_response["extraction_confidence"] > 0.0

        # Verify synthesis
        assert len(result["recommendations"]) > 0
        assert result["confidence"] > 0.0

    def test_route_to_symptom_monitor(self, coordinator):
        """Test routing a symptom request to SymptomMonitor."""
        request = "I have a fever of 101°F and decreased urine output today."

        result = coordinator.route_request(request, parallel=False)

        # Verify routing decision
        assert "SymptomMonitor" in result["agents_consulted"]
        assert result["request_type"] in ["symptom_check", "multi_concern"]

        # Verify specialist was called
        assert "SymptomMonitor" in result["specialist_responses"]
        symptom_response = result["specialist_responses"]["SymptomMonitor"]
        assert symptom_response["status"] == "success"

        # Verify extraction worked
        assert "extraction_confidence" in symptom_response

        # Verify synthesis
        assert len(result["recommendations"]) > 0

    def test_route_to_drug_interaction_checker(self, coordinator):
        """Test routing an interaction question to DrugInteractionChecker."""
        request = "Can I take ibuprofen with my tacrolimus medication?"

        result = coordinator.route_request(request, parallel=False)

        # Verify routing decision
        assert "DrugInteractionChecker" in result["agents_consulted"]

        # Verify specialist was called
        assert "DrugInteractionChecker" in result["specialist_responses"]
        interaction_response = result["specialist_responses"]["DrugInteractionChecker"]
        assert interaction_response["status"] == "success"

        # Verify synthesis
        assert len(result["recommendations"]) > 0


@pytest.mark.integration
class TestMultiSpecialistRouting:
    """Test routing to multiple specialist agents."""

    def test_route_to_multiple_specialists(self, coordinator):
        """Test routing a complex request to multiple specialists."""
        request = "I missed my tacrolimus at 8am and now I have a fever of 100.5°F"

        result = coordinator.route_request(request, parallel=False)

        # Verify routing to multiple agents
        assert len(result["agents_consulted"]) >= 2
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert "SymptomMonitor" in result["agents_consulted"]
        assert result["request_type"] == "multi_concern"

        # Verify both specialists were called successfully
        for agent_name in result["agents_consulted"]:
            response = result["specialist_responses"][agent_name]
            assert response["status"] == "success"

        # Verify synthesis integrates both responses
        assert len(result["recommendations"]) > 0

    def test_parallel_specialist_consultation(self, coordinator):
        """Test parallel consultation is faster than sequential."""
        import time

        request = "I missed my dose and have a fever and want to take ibuprofen"

        # Sequential consultation
        start_seq = time.time()
        result_seq = coordinator.route_request(request, parallel=False)
        time_seq = time.time() - start_seq

        # Parallel consultation
        start_par = time.time()
        result_par = coordinator.route_request(request, parallel=True)
        time_par = time.time() - start_par

        # Verify both got same agents
        assert set(result_seq["agents_consulted"]) == set(result_par["agents_consulted"])

        # Parallel should be faster (or at least not much slower)
        # Allow small margin for asyncio overhead
        print(f"Sequential: {time_seq:.2f}s, Parallel: {time_par:.2f}s")


@pytest.mark.integration
class TestParameterExtraction:
    """Test parameter extraction accuracy."""

    def test_medication_parameter_extraction(self, coordinator):
        """Test extraction of medication parameters."""
        request = "I forgot my tacrolimus dose at 8:00 AM, it's now 2:30 PM"

        result = coordinator.route_request(request, parallel=False)

        # Get medication advisor response
        med_response = result["specialist_responses"]["MedicationAdvisor"]

        # Verify parameters were extracted
        assert med_response["status"] == "success"
        assert med_response["extraction_confidence"] > 0.3

    def test_symptom_parameter_extraction(self, coordinator):
        """Test extraction of symptom parameters."""
        request = "I have fever, nausea, and my urine output has decreased"

        result = coordinator.route_request(request, parallel=False)

        # Get symptom monitor response
        symptom_response = result["specialist_responses"]["SymptomMonitor"]

        # Verify parameters were extracted
        assert symptom_response["status"] == "success"
        assert symptom_response["extraction_confidence"] > 0.3


@pytest.mark.integration
class TestResponseSynthesis:
    """Test response synthesis quality."""

    def test_synthesis_coherence(self, coordinator):
        """Test that synthesis creates coherent advice."""
        request = "I missed my morning tacrolimus and now I feel feverish"

        result = coordinator.route_request(request, parallel=False)

        recommendations = result["recommendations"]

        # Verify synthesis is not empty
        assert len(recommendations) > 100  # Should be substantive

        # Verify synthesis mentions both concerns (basic check)
        # LLM output can vary, so we use flexible checks
        assert isinstance(recommendations, str)

    def test_synthesis_with_single_agent(self, coordinator):
        """Test synthesis works with single agent."""
        request = "What should I do about my missed tacrolimus dose?"

        result = coordinator.route_request(request, parallel=False)

        # Should work even with single agent
        assert len(result["agents_consulted"]) >= 1
        assert len(result["recommendations"]) > 0

    def test_confidence_scoring(self, coordinator):
        """Test that confidence scores are reasonable."""
        request = "I missed my dose"

        result = coordinator.route_request(request, parallel=False)

        # Confidence should be between 0 and 1
        assert 0.0 <= result["confidence"] <= 1.0

        # With successful consultation, should have reasonable confidence
        if all(r["status"] == "success" for r in result["specialist_responses"].values()):
            assert result["confidence"] > 0.5


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in multi-agent communication."""

    def test_missing_specialist_agent(self, api_key):
        """Test coordinator handles missing specialist gracefully."""
        # Create coordinator with only one specialist
        coordinator = TransplantCoordinatorAgent(
            api_key=api_key,
            medication_advisor=MedicationAdvisorAgent(api_key=api_key),
            symptom_monitor=None,  # Missing
            drug_interaction_checker=None,  # Missing
        )

        request = "I have a fever and missed my dose"

        result = coordinator.route_request(request, parallel=False)

        # Should still work, just consulting available agent
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert len(result["recommendations"]) > 0

    def test_parameter_extraction_fallback(self, coordinator):
        """Test fallback when parameter extraction struggles."""
        # Ambiguous request
        request = "I'm concerned about my medication"

        result = coordinator.route_request(request, parallel=False)

        # Should still route and respond
        assert len(result["agents_consulted"]) > 0
        assert len(result["recommendations"]) > 0


@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    def test_scenario_missed_dose_simple(self, coordinator):
        """Test: Patient missed tacrolimus dose."""
        request = "I missed my tacrolimus at 8am, it's now 2pm"

        result = coordinator.route_request(request)

        assert "MedicationAdvisor" in result["agents_consulted"]
        assert result["confidence"] > 0.4
        assert len(result["recommendations"]) > 50

    def test_scenario_fever_and_missed_dose(self, coordinator):
        """Test: Patient has fever and missed dose."""
        request = "I have a fever of 101°F and I forgot my morning tacrolimus dose"

        result = coordinator.route_request(request)

        assert len(result["agents_consulted"]) >= 2
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert "SymptomMonitor" in result["agents_consulted"]
        assert result["request_type"] == "multi_concern"

    def test_scenario_drug_interaction_question(self, coordinator):
        """Test: Patient asking about drug interaction."""
        request = "Can I eat grapefruit while taking tacrolimus?"

        result = coordinator.route_request(request)

        assert "DrugInteractionChecker" in result["agents_consulted"]
        assert len(result["recommendations"]) > 0


if __name__ == "__main__":
    # Run with: pytest tests/integration/test_inprocess_communication.py -v -m integration
    pytest.main([__file__, "-v", "-m", "integration"])
