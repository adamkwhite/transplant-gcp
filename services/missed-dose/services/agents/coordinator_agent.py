"""
TransplantCoordinator Agent Implementation

Primary orchestration agent that routes patient requests to appropriate
specialist agents and synthesizes their responses.
"""

import asyncio
from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.adk.runners import Runner  # type: ignore[import-untyped]
from google.adk.sessions.in_memory_session_service import (
    InMemorySessionService,  # type: ignore[import-untyped]
)
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

        # Create Runner with in-memory session service
        self.runner = Runner(
            app_name="TransplantCoordinator",
            agent=self.agent,
            session_service=InMemorySessionService(),
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
        parallel: bool = True,
    ) -> dict[str, Any]:
        """
        Route patient request to appropriate specialist agent(s).

        Args:
            request: Patient request text (e.g., "I missed my tacrolimus dose")
            patient_id: Optional patient identifier
            patient_context: Optional patient medical context
            parallel: If True, consult specialists in parallel; if False, consult sequentially

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
            parallel=parallel,
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

        # Use Runner.run_async() with proper session/user context
        async def _run_agent():
            response_text = ""
            user_message = types.Content(role="user", parts=[types.Part(text=prompt)])

            # Create session if it doesn't exist
            session = await self.runner.session_service.get_session(  # type: ignore[attr-defined]
                app_name=self.runner.app_name,  # type: ignore[attr-defined]
                user_id="system",
                session_id="routing_analysis",
            )
            if not session:
                await self.runner.session_service.create_session(  # type: ignore[attr-defined]
                    app_name=self.runner.app_name,  # type: ignore[attr-defined]
                    user_id="system",
                    session_id="routing_analysis",
                )

            async for event in self.runner.run_async(  # type: ignore[attr-defined]
                user_id="system",
                session_id="routing_analysis",
                new_message=user_message,
            ):
                # Collect text from events
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            return response_text

        response = asyncio.run(_run_agent())

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
            for word in [
                "interaction",
                "taking",
                "new medication",
                "food",
                "grapefruit",
                "ibuprofen",
                "supplement",
            ]
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
        parallel: bool = True,
    ) -> dict[str, Any]:
        """
        Consult specialist agents based on routing decision.

        Args:
            routing_decision: Output from _analyze_routing
            _request: Patient request text (unused for now, will be used in Task 3.0)
            _patient_id: Patient identifier (unused for now, will be used in Task 3.0)
            _patient_context: Patient medical context (unused for now, will be used in Task 3.0)
            parallel: If True, consult agents in parallel; if False, sequentially

        Returns:
            Dict with responses from each consulted agent
        """
        agents_needed = routing_decision.get("agents_needed", [])

        if parallel:
            # Parallel execution using asyncio.gather()
            return asyncio.run(self._consult_specialists_parallel(agents_needed))
        else:
            # Sequential execution
            return self._consult_specialists_sequential(agents_needed)

    def _consult_specialists_sequential(self, agents_needed: list[str]) -> dict[str, Any]:
        """Consult specialists sequentially (one after another)."""
        responses = {}

        # Consult MedicationAdvisor if needed
        if "MedicationAdvisor" in agents_needed and self.medication_advisor:
            responses["MedicationAdvisor"] = {
                "agent": "MedicationAdvisor",
                "response": "Medication advisor analysis completed",
                "status": "success",
                "extraction_confidence": 0.85,
            }

        # Consult SymptomMonitor if needed
        if "SymptomMonitor" in agents_needed and self.symptom_monitor:
            responses["SymptomMonitor"] = {
                "agent": "SymptomMonitor",
                "response": "Symptom monitor analysis completed",
                "status": "success",
                "extraction_confidence": 0.80,
            }

        # Consult DrugInteractionChecker if needed
        if "DrugInteractionChecker" in agents_needed and self.drug_interaction_checker:
            responses["DrugInteractionChecker"] = {
                "agent": "DrugInteractionChecker",
                "response": "Drug interaction check completed",
                "status": "success",
                "extraction_confidence": 0.90,
            }

        return responses

    async def _consult_specialists_parallel(self, agents_needed: list[str]) -> dict[str, Any]:
        """Consult specialists in parallel using asyncio.gather()."""
        tasks = []
        agent_names = []

        # Create tasks for each needed agent
        if "MedicationAdvisor" in agents_needed and self.medication_advisor:
            tasks.append(self._consult_medication_advisor_async())
            agent_names.append("MedicationAdvisor")

        if "SymptomMonitor" in agents_needed and self.symptom_monitor:
            tasks.append(self._consult_symptom_monitor_async())
            agent_names.append("SymptomMonitor")

        if "DrugInteractionChecker" in agents_needed and self.drug_interaction_checker:
            tasks.append(self._consult_drug_interaction_async())
            agent_names.append("DrugInteractionChecker")

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks)

        # Combine results into dict
        responses = {}
        for name, result in zip(agent_names, results):
            responses[name] = result

        return responses

    async def _consult_medication_advisor_async(self) -> dict[str, Any]:
        """Async consultation with MedicationAdvisor."""
        # Simulate async work (in real implementation, would call agent.run_async())
        await asyncio.sleep(0.1)
        return {
            "agent": "MedicationAdvisor",
            "response": "Medication advisor analysis completed",
            "status": "success",
            "extraction_confidence": 0.85,
        }

    async def _consult_symptom_monitor_async(self) -> dict[str, Any]:
        """Async consultation with SymptomMonitor."""
        await asyncio.sleep(0.1)
        return {
            "agent": "SymptomMonitor",
            "response": "Symptom monitor analysis completed",
            "status": "success",
            "extraction_confidence": 0.80,
        }

    async def _consult_drug_interaction_async(self) -> dict[str, Any]:
        """Async consultation with DrugInteractionChecker."""
        await asyncio.sleep(0.1)
        return {
            "agent": "DrugInteractionChecker",
            "response": "Drug interaction check completed",
            "status": "success",
            "extraction_confidence": 0.90,
        }

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

        # Use Runner.run_async() with proper session/user context
        async def _run_agent():
            synthesis_text = ""
            user_message = types.Content(role="user", parts=[types.Part(text=synthesis_prompt)])

            # Create session if it doesn't exist
            session = await self.runner.session_service.get_session(  # type: ignore[attr-defined]
                app_name=self.runner.app_name,  # type: ignore[attr-defined]
                user_id="system",
                session_id="synthesis",
            )
            if not session:
                await self.runner.session_service.create_session(  # type: ignore[attr-defined]
                    app_name=self.runner.app_name,  # type: ignore[attr-defined]
                    user_id="system",
                    session_id="synthesis",
                )

            async for event in self.runner.run_async(  # type: ignore[attr-defined]
                user_id="system",
                session_id="synthesis",
                new_message=user_message,
            ):
                # Collect text from events
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            synthesis_text += part.text
            return synthesis_text

        coordinator_response = asyncio.run(_run_agent())

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
