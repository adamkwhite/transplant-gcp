"""
Mock Agent Implementations for Pub/Sub Testing

These mock agents bypass the ADK API issues and return realistic test responses
to allow testing of the Pub/Sub communication infrastructure.
"""

from typing import Any


class MockMedicationAdvisorAgent:
    """Mock medication advisor for testing Pub/Sub infrastructure."""

    def analyze_missed_dose(
        self,
        medication: str,
        scheduled_time: str,
        current_time: str,  # noqa: ARG002
        patient_id: str | None = None,  # noqa: ARG002
        patient_context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Return mock medication advice response."""
        return {
            "recommendation": f"For {medication} missed at {scheduled_time}, take now if within 4 hours",
            "reasoning_steps": [
                "Analyzed medication half-life",
                "Considered time elapsed",
                "Assessed rejection risk",
            ],
            "risk_level": "moderate",
            "confidence": 0.85,
            "next_steps": ["Take dose now", "Monitor for side effects", "Contact team if unsure"],
            "agent_name": "Mock MedicationAdvisor",
        }


class MockSymptomMonitorAgent:
    """Mock symptom monitor for testing Pub/Sub infrastructure."""

    def analyze_symptoms(
        self,
        symptoms: list[str],
        patient_id: str | None = None,  # noqa: ARG002
        patient_context: dict[str, Any] | None = None,  # noqa: ARG002
        vital_signs: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Return mock symptom analysis response."""
        return {
            "rejection_risk": "moderate" if "fever" in symptoms else "low",
            "urgency": "same_day" if "fever" in symptoms else "routine",
            "reasoning": f"Patient reports {len(symptoms)} symptoms",
            "actions": [
                "Monitor temperature",
                "Track fluid intake",
                "Contact team if worsens",
            ],
            "differential": ["Infection", "Rejection", "Medication side effect"],
            "confidence": 0.80,
            "agent_name": "Mock SymptomMonitor",
        }


class MockDrugInteractionCheckerAgent:
    """Mock drug interaction checker for testing Pub/Sub infrastructure."""

    def check_interaction(
        self,
        medications: list[str],
        foods: list[str] | None = None,
        supplements: list[str] | None = None,  # noqa: ARG002
        patient_id: str | None = None,  # noqa: ARG002
        patient_context: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Return mock interaction check response."""
        has_interaction = "ibuprofen" in medications or (foods and "grapefruit" in str(foods))

        return {
            "has_interaction": has_interaction,
            "severity": "severe" if has_interaction else "none",
            "interactions": [
                {"drug1": medications[0], "drug2": "ibuprofen", "effect": "Increased toxicity"}
            ]
            if has_interaction
            else [],
            "mechanism": "CYP3A4 inhibition" if has_interaction else "No interactions",
            "clinical_effect": "Risk of nephrotoxicity" if has_interaction else "None",
            "recommendation": "Avoid combination - use acetaminophen instead"
            if has_interaction
            else "No interactions detected",
            "confidence": 0.90,
            "agent_name": "Mock DrugInteractionChecker",
        }
