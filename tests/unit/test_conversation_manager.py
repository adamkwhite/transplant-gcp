"""Unit tests for ConversationManager."""

import pytest

from services.orchestration.conversation_manager import (
    ConversationManager,
)


class TestConversationManager:
    """Test suite for ConversationManager."""

    @pytest.fixture
    def manager(self):
        """Create a ConversationManager instance."""
        return ConversationManager()

    @pytest.fixture
    def conversation_id(self):
        """Standard conversation ID."""
        return "test_conv_001"

    @pytest.fixture
    def patient_id(self):
        """Standard patient ID."""
        return "patient_001"

    def test_start_conversation(self, manager, conversation_id, patient_id):
        """Test starting a new conversation."""
        conversation = manager.start_conversation(
            conversation_id=conversation_id,
            patient_id=patient_id,
            initial_context={"medications": ["tacrolimus"]},
        )

        assert conversation.conversation_id == conversation_id
        assert conversation.patient_id == patient_id
        assert conversation.context == {"medications": ["tacrolimus"]}
        assert len(conversation.turns) == 0

    def test_start_conversation_without_context(self, manager, conversation_id, patient_id):
        """Test starting conversation without initial context."""
        conversation = manager.start_conversation(
            conversation_id=conversation_id, patient_id=patient_id
        )

        assert conversation.context == {}

    def test_add_turn(self, manager, conversation_id, patient_id):
        """Test adding a turn to conversation."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)

        turn = manager.add_turn(
            conversation_id=conversation_id,
            role="user",
            content="I forgot my medication",
            metadata={"intent": "missed_dose"},
        )

        assert turn.role == "user"
        assert turn.content == "I forgot my medication"
        assert turn.metadata == {"intent": "missed_dose"}

    def test_add_turn_nonexistent_conversation(self, manager, conversation_id):
        """Test adding turn to non-existent conversation raises error."""
        with pytest.raises(ValueError, match="Conversation .* not found"):
            manager.add_turn(conversation_id=conversation_id, role="user", content="Test")

    def test_get_conversation(self, manager, conversation_id, patient_id):
        """Test retrieving a conversation."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)

        conversation = manager.get_conversation(conversation_id)
        assert conversation is not None
        assert conversation.conversation_id == conversation_id

    def test_get_conversation_not_found(self, manager):
        """Test retrieving non-existent conversation returns None."""
        conversation = manager.get_conversation("nonexistent")
        assert conversation is None

    def test_get_conversation_history(self, manager, conversation_id, patient_id):
        """Test getting conversation history."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "Hello")
        manager.add_turn(conversation_id, "assistant", "Hi there")

        history = manager.get_conversation_history(conversation_id)

        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there"}

    def test_get_conversation_history_nonexistent(self, manager):
        """Test getting history for non-existent conversation returns empty list."""
        history = manager.get_conversation_history("nonexistent")
        assert history == []

    def test_get_conversation_history_with_limit(self, manager, conversation_id, patient_id):
        """Test getting limited conversation history."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "Turn 1")
        manager.add_turn(conversation_id, "assistant", "Turn 2")
        manager.add_turn(conversation_id, "user", "Turn 3")
        manager.add_turn(conversation_id, "assistant", "Turn 4")

        history = manager.get_conversation_history(conversation_id, max_turns=2)

        assert len(history) == 2
        assert history[0]["content"] == "Turn 3"
        assert history[1]["content"] == "Turn 4"

    def test_update_context(self, manager, conversation_id, patient_id):
        """Test updating conversation context."""
        manager.start_conversation(
            conversation_id=conversation_id,
            patient_id=patient_id,
            initial_context={"meds": ["tacrolimus"]},
        )

        manager.update_context(conversation_id, {"symptoms": ["fever"]})

        context = manager.get_context(conversation_id)
        assert context["meds"] == ["tacrolimus"]
        assert context["symptoms"] == ["fever"]

    def test_update_context_nonexistent_conversation(self, manager, conversation_id):
        """Test updating context for non-existent conversation raises error."""
        with pytest.raises(ValueError, match="Conversation .* not found"):
            manager.update_context(conversation_id, {"test": "value"})

    def test_get_context(self, manager, conversation_id, patient_id):
        """Test getting conversation context."""
        manager.start_conversation(
            conversation_id=conversation_id,
            patient_id=patient_id,
            initial_context={"key": "value"},
        )

        context = manager.get_context(conversation_id)
        assert context == {"key": "value"}

    def test_get_context_nonexistent_conversation(self, manager):
        """Test getting context for non-existent conversation returns empty dict."""
        context = manager.get_context("nonexistent")
        assert context == {}

    def test_is_follow_up_with_no_history(self, manager, conversation_id):
        """Test follow-up detection with no conversation history."""
        # No conversation started
        assert not manager.is_follow_up(conversation_id, "What about that?")

    def test_is_follow_up_with_empty_conversation(self, manager, conversation_id, patient_id):
        """Test follow-up detection with empty conversation."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)

        assert not manager.is_follow_up(conversation_id, "What about that?")

    def test_is_follow_up_short_with_indicators(self, manager, conversation_id, patient_id):
        """Test follow-up detection with short input and indicators."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "I missed my dose")
        manager.add_turn(conversation_id, "assistant", "Which medication?")

        # Short inputs with indicators
        assert manager.is_follow_up(conversation_id, "What about it?")
        assert manager.is_follow_up(conversation_id, "That one")
        assert manager.is_follow_up(conversation_id, "Yes please")
        assert manager.is_follow_up(conversation_id, "Also this")

    def test_is_follow_up_medium_with_strong_indicators(self, manager, conversation_id, patient_id):
        """Test follow-up detection with medium input and strong indicators."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "I have symptoms")

        # Medium-length inputs with strong indicators
        assert manager.is_follow_up(conversation_id, "What about the fever I mentioned?")
        assert manager.is_follow_up(conversation_id, "What if I also have chills?")
        assert manager.is_follow_up(conversation_id, "And also some weakness in my legs")

    def test_is_follow_up_long_input_no_indicators(self, manager, conversation_id, patient_id):
        """Test follow-up detection rejects long input without indicators."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "I missed my dose")

        # Long input without indicators - should not be detected as follow-up
        assert not manager.is_follow_up(
            conversation_id,
            "I am experiencing severe headaches and nausea this morning after breakfast",
        )

    def test_get_summary(self, manager, conversation_id, patient_id):
        """Test getting conversation summary."""
        manager.start_conversation(
            conversation_id=conversation_id,
            patient_id=patient_id,
            initial_context={"med": "tacrolimus"},
        )
        manager.add_turn(conversation_id, "user", "Question")
        manager.add_turn(conversation_id, "assistant", "Answer")

        summary = manager.get_summary(conversation_id)

        assert summary["conversation_id"] == conversation_id
        assert summary["patient_id"] == patient_id
        assert summary["turn_count"] == 2
        assert "started_at" in summary
        assert "last_updated" in summary
        assert "duration_seconds" in summary
        assert summary["context_keys"] == ["med"]

    def test_get_summary_nonexistent_conversation(self, manager):
        """Test getting summary for non-existent conversation returns empty dict."""
        summary = manager.get_summary("nonexistent")
        assert summary == {}

    def test_end_conversation(self, manager, conversation_id, patient_id):
        """Test ending a conversation."""
        manager.start_conversation(conversation_id=conversation_id, patient_id=patient_id)
        manager.add_turn(conversation_id, "user", "Test")

        summary = manager.end_conversation(conversation_id)

        assert summary["conversation_id"] == conversation_id
        assert summary["turn_count"] == 1

    def test_end_conversation_nonexistent(self, manager):
        """Test ending non-existent conversation returns empty dict."""
        summary = manager.end_conversation("nonexistent")
        assert summary == {}
