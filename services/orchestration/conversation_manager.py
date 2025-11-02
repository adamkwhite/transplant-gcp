"""
Conversation Manager for Multi-Turn Interactions

Manages conversation history and context across multiple turns.
Integrates with ADK orchestrator for seamless multi-turn support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """Represents a complete conversation with a patient."""

    conversation_id: str
    patient_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages multi-turn conversations for ADK orchestrator.

    Features:
    - Conversation history tracking
    - Context preservation across turns
    - Follow-up question handling
    - Conversation state management

    Example Multi-Turn Flow:
        User: "What should I do?"
        Assistant: "About what specifically? A missed dose, symptoms, or medication interaction?"
        User: "About my missed dose"
        Assistant: "Which medication did you miss?"
        User: "Tacrolimus at 8 AM"
        Assistant: [Routes to MedicationAdvisor with full context]
    """

    def __init__(self):
        """Initialize conversation manager."""
        self.conversations: dict[str, Conversation] = {}

    def start_conversation(
        self,
        conversation_id: str,
        patient_id: str,
        initial_context: dict[str, Any] | None = None,
    ) -> Conversation:
        """
        Start a new conversation.

        Args:
            conversation_id: Unique conversation identifier
            patient_id: Patient identifier
            initial_context: Optional initial context (patient history, medications)

        Returns:
            New Conversation object
        """
        conversation = Conversation(
            conversation_id=conversation_id,
            patient_id=patient_id,
            context=initial_context or {},
        )
        self.conversations[conversation_id] = conversation
        return conversation

    def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationTurn:
        """
        Add a turn to the conversation.

        Args:
            conversation_id: Conversation identifier
            role: "user" or "assistant"
            content: Turn content
            metadata: Optional metadata (agents_consulted, routing_path, etc.)

        Returns:
            ConversationTurn object
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        turn = ConversationTurn(role=role, content=content, metadata=metadata or {})

        conversation = self.conversations[conversation_id]
        conversation.turns.append(turn)
        conversation.last_updated = datetime.now()

        return turn

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation object or None if not found
        """
        return self.conversations.get(conversation_id)

    def get_conversation_history(
        self, conversation_id: str, max_turns: int | None = None
    ) -> list[dict[str, str]]:
        """
        Get conversation history in ADK-compatible format.

        Args:
            conversation_id: Conversation identifier
            max_turns: Optional limit on number of turns to return

        Returns:
            List of dicts with role and content
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return []

        turns = conversation.turns
        if max_turns:
            turns = turns[-max_turns:]

        return [{"role": turn.role, "content": turn.content} for turn in turns]

    def update_context(self, conversation_id: str, context_updates: dict[str, Any]) -> None:
        """
        Update conversation context.

        Args:
            conversation_id: Conversation identifier
            context_updates: Dict of context key-value pairs to update
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        conversation = self.conversations[conversation_id]
        conversation.context.update(context_updates)
        conversation.last_updated = datetime.now()

    def get_context(self, conversation_id: str) -> dict[str, Any]:
        """
        Get conversation context.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Context dictionary
        """
        conversation = self.conversations.get(conversation_id)
        return conversation.context if conversation else {}

    def is_follow_up(self, conversation_id: str, user_input: str) -> bool:
        """
        Detect if user input is a follow-up to previous conversation.

        Heuristics:
        - Conversation has prior turns
        - Input is short and context-dependent
        - Input uses pronouns ("it", "that", "this")
        - Input is incomplete without context

        Args:
            conversation_id: Conversation identifier
            user_input: User's current input

        Returns:
            True if likely a follow-up question
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation or len(conversation.turns) == 0:
            return False

        # Check for follow-up indicators
        follow_up_indicators = [
            # Pronouns
            "it",
            "that",
            "this",
            "them",
            "those",
            # Short clarifications
            "yes",
            "no",
            "yeah",
            "yep",
            "nope",
            # Follow-up phrases
            "what about",
            "and also",
            "also",
            "plus",
            "in addition",
        ]

        input_lower = user_input.lower()

        # Check if input is short and contains follow-up indicators
        if len(user_input.split()) <= 5:
            for indicator in follow_up_indicators:
                if indicator in input_lower:
                    return True

        return False

    def get_summary(self, conversation_id: str) -> dict[str, Any]:
        """
        Get conversation summary.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Dict with conversation statistics and metadata
        """
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            return {}

        return {
            "conversation_id": conversation.conversation_id,
            "patient_id": conversation.patient_id,
            "turn_count": len(conversation.turns),
            "started_at": conversation.started_at.isoformat(),
            "last_updated": conversation.last_updated.isoformat(),
            "duration_seconds": (
                conversation.last_updated - conversation.started_at
            ).total_seconds(),
            "context_keys": list(conversation.context.keys()),
        }

    def end_conversation(self, conversation_id: str) -> dict[str, Any]:
        """
        End a conversation and return final summary.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation summary
        """
        summary = self.get_summary(conversation_id)

        # Optionally: persist conversation to database
        # For now, keep in memory (could be cleared by garbage collection)

        return summary
