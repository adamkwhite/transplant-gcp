"""
TransplantCoordinator Agent Implementation

Primary orchestration agent that routes patient requests to appropriate
specialist agents and synthesizes their responses.
"""

from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from services.config.adk_config import (
    COORDINATOR_CONFIG,
    DEFAULT_GENERATION_CONFIG,
    GEMINI_API_KEY,
)


class TransplantCoordinatorAgent:
    """
    ADK Coordinator Agent for routing and orchestrating specialist agents.

    This agent specializes in:
    - Analyzing patient requests to identify required specialist agents
    - Routing to MedicationAdvisor, SymptomMonitor, or DrugInteractionChecker
    - Coordinating multi-agent responses when multiple specialists needed
    - Synthesizing recommendations into comprehensive guidance
    """

    def __init__(
        self,
        api_key: str | None = None,
        medication_advisor: Any | None = None,
        symptom_monitor: Any | None = None,
        drug_interaction_checker: Any | None = None,
    ):
        """
        Initialize the TransplantCoordinator agent.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
            medication_advisor: MedicationAdvisorAgent instance (for delegation)
            symptom_monitor: SymptomMonitorAgent instance (for delegation)
            drug_interaction_checker: DrugInteractionCheckerAgent instance (for delegation)
        """
        self.api_key = api_key or GEMINI_API_KEY

        # Create ADK agent instance with generation config
        generate_config = types.GenerateContentConfig(
            temperature=DEFAULT_GENERATION_CONFIG["temperature"],
            max_output_tokens=int(DEFAULT_GENERATION_CONFIG["max_output_tokens"]),
            top_p=DEFAULT_GENERATION_CONFIG["top_p"],
            top_k=DEFAULT_GENERATION_CONFIG["top_k"],
        )

        self.agent = Agent(
            name=COORDINATOR_CONFIG["name"],
            model=COORDINATOR_CONFIG["model"],
            description=COORDINATOR_CONFIG["description"],
            instruction=COORDINATOR_CONFIG["instruction"],
            generate_content_config=generate_config,
        )

        # Store specialist agent references
        self.medication_advisor = medication_advisor
        self.symptom_monitor = symptom_monitor
        self.drug_interaction_checker = drug_interaction_checker

    def route_request(
        self,
        request: str,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Route patient request to appropriate specialist agent(s).

        Args:
            request: Patient request text (e.g., "I missed my tacrolimus dose")
            patient_id: Optional patient identifier
            patient_context: Optional patient medical context

        Returns:
            Dict with:
                - agents_consulted: List of specialist agents used
                - recommendations: Synthesized recommendations
                - specialist_responses: Individual agent outputs
                - coordinator_analysis: Overall assessment
                - confidence: Confidence score (0.0-1.0)
        """
        # Analyze request to determine routing
        routing_decision = self._analyze_routing(request)

        # Collect responses from specialist agents
        specialist_responses = self._consult_specialists(
            routing_decision=routing_decision,
            _request=request,
            _patient_id=patient_id,
            _patient_context=patient_context,
        )

        # Synthesize comprehensive response
        return self._synthesize_response(
            request=request,
            routing_decision=routing_decision,
            specialist_responses=specialist_responses,
        )

    def _analyze_routing(self, request: str) -> dict[str, Any]:
        """
        Analyze request to determine which specialist agents to consult.

        Args:
            request: Patient request text

        Returns:
            Dict with routing decisions and reasoning
        """
        # Use coordinator agent to determine routing
        prompt = f"""Analyze this patient request and determine which specialist agents to consult:

Request: {request}

Available agents:
- MedicationAdvisor: For missed doses, medication timing questions
- SymptomMonitor: For symptoms, side effects, rejection concerns
- DrugInteractionChecker: For drug interactions, new medications, food/supplement questions

Respond with JSON: {{
    "agents_needed": ["agent_name1", "agent_name2"],
    "reasoning": "explanation of why these agents are needed",
    "request_type": "missed_dose|symptom_check|interaction_check|multi_concern"
}}"""

        response = self.agent.run(prompt)  # type: ignore[attr-defined]

        # Parse routing decision (simplified for now)
        # In real implementation, parse JSON from response
        request_lower = request.lower()

        agents_needed = []
        if any(word in request_lower for word in ["missed", "late", "dose", "timing", "forgot"]):
            agents_needed.append("MedicationAdvisor")
        if any(
            word in request_lower
            for word in [
                "symptom",
                "feeling",
                "fever",
                "pain",
                "rejection",
                "urine",
                "weight",
            ]
        ):
            agents_needed.append("SymptomMonitor")
        if any(
            word in request_lower
            for word in ["interaction", "taking", "new medication", "food", "grapefruit"]
        ):
            agents_needed.append("DrugInteractionChecker")

        # Default to MedicationAdvisor if unclear
        if not agents_needed:
            agents_needed.append("MedicationAdvisor")

        return {
            "agents_needed": agents_needed,
            "reasoning": str(response),
            "request_type": self._classify_request_type(agents_needed),
        }

    def _classify_request_type(self, agents_needed: list[str]) -> str:
        """Classify request type based on agents needed."""
        if len(agents_needed) > 1:
            return "multi_concern"
        if "MedicationAdvisor" in agents_needed:
            return "missed_dose"
        if "SymptomMonitor" in agents_needed:
            return "symptom_check"
        if "DrugInteractionChecker" in agents_needed:
            return "interaction_check"
        return "general_inquiry"

    def _consult_specialists(
        self,
        routing_decision: dict[str, Any],
        _request: str,
        _patient_id: str | None,
        _patient_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Consult specialist agents based on routing decision.

        Args:
            routing_decision: Output from _analyze_routing
            _request: Patient request text (unused for now, will be used in Task 3.0)
            _patient_id: Patient identifier (unused for now, will be used in Task 3.0)
            _patient_context: Patient medical context (unused for now, will be used in Task 3.0)

        Returns:
            Dict with responses from each consulted agent
        """
        responses = {}

        agents_needed = routing_decision.get("agents_needed", [])

        # Consult MedicationAdvisor if needed
        if "MedicationAdvisor" in agents_needed and self.medication_advisor:
            # In real implementation, parse request to extract parameters
            # For now, return placeholder
            responses["MedicationAdvisor"] = {
                "agent": "MedicationAdvisor",
                "response": "Medication advisor analysis pending",
                "status": "consulted",
            }

        # Consult SymptomMonitor if needed
        if "SymptomMonitor" in agents_needed and self.symptom_monitor:
            responses["SymptomMonitor"] = {
                "agent": "SymptomMonitor",
                "response": "Symptom monitor analysis pending",
                "status": "consulted",
            }

        # Consult DrugInteractionChecker if needed
        if "DrugInteractionChecker" in agents_needed and self.drug_interaction_checker:
            responses["DrugInteractionChecker"] = {
                "agent": "DrugInteractionChecker",
                "response": "Drug interaction check pending",
                "status": "consulted",
            }

        return responses

    def _synthesize_response(
        self,
        request: str,
        routing_decision: dict[str, Any],
        specialist_responses: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synthesize specialist responses into comprehensive guidance.

        Args:
            request: Original patient request
            routing_decision: Routing analysis
            specialist_responses: Responses from specialist agents

        Returns:
            Synthesized response with comprehensive recommendations
        """
        # Build synthesis prompt
        prompt_parts = [
            f"Original request: {request}",
            f"\nRouting decision: {routing_decision['reasoning']}",
            "\nSpecialist responses:",
        ]

        for agent_name, response_data in specialist_responses.items():
            prompt_parts.append(f"- {agent_name}: {response_data['response']}")

        prompt_parts.append(
            "\nSynthesize a comprehensive response that integrates all specialist recommendations. "
            "Prioritize patient safety and provide clear, actionable guidance."
        )

        synthesis_prompt = "\n".join(prompt_parts)
        coordinator_response = self.agent.run(synthesis_prompt)  # type: ignore[attr-defined]

        return {
            "agents_consulted": list(specialist_responses.keys()),
            "recommendations": str(coordinator_response),
            "specialist_responses": specialist_responses,
            "coordinator_analysis": routing_decision["reasoning"],
            "request_type": routing_decision["request_type"],
            "confidence": 0.85,
            "agent_name": self.agent.name,
            "raw_response": str(coordinator_response),
        }

    def get_agent_capabilities(self) -> dict[str, Any]:
        """
        Get information about available specialist agents and their capabilities.

        Returns:
            Dict describing each specialist agent's role
        """
        return {
            "coordinator": {
                "name": "TransplantCoordinator",
                "role": "Primary orchestration and routing",
                "capabilities": [
                    "Request analysis and routing",
                    "Multi-agent coordination",
                    "Response synthesis",
                ],
            },
            "specialists": {
                "MedicationAdvisor": {
                    "role": "Missed dose analysis",
                    "handles": [
                        "Late/missed medication doses",
                        "Medication timing questions",
                        "Therapeutic windows",
                        "Rejection risk from non-adherence",
                    ],
                },
                "SymptomMonitor": {
                    "role": "Rejection symptom detection",
                    "handles": [
                        "Patient-reported symptoms",
                        "Rejection risk assessment",
                        "Urgency determination",
                        "Differential diagnosis",
                    ],
                },
                "DrugInteractionChecker": {
                    "role": "Medication safety validation",
                    "handles": [
                        "Drug-drug interactions",
                        "Drug-food interactions",
                        "Drug-supplement interactions",
                        "Interaction severity assessment",
                    ],
                },
            },
        }
