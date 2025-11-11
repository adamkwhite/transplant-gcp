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
        current_time: str,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return mock medication advice response."""
        patient_info = f" for patient {patient_id}" if patient_id else ""
        transplant_type = (
            patient_context.get("transplant_type", "kidney") if patient_context else "kidney"
        )

        return {
            "recommendation": f"For {medication} scheduled at {scheduled_time}, now {current_time}{patient_info}, take now if within 4 hours",
            "reasoning_steps": [
                f"Analyzed {medication} half-life for {transplant_type} transplant",
                f"Time elapsed from {scheduled_time} to {current_time}",
                "Assessed rejection risk based on patient context",
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
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
        vital_signs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return mock symptom analysis response."""
        patient_info = f" (patient {patient_id})" if patient_id else ""
        transplant_type = (
            patient_context.get("transplant_type", "kidney") if patient_context else "kidney"
        )
        temp = vital_signs.get("temperature") if vital_signs else None
        temp_note = f" with temperature {temp}°F" if temp else ""

        return {
            "rejection_risk": "moderate" if "fever" in symptoms else "low",
            "urgency": "same_day" if "fever" in symptoms else "routine",
            "reasoning": f"Patient{patient_info} reports {len(symptoms)} symptoms{temp_note} post-{transplant_type} transplant",
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
        supplements: list[str] | None = None,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return mock interaction check response."""
        has_interaction = "ibuprofen" in medications or (foods and "grapefruit" in str(foods))
        has_supplement_interaction = supplements and any(
            supp in ["st john's wort", "ginkgo"] for supp in supplements
        )
        patient_info = f" for patient {patient_id}" if patient_id else ""
        transplant_type = (
            patient_context.get("transplant_type", "kidney") if patient_context else "kidney"
        )

        return {
            "has_interaction": has_interaction or has_supplement_interaction,
            "severity": "severe" if (has_interaction or has_supplement_interaction) else "none",
            "interactions": [
                {"drug1": medications[0], "drug2": "ibuprofen", "effect": "Increased toxicity"}
            ]
            if has_interaction
            else [],
            "mechanism": "CYP3A4 inhibition"
            if (has_interaction or has_supplement_interaction)
            else "No interactions",
            "clinical_effect": f"Risk of nephrotoxicity in {transplant_type} transplant{patient_info}"
            if has_interaction
            else "None",
            "recommendation": "Avoid combination - use acetaminophen instead"
            if has_interaction
            else "No interactions detected",
            "confidence": 0.90,
            "agent_name": "Mock DrugInteractionChecker",
        }
