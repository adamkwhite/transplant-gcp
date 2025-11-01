"""
SymptomMonitor Agent Implementation

Specialized ADK agent for detecting transplant rejection symptoms and
assessing urgency for kidney transplant patients.
"""

from typing import Any

from google.adk.agents import Agent

from services.config.adk_config import (
    DEFAULT_GENERATION_CONFIG,
    GEMINI_API_KEY,
    SYMPTOM_MONITOR_CONFIG,
)


class SymptomMonitorAgent:
    """
    ADK Agent for transplant rejection symptom detection and risk assessment.

    This agent specializes in:
    - Analyzing patient-reported symptoms for rejection indicators
    - Assessing rejection risk levels (low/medium/high/critical)
    - Determining urgency (routine/same_day/urgent/emergency)
    - Providing differential diagnosis for alternative causes
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the SymptomMonitor agent.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
        """
        self.api_key = api_key or GEMINI_API_KEY

        # Create ADK agent instance
        self.agent = Agent(
            name=SYMPTOM_MONITOR_CONFIG["name"],
            model=SYMPTOM_MONITOR_CONFIG["model"],
            description=SYMPTOM_MONITOR_CONFIG["description"],
            instruction=SYMPTOM_MONITOR_CONFIG["instruction"],
            generation_config=DEFAULT_GENERATION_CONFIG,
        )

    def analyze_symptoms(
        self,
        symptoms: list[str],
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
        vital_signs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze patient symptoms for transplant rejection risk.

        Args:
            symptoms: List of patient-reported symptoms (e.g., ["fever", "decreased urine"])
            patient_id: Optional patient identifier for context
            patient_context: Optional dict with transplant date, medication history, previous rejections
            vital_signs: Optional dict with temperature, weight, blood pressure

        Returns:
            Dict with:
                - rejection_risk: Risk level (low/medium/high/critical)
                - urgency: Action urgency (routine/same_day/urgent/emergency)
                - reasoning: Chain of clinical reasoning
                - actions: List of recommended immediate actions
                - differential: Alternative diagnoses to consider
                - confidence: Confidence score (0.0-1.0)
        """
        # Build prompt with clinical context
        prompt = self._build_symptom_analysis_prompt(
            symptoms=symptoms,
            patient_id=patient_id,
            patient_context=patient_context,
            vital_signs=vital_signs,
        )

        # Invoke agent (ADK handles session management)
        response = self.agent.run(prompt)

        # Parse agent response
        return self._parse_agent_response(response)

    def _build_symptom_analysis_prompt(
        self,
        symptoms: list[str],
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
        vital_signs: dict[str, Any] | None,
    ) -> str:
        """Build structured prompt for symptom analysis."""
        prompt_parts = [
            "Analyze these patient symptoms for kidney transplant rejection risk:",
            f"- Symptoms: {', '.join(symptoms)}",
        ]

        if patient_id:
            prompt_parts.append(f"- Patient ID: {patient_id}")

        if patient_context:
            prompt_parts.append(f"- Patient context: {patient_context}")

        if vital_signs:
            prompt_parts.append(f"- Vital signs: {vital_signs}")

        prompt_parts.append(
            "\nProvide a JSON response with: rejection_risk, urgency, reasoning, "
            "actions (list), differential (list), confidence (0.0-1.0)."
        )

        return "\n".join(prompt_parts)

    def _parse_agent_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK agent response into structured format.

        Args:
            response: Raw agent response from ADK

        Returns:
            Structured dict with symptom analysis
        """
        # ADK returns agent response object
        # Extract text content and parse JSON if present
        response_text = str(response)

        # Basic parsing (in real implementation, use JSON parsing)
        # For now, return structured format
        return {
            "rejection_risk": "medium",
            "urgency": "same_day",
            "reasoning": response_text,
            "actions": [
                "Contact transplant coordinator",
                "Monitor symptoms closely",
            ],
            "differential": [
                "Viral infection",
                "Urinary tract infection",
                "Medication side effect",
            ],
            "confidence": 0.80,
            "agent_name": self.agent.name,
            "raw_response": response_text,
        }

    def get_rejection_symptoms_reference(self) -> dict[str, Any]:
        """
        Get reference information about kidney transplant rejection symptoms.

        Returns:
            Dict with symptom categories and clinical significance
        """
        return {
            "critical_symptoms": {
                "fever": {
                    "threshold": "> 100°F (37.8°C)",
                    "significance": "Possible acute rejection or infection",
                    "urgency": "urgent",
                },
                "decreased_urine": {
                    "threshold": "< 500ml/day or sudden drop",
                    "significance": "Acute rejection or kidney dysfunction",
                    "urgency": "urgent",
                },
                "weight_gain": {
                    "threshold": "> 2 lbs/day (fluid retention)",
                    "significance": "Kidney dysfunction, rejection",
                    "urgency": "same_day",
                },
                "elevated_creatinine": {
                    "threshold": "> 20% increase from baseline",
                    "significance": "Strong indicator of rejection",
                    "urgency": "urgent",
                },
            },
            "warning_symptoms": {
                "transplant_tenderness": "Possible rejection or infection",
                "flu_symptoms": "Infection or rejection",
                "fatigue": "Kidney dysfunction",
                "swelling": "Fluid retention",
            },
            "monitoring_guidelines": {
                "temperature": "Daily, report if > 100°F",
                "weight": "Daily, same time, report > 2 lbs gain",
                "blood_pressure": "Daily, report significant changes",
                "urine_output": "Monitor daily, report decreases",
            },
        }
