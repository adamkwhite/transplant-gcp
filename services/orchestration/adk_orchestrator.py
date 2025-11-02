"""
ADK-Native Multi-Agent Orchestrator

Uses Google ADK's built-in orchestration features:
- LLM-driven delegation via transfer_to_agent()
- Shared session state for context management
- AutoFlow for conversation handling

This orchestrator wraps ADK's coordinator/dispatcher pattern.
"""

from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.adk.runners import Runner  # type: ignore[import-untyped]
from google.adk.sessions import InMemorySessionService  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from services.config.adk_config import (
    COORDINATOR_CONFIG,
    DEFAULT_GENERATION_CONFIG,
    DRUG_INTERACTION_CONFIG,
    GEMINI_API_KEY,
    MEDICATION_ADVISOR_CONFIG,
    SYMPTOM_MONITOR_CONFIG,
)


class ADKOrchestrator:
    """
    ADK-native orchestrator using built-in multi-agent capabilities.

    Architecture:
        TransplantCoordinator (root)
        ├── MedicationAdvisor (sub-agent)
        ├── SymptomMonitor (sub-agent)
        └── DrugInteractionChecker (sub-agent)

    Routing: LLM-driven via transfer_to_agent()
    State: Shared session.state across hierarchy
    Conversations: Handled by ADK's AutoFlow
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize ADK orchestrator with coordinator and specialist agents.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
        """
        self.api_key = api_key or GEMINI_API_KEY

        # Create generation config
        generate_config = types.GenerateContentConfig(
            temperature=DEFAULT_GENERATION_CONFIG["temperature"],
            max_output_tokens=int(DEFAULT_GENERATION_CONFIG["max_output_tokens"]),
            top_p=DEFAULT_GENERATION_CONFIG["top_p"],
            top_k=DEFAULT_GENERATION_CONFIG["top_k"],
        )

        # Create specialist agents
        self.medication_advisor = Agent(
            name=MEDICATION_ADVISOR_CONFIG["name"],
            model=MEDICATION_ADVISOR_CONFIG["model"],
            description=MEDICATION_ADVISOR_CONFIG["description"],
            instruction=MEDICATION_ADVISOR_CONFIG["instruction"],
            generate_content_config=generate_config,
        )

        self.symptom_monitor = Agent(
            name=SYMPTOM_MONITOR_CONFIG["name"],
            model=SYMPTOM_MONITOR_CONFIG["model"],
            description=SYMPTOM_MONITOR_CONFIG["description"],
            instruction=SYMPTOM_MONITOR_CONFIG["instruction"],
            generate_content_config=generate_config,
        )

        self.drug_interaction_checker = Agent(
            name=DRUG_INTERACTION_CONFIG["name"],
            model=DRUG_INTERACTION_CONFIG["model"],
            description=DRUG_INTERACTION_CONFIG["description"],
            instruction=DRUG_INTERACTION_CONFIG["instruction"],
            generate_content_config=generate_config,
        )

        # Create coordinator agent with specialists as sub-agents
        # ADK will handle transfer_to_agent() routing automatically via AutoFlow
        self.coordinator = Agent(
            name=COORDINATOR_CONFIG["name"],
            model=COORDINATOR_CONFIG["model"],
            description=COORDINATOR_CONFIG["description"],
            instruction=self._build_coordinator_instruction(),
            generate_content_config=generate_config,
            sub_agents=[  # Establishes parent-child hierarchy
                self.medication_advisor,
                self.symptom_monitor,
                self.drug_interaction_checker,
            ],
        )

    def _build_coordinator_instruction(self) -> str:
        """
        Build comprehensive coordinator instruction with routing guidance.

        Instructs LLM on when to use transfer_to_agent() for delegation.
        """
        return """You are the TransplantCoordinator for a medication adherence system.

**Your Role:**
Analyze patient requests and route to appropriate specialist agents using transfer_to_agent().

**Available Specialists:**

1. **MedicationAdvisor**
   - When to use: Missed doses, medication timing, adherence questions
   - Handles: "I forgot my tacrolimus", "Should I take it now?", "When is my next dose?"
   - Use: transfer_to_agent(agent_name='MedicationAdvisor')

2. **SymptomMonitor**
   - When to use: Symptoms, side effects, rejection concerns
   - Handles: "I have a fever", "Feeling weak", "Is this rejection?"
   - Use: transfer_to_agent(agent_name='SymptomMonitor')

3. **DrugInteractionChecker**
   - When to use: Drug interactions, new medications, food/supplements
   - Handles: "Can I take ibuprofen?", "Is grapefruit safe?", "Starting new antibiotic"
   - Use: transfer_to_agent(agent_name='DrugInteractionChecker')

**Multi-Specialist Cases:**
For complex cases requiring multiple specialists:
1. Transfer to first specialist
2. Await response
3. Transfer to second specialist with context
4. Synthesize final recommendation

**Priority:**
- Patient safety first
- Clear, actionable guidance
- Escalate to doctor when appropriate

**Examples:**

User: "I missed my tacrolimus dose this morning, what should I do?"
Action: transfer_to_agent(agent_name='MedicationAdvisor')

User: "I have a fever and decreased urine output"
Action: transfer_to_agent(agent_name='SymptomMonitor')

User: "Can I take Advil for headache?"
Action: transfer_to_agent(agent_name='DrugInteractionChecker')

User: "I missed my dose and now have a fever"
Action: transfer_to_agent(agent_name='MedicationAdvisor') first, then SymptomMonitor
"""

    def process_request(
        self,
        user_request: str,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        Process patient request using ADK's native orchestration.

        ADK handles:
        - LLM-driven routing via transfer_to_agent()
        - Session state management
        - Multi-turn conversation context
        - Event streaming

        Args:
            user_request: Patient's natural language request
            patient_id: Optional patient identifier
            patient_context: Optional patient medical context
            conversation_history: Optional prior conversation turns

        Returns:
            Dict with:
                - response: Final response to patient
                - agents_consulted: List of specialist agents used
                - routing_path: Sequence of agent transfers
                - state: Final session state
                - raw_events: Raw ADK events (for debugging)
        """
        # Build request with context
        full_request = self._build_request_with_context(
            user_request=user_request,
            patient_id=patient_id,
            patient_context=patient_context,
            conversation_history=conversation_history,
        )

        # Create a runner to execute the coordinator agent
        # The runner handles the event loop and session management
        runner = Runner(
            agent=self.coordinator,
            app_name="transplant_medication_adherence",
            session_service=InMemorySessionService(),
        )

        # Run the coordinator agent using the runner
        # ADK's Runner + AutoFlow automatically handles:
        # - transfer_to_agent() function calls
        # - Routing to sub-agents
        # - Session state management
        # - Multi-turn context
        response_text = ""
        for event in runner.run(
            user_id=patient_id or "default_user",
            session_id="session_" + (patient_id or "default"),
            new_message=full_request,
        ):
            # Collect text from events
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        # Parse response
        return self._parse_orchestrator_response(response_text)

    def _build_request_with_context(
        self,
        user_request: str,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
        conversation_history: list[dict[str, str]] | None,
    ) -> str:
        """Build enriched request with patient context and history."""
        parts = []

        # Add conversation history if present
        if conversation_history:
            parts.append("**Previous Conversation:**")
            for turn in conversation_history[-3:]:  # Last 3 turns for context
                role = turn.get("role", "user")
                content = turn.get("content", "")
                parts.append(f"{role.capitalize()}: {content}")
            parts.append("")

        # Add patient context if present
        if patient_id:
            parts.append(f"**Patient ID:** {patient_id}")

        if patient_context:
            parts.append("**Patient Context:**")
            for key, value in patient_context.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        # Add current request
        parts.append("**Current Request:**")
        parts.append(user_request)

        return "\n".join(parts)

    def _parse_orchestrator_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK orchestrator response into structured format.

        Args:
            response: Raw ADK agent response

        Returns:
            Structured dict with response data
        """
        response_text = str(response)

        # Extract metadata from ADK response
        # In real implementation, parse events to extract routing path
        return {
            "response": response_text,
            "agents_consulted": self._extract_agents_consulted(response),
            "routing_path": self._extract_routing_path(response),
            "orchestrator": "ADK",
            "raw_response": response_text,
        }

    def _extract_agents_consulted(self, _response: Any) -> list[str]:
        """
        Extract which specialist agents were consulted.

        Args:
            _response: ADK response object (unused - would parse events)

        Returns:
            List of agent names that were invoked
        """
        # Parse ADK events to find transfer_to_agent calls
        # For now, return empty list (implement by parsing events)
        return []

    def _extract_routing_path(self, _response: Any) -> list[str]:
        """
        Extract the routing path (sequence of agent transfers).

        Args:
            _response: ADK response object (unused - would parse events)

        Returns:
            Ordered list of agents in routing path
        """
        # Parse ADK events to reconstruct routing sequence
        # For now, return coordinator only
        return ["TransplantCoordinator"]

    def get_agent_capabilities(self) -> dict[str, Any]:
        """
        Get information about available agents and their capabilities.

        Returns:
            Dict describing coordinator and specialist capabilities
        """
        return {
            "orchestration_method": "ADK Native",
            "features": [
                "LLM-driven routing via transfer_to_agent()",
                "Shared session state",
                "Multi-turn conversation support",
                "Automatic context management",
            ],
            "coordinator": {
                "name": self.coordinator.name,
                "model": COORDINATOR_CONFIG["model"],
                "routing": "LLM-driven delegation",
            },
            "specialists": {
                "MedicationAdvisor": {
                    "name": self.medication_advisor.name,
                    "model": MEDICATION_ADVISOR_CONFIG["model"],
                    "handles": [
                        "Missed medication doses",
                        "Medication timing questions",
                        "Therapeutic windows",
                        "Rejection risk from non-adherence",
                    ],
                },
                "SymptomMonitor": {
                    "name": self.symptom_monitor.name,
                    "model": SYMPTOM_MONITOR_CONFIG["model"],
                    "handles": [
                        "Patient-reported symptoms",
                        "Rejection risk assessment",
                        "Urgency determination",
                        "Differential diagnosis",
                    ],
                },
                "DrugInteractionChecker": {
                    "name": self.drug_interaction_checker.name,
                    "model": DRUG_INTERACTION_CONFIG["model"],
                    "handles": [
                        "Drug-drug interactions",
                        "Drug-food interactions",
                        "Drug-supplement interactions",
                        "Interaction severity assessment",
                    ],
                },
            },
        }
