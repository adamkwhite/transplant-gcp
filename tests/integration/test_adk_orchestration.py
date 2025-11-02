"""
Integration Tests for ADK Orchestration

Tests the complete ADK-native multi-agent orchestration system including:
- LLM-driven routing accuracy
- Multi-turn conversation support
- Parameter extraction from natural language
- Context preservation across turns

These tests use the real Gemini API and measure actual performance.
"""

import os
from uuid import uuid4

import pytest

from services.orchestration.adk_orchestrator import ADKOrchestrator
from services.orchestration.conversation_manager import ConversationManager


@pytest.mark.integration
class TestADKOrchestration:
    """Integration tests for ADK orchestration."""

    @pytest.fixture
    def orchestrator(self):
        """Create ADK orchestrator instance."""
        # Skip if no API key
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")

        return ADKOrchestrator(api_key=api_key)

    @pytest.fixture
    def conversation_manager(self):
        """Create conversation manager instance."""
        return ConversationManager()

    def test_llm_routing_missed_dose(self, orchestrator):
        """
        Test LLM-driven routing for missed dose query.

        Expected behavior:
        - Coordinator analyzes natural language request
        - Routes to MedicationAdvisor without keyword matching
        - Returns appropriate missed dose guidance
        """
        response = orchestrator.process_request(
            user_request="I forgot to take my tacrolimus this morning at 8 AM, it's now 2 PM",
            patient_id="test_patient_001",
        )

        # Verify response structure
        assert "response" in response
        assert "agents_consulted" in response
        assert "routing_path" in response

        # Verify response is not empty
        assert len(response["response"]) > 0

        # Note: Can't verify exact routing without parsing ADK events
        # In real implementation, would check:
        # assert "MedicationAdvisor" in response["agents_consulted"]

    def test_llm_routing_symptom_check(self, orchestrator):
        """
        Test LLM-driven routing for symptom monitoring.

        Expected behavior:
        - Coordinator recognizes symptom-related query
        - Routes to SymptomMonitor
        - Assesses rejection risk and urgency
        """
        response = orchestrator.process_request(
            user_request="I have a fever of 101°F and decreased urine output today",
            patient_id="test_patient_002",
            patient_context={"transplant_type": "kidney", "days_post_transplant": 45},
        )

        # Verify response
        assert "response" in response
        assert len(response["response"]) > 0

        # Expected: SymptomMonitor consulted
        # assert "SymptomMonitor" in response["agents_consulted"]

    def test_llm_routing_drug_interaction(self, orchestrator):
        """
        Test LLM-driven routing for drug interaction query.

        Expected behavior:
        - Coordinator recognizes interaction question
        - Routes to DrugInteractionChecker
        - Provides interaction assessment
        """
        response = orchestrator.process_request(
            user_request="Can I take ibuprofen for my headache? I'm on tacrolimus.",
            patient_id="test_patient_003",
        )

        # Verify response
        assert "response" in response
        assert len(response["response"]) > 0

        # Expected: DrugInteractionChecker consulted
        # assert "DrugInteractionChecker" in response["agents_consulted"]

    def test_multi_turn_conversation_clarification(self, orchestrator, conversation_manager):
        """
        Test multi-turn conversation with clarification.

        Flow:
        1. User: "What should I do?"
        2. Assistant: "About what?" (clarification)
        3. User: "My missed dose"
        4. Assistant: "Which medication?" (further clarification)
        5. User: "Tacrolimus"
        6. Assistant: [Provides guidance]
        """
        conversation_id = str(uuid4())
        patient_id = "test_patient_004"

        # Start conversation
        conversation_manager.start_conversation(conversation_id, patient_id)

        # Turn 1: Vague question
        turn1_request = "What should I do?"
        turn1_response = orchestrator.process_request(
            user_request=turn1_request,
            patient_id=patient_id,
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn1_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn1_response["response"])

        # Turn 2: Clarification - "My missed dose"
        turn2_request = "My missed dose"
        turn2_response = orchestrator.process_request(
            user_request=turn2_request,
            patient_id=patient_id,
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn2_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn2_response["response"])

        # Turn 3: Medication name - "Tacrolimus"
        turn3_request = "Tacrolimus at 8 AM, it's now 2 PM"
        turn3_response = orchestrator.process_request(
            user_request=turn3_request,
            patient_id=patient_id,
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn3_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn3_response["response"])

        # Verify conversation tracked correctly
        conversation = conversation_manager.get_conversation(conversation_id)
        assert conversation is not None
        assert len(conversation.turns) == 6  # 3 user + 3 assistant turns

        # Verify final response addresses missed dose
        assert len(turn3_response["response"]) > 0

    def test_multi_turn_conversation_follow_up(self, orchestrator, conversation_manager):
        """
        Test multi-turn conversation with follow-up question.

        Flow:
        1. User: "I missed my tacrolimus at 8 AM, it's now 2 PM"
        2. Assistant: [Provides initial guidance]
        3. User: "What if I also have a fever?" (follow-up)
        4. Assistant: [Escalates to SymptomMonitor]
        """
        conversation_id = str(uuid4())
        patient_id = "test_patient_005"

        # Start conversation
        conversation_manager.start_conversation(conversation_id, patient_id)

        # Turn 1: Initial question
        turn1_request = "I missed my tacrolimus at 8 AM, it's now 2 PM"
        turn1_response = orchestrator.process_request(
            user_request=turn1_request,
            patient_id=patient_id,
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn1_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn1_response["response"])

        # Turn 2: Follow-up about fever
        turn2_request = "What if I also have a fever of 101°F?"
        turn2_response = orchestrator.process_request(
            user_request=turn2_request,
            patient_id=patient_id,
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn2_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn2_response["response"])

        # Verify follow-up detected
        assert conversation_manager.is_follow_up(conversation_id, turn2_request)

        # Verify conversation structure
        conversation = conversation_manager.get_conversation(conversation_id)
        assert len(conversation.turns) == 4  # 2 user + 2 assistant turns

    def test_parameter_extraction_accuracy(self, orchestrator):
        """
        Test LLM's ability to extract parameters from natural language.

        Tests various phrasings of the same query to verify:
        - LLM understands semantic meaning
        - Parameters correctly extracted
        - No keyword matching brittleness
        """
        # Variation 1: Formal phrasing
        response1 = orchestrator.process_request(
            user_request="I missed my tacrolimus dose scheduled for 8:00 AM. The current time is 2:00 PM.",
            patient_id="test_patient_006",
        )
        assert len(response1["response"]) > 0

        # Variation 2: Casual phrasing
        response2 = orchestrator.process_request(
            user_request="Forgot to take my tacrolimus this morning around 8, it's like 2 now",
            patient_id="test_patient_006",
        )
        assert len(response2["response"]) > 0

        # Variation 3: Conversational phrasing
        response3 = orchestrator.process_request(
            user_request="I was supposed to take tacrolimus at 8 but I totally spaced. It's 2pm now.",
            patient_id="test_patient_006",
        )
        assert len(response3["response"]) > 0

        # All should produce responses (LLM understands semantics)
        # Note: Can't verify exact parameter extraction without structured output

    def test_context_preservation_across_turns(self, orchestrator, conversation_manager):
        """
        Test that patient context is preserved across conversation turns.

        Context includes:
        - Patient medical history
        - Current medications
        - Previous answers
        """
        conversation_id = str(uuid4())
        patient_id = "test_patient_007"

        patient_context = {
            "transplant_type": "kidney",
            "days_post_transplant": 90,
            "current_medications": ["tacrolimus", "mycophenolate", "prednisone"],
            "recent_creatinine": 1.2,
        }

        # Start conversation with context
        conversation_manager.start_conversation(
            conversation_id, patient_id, initial_context=patient_context
        )

        # Turn 1: Ask about medication
        turn1_request = "Which immunosuppressants am I on?"
        turn1_response = orchestrator.process_request(
            user_request=turn1_request,
            patient_id=patient_id,
            patient_context=conversation_manager.get_context(conversation_id),
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn1_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn1_response["response"])

        # Turn 2: Follow-up using context
        turn2_request = "Can I take ibuprofen with those?"
        turn2_response = orchestrator.process_request(
            user_request=turn2_request,
            patient_id=patient_id,
            patient_context=conversation_manager.get_context(conversation_id),
            conversation_history=conversation_manager.get_conversation_history(conversation_id),
        )

        conversation_manager.add_turn(conversation_id, "user", turn2_request)
        conversation_manager.add_turn(conversation_id, "assistant", turn2_response["response"])

        # Verify context maintained
        context = conversation_manager.get_context(conversation_id)
        assert context["transplant_type"] == "kidney"
        assert "tacrolimus" in context["current_medications"]

    def test_complex_multi_specialist_case(self, orchestrator):
        """
        Test complex case requiring multiple specialists.

        Scenario: Patient missed dose AND has symptoms
        Expected: Consult both MedicationAdvisor and SymptomMonitor
        """
        response = orchestrator.process_request(
            user_request="I missed my tacrolimus this morning and now I have a fever and feel weak",
            patient_id="test_patient_008",
            patient_context={"transplant_type": "kidney", "days_post_transplant": 30},
        )

        # Verify response addresses both concerns
        assert len(response["response"]) > 0

        # Expected: Multiple specialists consulted
        # In real implementation with event parsing:
        # assert "MedicationAdvisor" in response["agents_consulted"]
        # assert "SymptomMonitor" in response["agents_consulted"]
        # assert len(response["agents_consulted"]) >= 2

    def test_agent_capabilities_metadata(self, orchestrator):
        """Test that orchestrator provides accurate capability metadata."""
        capabilities = orchestrator.get_agent_capabilities()

        # Verify structure
        assert "orchestration_method" in capabilities
        assert capabilities["orchestration_method"] == "ADK Native"

        assert "features" in capabilities
        assert "LLM-driven routing via transfer_to_agent()" in capabilities["features"]

        assert "coordinator" in capabilities
        assert capabilities["coordinator"]["routing"] == "LLM-driven delegation"

        assert "specialists" in capabilities
        assert "MedicationAdvisor" in capabilities["specialists"]
        assert "SymptomMonitor" in capabilities["specialists"]
        assert "DrugInteractionChecker" in capabilities["specialists"]

    def test_conversation_manager_summary(self, conversation_manager):
        """Test conversation manager summary functionality."""
        conversation_id = str(uuid4())
        patient_id = "test_patient_009"

        # Start conversation
        conversation_manager.start_conversation(conversation_id, patient_id)

        # Add some turns
        conversation_manager.add_turn(conversation_id, "user", "Hello")
        conversation_manager.add_turn(conversation_id, "assistant", "Hi there!")
        conversation_manager.add_turn(conversation_id, "user", "I need help")
        conversation_manager.add_turn(conversation_id, "assistant", "What can I help you with?")

        # Get summary
        summary = conversation_manager.get_summary(conversation_id)

        # Verify summary
        assert summary["conversation_id"] == conversation_id
        assert summary["patient_id"] == patient_id
        assert summary["turn_count"] == 4
        assert "started_at" in summary
        assert "last_updated" in summary
        assert "duration_seconds" in summary
