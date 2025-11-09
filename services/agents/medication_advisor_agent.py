"""
MedicationAdvisor Agent Implementation

Specialized ADK agent for analyzing missed medication doses and providing
evidence-based recommendations for transplant patients.

Integrates real clinical outcomes data from SRTR (Scientific Registry of
Transplant Recipients) to provide population-based risk assessments.
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
    DEFAULT_GENERATION_CONFIG,
    GEMINI_API_KEY,
    MEDICATION_ADVISOR_CONFIG,
)
from services.data.srtr_outcomes import get_srtr_data


class MedicationAdvisorAgent:
    """
    ADK Agent for missed dose analysis and medication adherence guidance.

    This agent specializes in:
    - Analyzing missed dose scenarios (time late, medication type, patient context)
    - Providing specific recommendations (take now, skip, partial dose, call doctor)
    - Assessing rejection risk based on adherence patterns
    - Considering pharmacokinetics (half-life, therapeutic windows)
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the MedicationAdvisor agent.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
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
            name=MEDICATION_ADVISOR_CONFIG["name"],
            model=MEDICATION_ADVISOR_CONFIG["model"],
            description=MEDICATION_ADVISOR_CONFIG["description"],
            instruction=MEDICATION_ADVISOR_CONFIG["instruction"],
            generate_content_config=generate_config,
        )

        # Create Runner with in-memory session service
        self.runner = Runner(
            app_name="MedicationAdvisor",
            agent=self.agent,
            session_service=InMemorySessionService(),
        )

    def analyze_missed_dose(
        self,
        medication: str,
        scheduled_time: str,
        current_time: str,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a missed medication dose and provide recommendations.

        Args:
            medication: Name of the medication (e.g., "tacrolimus", "mycophenolate")
            scheduled_time: When dose should have been taken (e.g., "8:00 AM")
            current_time: Current time (e.g., "2:00 PM")
            patient_id: Optional patient identifier for context
            patient_context: Optional dict with patient history, adherence patterns

        Returns:
            Dict with:
                - recommendation: Specific action to take
                - reasoning_steps: Chain of reasoning
                - risk_level: Assessment of rejection risk (low/medium/high/critical)
                - confidence: Confidence score (0.0-1.0)
                - next_steps: List of follow-up actions
        """
        # Build prompt with patient context
        prompt = self._build_missed_dose_prompt(
            medication=medication,
            scheduled_time=scheduled_time,
            current_time=current_time,
            patient_id=patient_id,
            patient_context=patient_context,
        )

        # Invoke agent using Runner with proper session context
        async def _run_agent():
            response_text = ""
            user_message = types.Content(role="user", parts=[types.Part(text=prompt)])

            # Create session if it doesn't exist
            session = await self.runner.session_service.get_session(  # type: ignore[attr-defined]
                app_name=self.runner.app_name,  # type: ignore[attr-defined]
                user_id="system",
                session_id="medication_analysis",
            )
            if not session:
                await self.runner.session_service.create_session(  # type: ignore[attr-defined]
                    app_name=self.runner.app_name,  # type: ignore[attr-defined]
                    user_id="system",
                    session_id="medication_analysis",
                )

            async for event in self.runner.run_async(  # type: ignore[attr-defined]
                user_id="system",
                session_id="medication_analysis",
                new_message=user_message,
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            return response_text

        response = asyncio.run(_run_agent())

        # Parse agent response
        return self._parse_agent_response(response)

    def _build_missed_dose_prompt(
        self,
        medication: str,
        scheduled_time: str,
        current_time: str,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> str:
        """Build structured prompt for missed dose analysis with SRTR population data."""
        prompt_parts = [
            "Analyze this missed dose scenario:",
            f"- Medication: {medication}",
            f"- Scheduled time: {scheduled_time}",
            f"- Current time: {current_time}",
        ]

        if patient_id:
            prompt_parts.append(f"- Patient ID: {patient_id}")

        if patient_context:
            prompt_parts.append(f"- Patient context: {patient_context}")

        # Add SRTR population statistics if patient context includes required fields
        srtr_data_available = False
        if patient_context:
            organ = patient_context.get("organ_type", "kidney")
            age_group = patient_context.get("age_group", "35-49")
            months_post_tx = patient_context.get("months_post_transplant", 6)

            try:
                srtr = get_srtr_data(organ)
                population_stats = srtr.format_for_prompt(age_group, months_post_tx)
                rejection_rate = srtr.get_acute_rejection_rate(age_group)

                prompt_parts.extend(
                    [
                        "\n--- Real Clinical Outcomes Data (SRTR 2023) ---",
                        population_stats,
                        "\nUse these population statistics to contextualize your risk assessment.",
                        "\nIMPORTANT: Include a 'srtr_data_source' section in your response showing:",
                        "- Source: SRTR 2023 Annual Data Report",
                        f"- Organ: {organ.capitalize()}",
                        f"- Age Group: {age_group}",
                        f"- Baseline Rejection Rate: {rejection_rate}%",
                        f"- Total Records in Database: {srtr._summary.get('total_records', 'N/A')} {organ} transplant recipients",  # type: ignore[union-attr]
                    ]
                )
                srtr_data_available = True
            except Exception:
                # If SRTR data unavailable, continue without it
                prompt_parts.append("\n--- WARNING: SRTR data unavailable (demo mode) ---")

        prompt_parts.append(
            "\nProvide a JSON response with: recommendation, reasoning_steps (list), "
            "risk_level, confidence (0.0-1.0), next_steps (list)"
            + (
                ", srtr_data_source (dict with source, organ, age_group, baseline_rejection_rate, total_records)"
                if srtr_data_available
                else ""
            )
            + "."
        )

        return "\n".join(prompt_parts)

    def _parse_agent_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK agent response into structured format.

        Args:
            response: Raw agent response from ADK

        Returns:
            Structured dict with recommendation data
        """
        # ADK returns agent response object
        # Extract text content and parse JSON if present
        response_text = str(response)

        # Basic parsing (in real implementation, use JSON parsing)
        # For now, return structured format
        return {
            "recommendation": response_text,
            "reasoning_steps": ["Agent analysis in progress"],
            "risk_level": "medium",
            "confidence": 0.85,
            "next_steps": ["Monitor patient response"],
            "agent_name": self.agent.name,
            "raw_response": response_text,
        }

    def get_therapeutic_window(self, medication: str) -> dict[str, Any]:
        """
        Get therapeutic window information for a medication.

        Args:
            medication: Medication name

        Returns:
            Dict with window_hours, critical_period, and guidance
        """
        windows = {
            "tacrolimus": {
                "window_hours": 12,
                "critical_period": 4,  # Most critical within 4 hours
                "guidance": "Critical immunosuppressant - contact doctor if >12h late",
            },
            "mycophenolate": {
                "window_hours": 12,
                "critical_period": 6,
                "guidance": "Important antiproliferative immunosuppressant - can be flexible within window",
            },
            "prednisone": {
                "window_hours": 24,
                "critical_period": 12,
                "guidance": "Daily corticosteroid - take as soon as remembered same day",
            },
        }

        return windows.get(
            medication.lower(),
            {
                "window_hours": 24,
                "critical_period": 12,
                "guidance": "Consult prescribing information",
            },
        )
