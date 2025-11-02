"""
TransplantCoordinator Agent Implementation

Primary orchestration agent that routes patient requests to appropriate
specialist agents and synthesizes their responses.
"""

import asyncio
import json
import re
from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from services.agents.parameter_extractor import ParameterExtractor
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

        # Initialize parameter extractor
        self.parameter_extractor = ParameterExtractor(api_key=self.api_key)

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
            parallel: If True, consult specialists in parallel (default: True)

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

        # Collect responses from specialist agents (parallel or sequential)
        if parallel and len(routing_decision.get("agents_needed", [])) > 1:
            # Use async parallel consultation for multiple agents
            specialist_responses = asyncio.run(
                self._consult_specialists_async(
                    routing_decision=routing_decision,
                    _request=request,
                    _patient_id=patient_id,
                    _patient_context=patient_context,
                )
            )
        else:
            # Use synchronous consultation
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

        Uses LLM to parse request and return structured JSON routing decision.

        Args:
            request: Patient request text

        Returns:
            Dict with routing decisions, reasoning, and extracted parameters
        """
        # Use coordinator agent to determine routing with structured output
        prompt = f"""Analyze this patient request and determine which specialist agents to consult:

Request: "{request}"

Available agents:
- MedicationAdvisor: For missed doses, medication timing questions, adherence concerns
- SymptomMonitor: For symptoms, side effects, rejection concerns, vital sign changes
- DrugInteractionChecker: For drug interactions, new medications, food/supplement questions

Respond with ONLY valid JSON (no markdown, no extra text):
{{
    "agents_needed": ["agent_name1", "agent_name2"],
    "reasoning": "explanation of why these agents are needed",
    "request_type": "missed_dose|symptom_check|interaction_check|multi_concern",
    "extracted_info": {{
        "medications": ["medication names if mentioned"],
        "symptoms": ["symptoms if mentioned"],
        "times_mentioned": ["times if mentioned"]
    }}
}}"""

        try:
            # Use run_async() which works with both ADK 1.16.0 and 1.17.0
            # run_async() returns an async generator, so we need to collect events
            async def _run_agent():
                response_text = ""
                async for event in self.agent.run_async(prompt):  # type: ignore[attr-defined]
                    # Collect text from events
                    if hasattr(event, "content") and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_text += part.text
                return response_text

            response_text = asyncio.run(_run_agent())

            # Parse JSON from response
            routing_decision = self._parse_json_response(response_text)

            # Validate and ensure required fields
            if "agents_needed" not in routing_decision:
                # Fallback to keyword-based routing
                return self._fallback_routing(request, response_text)

            # Ensure request_type is set
            if "request_type" not in routing_decision:
                routing_decision["request_type"] = self._classify_request_type(
                    routing_decision["agents_needed"]
                )

            return routing_decision

        except Exception as e:
            # Fallback to keyword-based routing on error
            print(f"Routing analysis error: {e}, using fallback")
            return self._fallback_routing(request, str(e))

    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""

        # Remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Extract content between code fences
            match = re.search(r"```(?:json)?\n(.*?)\n```", response_text, re.DOTALL)
            if match:
                response_text = match.group(1)

        # Try to parse JSON
        try:
            parsed: dict[str, Any] = json.loads(response_text)
            return parsed
        except json.JSONDecodeError:
            # Try to find JSON object in text
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                parsed_match: dict[str, Any] = json.loads(json_match.group(0))
                return parsed_match
            raise

    def _fallback_routing(self, request: str, llm_response: str) -> dict[str, Any]:
        """Fallback keyword-based routing when LLM parsing fails."""

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
            "reasoning": llm_response,
            "request_type": self._classify_request_type(agents_needed),
            "extracted_info": {},
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

        Extracts parameters from request and calls appropriate specialist methods.

        Args:
            routing_decision: Output from _analyze_routing
            _request: Patient request text
            _patient_id: Patient identifier
            _patient_context: Patient medical context

        Returns:
            Dict with responses from each consulted agent
        """
        responses = {}
        agents_needed = routing_decision.get("agents_needed", [])

        # Consult MedicationAdvisor if needed
        if "MedicationAdvisor" in agents_needed and self.medication_advisor:
            try:
                # Extract parameters for medication advisor
                params = self.parameter_extractor.extract_for_medication_advisor(_request)

                # Call medication advisor with extracted parameters
                med_response = self.medication_advisor.analyze_missed_dose(
                    medication=params.get("medication", "unknown"),
                    scheduled_time=params.get("scheduled_time", "unknown"),
                    current_time=params.get("current_time", "unknown"),
                    patient_id=_patient_id,
                    patient_context=_patient_context,
                )

                responses["MedicationAdvisor"] = {
                    "agent": "MedicationAdvisor",
                    "response": med_response,
                    "status": "success",
                    "extraction_confidence": params.get("confidence", 0.0),
                }
            except Exception as e:
                responses["MedicationAdvisor"] = {
                    "agent": "MedicationAdvisor",
                    "response": f"Error consulting medication advisor: {e}",
                    "status": "error",
                }

        # Consult SymptomMonitor if needed
        if "SymptomMonitor" in agents_needed and self.symptom_monitor:
            try:
                # Extract parameters for symptom monitor
                params = self.parameter_extractor.extract_for_symptom_monitor(_request)

                # Call symptom monitor with extracted parameters
                symptom_response = self.symptom_monitor.analyze_symptoms(
                    symptoms=params.get("symptoms", []),
                    patient_id=_patient_id,
                    patient_context=_patient_context,
                    vital_signs=params.get("vital_signs"),
                )

                responses["SymptomMonitor"] = {
                    "agent": "SymptomMonitor",
                    "response": symptom_response,
                    "status": "success",
                    "extraction_confidence": params.get("confidence", 0.0),
                }
            except Exception as e:
                responses["SymptomMonitor"] = {
                    "agent": "SymptomMonitor",
                    "response": f"Error consulting symptom monitor: {e}",
                    "status": "error",
                }

        # Consult DrugInteractionChecker if needed
        if "DrugInteractionChecker" in agents_needed and self.drug_interaction_checker:
            try:
                # Extract parameters for drug interaction checker
                params = self.parameter_extractor.extract_for_drug_interaction(_request)

                # Call drug interaction checker with extracted parameters
                interaction_response = self.drug_interaction_checker.check_interaction(
                    medications=params.get("medications", []),
                    patient_id=_patient_id,
                    patient_context=_patient_context,
                )

                responses["DrugInteractionChecker"] = {
                    "agent": "DrugInteractionChecker",
                    "response": interaction_response,
                    "status": "success",
                    "extraction_confidence": params.get("confidence", 0.0),
                }
            except Exception as e:
                responses["DrugInteractionChecker"] = {
                    "agent": "DrugInteractionChecker",
                    "response": f"Error consulting drug interaction checker: {e}",
                    "status": "error",
                }

        return responses

    async def _consult_specialists_async(
        self,
        routing_decision: dict[str, Any],
        _request: str,
        _patient_id: str | None,
        _patient_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """
        Consult specialist agents in parallel using asyncio.

        Wraps synchronous agent.run() calls in asyncio.to_thread() for
        concurrent execution.

        Args:
            routing_decision: Output from _analyze_routing
            _request: Patient request text
            _patient_id: Patient identifier
            _patient_context: Patient medical context

        Returns:
            Dict with responses from each consulted agent
        """
        responses = {}
        agents_needed = routing_decision.get("agents_needed", [])
        tasks = []

        # Create async tasks for each specialist
        if "MedicationAdvisor" in agents_needed and self.medication_advisor:
            tasks.append(
                self._consult_medication_advisor_async(_request, _patient_id, _patient_context)
            )

        if "SymptomMonitor" in agents_needed and self.symptom_monitor:
            tasks.append(
                self._consult_symptom_monitor_async(_request, _patient_id, _patient_context)
            )

        if "DrugInteractionChecker" in agents_needed and self.drug_interaction_checker:
            tasks.append(
                self._consult_drug_interaction_async(_request, _patient_id, _patient_context)
            )

        # Execute all tasks in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for result in results:
                if isinstance(result, Exception):
                    # Handle exceptions
                    continue
                if isinstance(result, dict) and "agent" in result:
                    agent_name = result["agent"]
                    responses[agent_name] = result

        return responses

    async def _consult_medication_advisor_async(
        self,
        request: str,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Async wrapper for MedicationAdvisor consultation."""
        assert self.medication_advisor is not None, "MedicationAdvisor not initialized"

        try:
            # Extract parameters
            params = await asyncio.to_thread(
                self.parameter_extractor.extract_for_medication_advisor, request
            )

            # Call agent (wrapped in to_thread since it's synchronous)
            med_response = await asyncio.to_thread(
                self.medication_advisor.analyze_missed_dose,
                medication=params.get("medication", "unknown"),
                scheduled_time=params.get("scheduled_time", "unknown"),
                current_time=params.get("current_time", "unknown"),
                patient_id=patient_id,
                patient_context=patient_context,
            )

            return {
                "agent": "MedicationAdvisor",
                "response": med_response,
                "status": "success",
                "extraction_confidence": params.get("confidence", 0.0),
            }
        except Exception as e:
            return {
                "agent": "MedicationAdvisor",
                "response": f"Error: {e}",
                "status": "error",
            }

    async def _consult_symptom_monitor_async(
        self,
        request: str,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Async wrapper for SymptomMonitor consultation."""
        assert self.symptom_monitor is not None, "SymptomMonitor not initialized"

        try:
            # Extract parameters
            params = await asyncio.to_thread(
                self.parameter_extractor.extract_for_symptom_monitor, request
            )

            # Call agent (wrapped in to_thread since it's synchronous)
            symptom_response = await asyncio.to_thread(
                self.symptom_monitor.analyze_symptoms,
                symptoms=params.get("symptoms", []),
                patient_id=patient_id,
                patient_context=patient_context,
                vital_signs=params.get("vital_signs"),
            )

            return {
                "agent": "SymptomMonitor",
                "response": symptom_response,
                "status": "success",
                "extraction_confidence": params.get("confidence", 0.0),
            }
        except Exception as e:
            return {
                "agent": "SymptomMonitor",
                "response": f"Error: {e}",
                "status": "error",
            }

    async def _consult_drug_interaction_async(
        self,
        request: str,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Async wrapper for DrugInteractionChecker consultation."""
        assert self.drug_interaction_checker is not None, "DrugInteractionChecker not initialized"

        try:
            # Extract parameters
            params = await asyncio.to_thread(
                self.parameter_extractor.extract_for_drug_interaction, request
            )

            # Call agent (wrapped in to_thread since it's synchronous)
            interaction_response = await asyncio.to_thread(
                self.drug_interaction_checker.check_interaction,
                medications=params.get("medications", []),
                patient_id=patient_id,
                patient_context=patient_context,
            )

            return {
                "agent": "DrugInteractionChecker",
                "response": interaction_response,
                "status": "success",
                "extraction_confidence": params.get("confidence", 0.0),
            }
        except Exception as e:
            return {
                "agent": "DrugInteractionChecker",
                "response": f"Error: {e}",
                "status": "error",
            }

    def _synthesize_response(
        self,
        request: str,
        routing_decision: dict[str, Any],
        specialist_responses: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synthesize specialist responses into comprehensive guidance.

        Uses coordinator LLM to aggregate specialist recommendations into
        coherent, actionable medical advice.

        Args:
            request: Original patient request
            routing_decision: Routing analysis
            specialist_responses: Responses from specialist agents

        Returns:
            Synthesized response with comprehensive recommendations
        """
        # Build detailed synthesis prompt
        prompt_parts = [
            "You are a transplant care coordinator synthesizing specialist recommendations.",
            f'\nPatient Request: "{request}"',
            f"\nRouting Analysis: {routing_decision.get('reasoning', 'N/A')}",
            f"\nRequest Type: {routing_decision.get('request_type', 'N/A')}",
            "\n--- SPECIALIST RECOMMENDATIONS ---",
        ]

        # Add each specialist response with details
        for agent_name, response_data in specialist_responses.items():
            status = response_data.get("status", "unknown")
            prompt_parts.append(f"\n{agent_name} ({status}):")

            if status == "success":
                # Extract structured response
                agent_response = response_data.get("response", {})
                if isinstance(agent_response, dict):
                    # Format structured response nicely
                    for key, value in agent_response.items():
                        if key not in ["raw_response", "agent_name"]:
                            prompt_parts.append(f"  {key}: {value}")
                else:
                    prompt_parts.append(f"  {agent_response}")

                # Add extraction confidence
                extraction_conf = response_data.get("extraction_confidence", 0.0)
                prompt_parts.append(f"  Parameter extraction confidence: {extraction_conf:.2f}")
            else:
                # Handle error cases
                prompt_parts.append(f"  Error: {response_data.get('response', 'Unknown error')}")

        # Add synthesis instructions
        prompt_parts.append("\n--- SYNTHESIS INSTRUCTIONS ---")
        prompt_parts.append("Synthesize a comprehensive, patient-friendly response that:")
        prompt_parts.append("1. Integrates all specialist recommendations coherently")
        prompt_parts.append("2. Prioritizes patient safety above all else")
        prompt_parts.append("3. Provides clear, actionable next steps")
        prompt_parts.append("4. Explains medical reasoning in accessible language")
        prompt_parts.append("5. Highlights any urgent actions or red flags")
        prompt_parts.append("6. Maintains empathetic, supportive tone")
        prompt_parts.append("\nProvide a concise synthesis (2-4 paragraphs):")

        synthesis_prompt = "\n".join(prompt_parts)

        try:
            # Use run_async() which works with both ADK 1.16.0 and 1.17.0
            # run_async() returns an async generator, so we need to collect events
            async def _run_agent():
                synthesis_text = ""
                async for event in self.agent.run_async(synthesis_prompt):  # type: ignore[attr-defined]
                    # Collect text from events
                    if hasattr(event, "content") and event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                synthesis_text += part.text
                return synthesis_text

            synthesis_text = asyncio.run(_run_agent())
        except Exception:
            # Fallback synthesis on error
            synthesis_text = self._fallback_synthesis(
                request, routing_decision, specialist_responses
            )

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            routing_decision, specialist_responses
        )

        return {
            "agents_consulted": list(specialist_responses.keys()),
            "recommendations": synthesis_text,
            "specialist_responses": specialist_responses,
            "coordinator_analysis": routing_decision.get("reasoning", "N/A"),
            "request_type": routing_decision.get("request_type", "general_inquiry"),
            "confidence": overall_confidence,
            "agent_name": self.agent.name,
            "raw_response": synthesis_text,
        }

    def _fallback_synthesis(
        self,
        request: str,
        routing_decision: dict[str, Any],  # noqa: ARG002
        specialist_responses: dict[str, Any],
    ) -> str:
        """Fallback synthesis when LLM synthesis fails."""

        parts = [f"Based on your request: '{request}'"]

        for agent_name, response_data in specialist_responses.items():
            status = response_data.get("status", "unknown")
            if status == "success":
                agent_response = response_data.get("response", {})
                if isinstance(agent_response, dict):
                    recommendation = agent_response.get(
                        "recommendation", agent_response.get("raw_response", "Analysis complete")
                    )
                    parts.append(f"\n{agent_name}: {recommendation}")

        parts.append("\nPlease contact your transplant coordinator for personalized guidance.")

        return " ".join(parts)

    def _calculate_overall_confidence(
        self,
        routing_decision: dict[str, Any],
        specialist_responses: dict[str, Any],
    ) -> float:
        """Calculate overall confidence score."""

        # Start with base confidence
        confidence = 0.5

        # Check if routing was successful
        if routing_decision.get("agents_needed"):
            confidence += 0.1

        # Check specialist response quality
        successful_responses = 0
        total_responses = len(specialist_responses)

        for response_data in specialist_responses.values():
            if response_data.get("status") == "success":
                successful_responses += 1
                # Add extraction confidence if available
                extraction_conf = response_data.get("extraction_confidence", 0.0)
                confidence += extraction_conf * 0.1

        # Increase confidence based on success rate
        if total_responses > 0:
            success_rate = successful_responses / total_responses
            confidence += success_rate * 0.2

        return min(confidence, 1.0)

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
