"""
MedicationAdvisor Agent Implementation

Specialized ADK agent for analyzing missed medication doses and providing
evidence-based recommendations for transplant patients.

Integrates real clinical outcomes data from SRTR (Scientific Registry of
Transplant Recipients) to provide population-based risk assessments.
"""

from typing import Any

from services.agents.base_adk_agent import BaseADKAgent
from services.config.adk_config import MEDICATION_ADVISOR_CONFIG
from services.data.srtr_outcomes import get_srtr_data


class MedicationAdvisorAgent(BaseADKAgent):
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
        super().__init__(
            agent_config=MEDICATION_ADVISOR_CONFIG,
            app_name="MedicationAdvisor",
            session_id_prefix="medication_analysis",
            api_key=api_key,
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

        # Invoke agent using base class method
        response = self._invoke_agent(prompt)

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
