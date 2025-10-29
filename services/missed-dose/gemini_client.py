"""
Google Gemini AI Client for Transplant Medication Adherence
Real AI inference for the Google Cloud Run Hackathon
"""

import json
import os
from typing import Any

import google.generativeai as genai


class GeminiClient:
    """Client for Google Gemini AI API"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use Gemini 2.0 Flash - fast and powerful model for medical reasoning
            self.model = genai.GenerativeModel("gemini-2.0-flash")
            self.flash_model = genai.GenerativeModel(
                "gemini-2.0-flash-lite"
            )  # Even faster for simple queries
        else:
            self.model = None
            self.flash_model = None

    def analyze_missed_dose(
        self, medication: str, hours_late: float, patient_context: dict
    ) -> dict[str, Any]:
        """
        Analyze missed medication dose using Gemini AI
        Returns structured medical guidance
        """
        if not self.model:
            return self._mock_response(medication, hours_late)

        prompt = f"""You are a medical AI assistant specializing in organ transplant medication management.

Patient Context:
- Medication: {medication}
- Hours late: {hours_late} hours
- Transplant type: {patient_context.get("transplant_type", "kidney")}
- Months post-transplant: {patient_context.get("months_post_transplant", 6)}
- Current adherence rate: {patient_context.get("adherence_rate", 0.85) * 100:.0f}%
- Doses missed this week: {patient_context.get("missed_this_week", 0)}

Medical Knowledge:
- Tacrolimus has a 12-hour therapeutic window
- Missing doses increases rejection risk
- Consistency is critical for immunosuppression

Question: Should the patient take the missed dose of {medication} now?

Provide a response in JSON format with these fields:
1. recommendation: Clear action (e.g., "Take dose now", "Skip dose", "Take half dose")
2. reasoning_steps: Array of 5 medical reasoning steps
3. risk_level: "low", "medium", "high", or "critical"
4. confidence: Number between 0 and 1
5. next_steps: Array of 3 specific actions for the patient

Format as valid JSON only."""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,  # Lower for medical accuracy
                    max_output_tokens=800,
                ),
            )

            # Parse JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)
            result["ai_model"] = "gemini-2.0-flash"
            return result

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self._mock_response(medication, hours_late)

    def analyze_symptoms(self, symptoms: list[str], patient_context: dict) -> dict[str, Any]:
        """
        Analyze symptoms for rejection risk using Gemini
        """
        if not self.model:
            return self._mock_symptom_analysis(symptoms)

        prompt = f"""You are a medical AI analyzing transplant rejection symptoms.

Patient reports: {", ".join(symptoms)}
Transplant type: {patient_context.get("transplant_type", "kidney")}
Current medications: {", ".join(patient_context.get("medications", ["tacrolimus", "mycophenolate"]))}

Critical rejection symptoms for kidney transplant:
- Fever > 100°F
- Decreased urine output
- Rapid weight gain (>2 lbs/day)
- Elevated creatinine
- Tenderness over transplant site

Analyze the symptoms and provide JSON response with:
1. rejection_risk: "low", "medium", "high", or "critical"
2. urgency: "routine", "same_day", "urgent", or "emergency"
3. reasoning: Array of medical reasoning steps
4. actions: Specific actions to take
5. differential: Other possible causes

Format as valid JSON only."""

        try:
            response = self.flash_model.generate_content(  # Use Flash for faster response
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=600,
                ),
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)
            result["ai_model"] = "gemini-2.0-flash"
            return result

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self._mock_symptom_analysis(symptoms)

    def check_drug_interactions(self, medications: list[str], new_item: str) -> dict[str, Any]:
        """
        Check for drug interactions using Gemini's medical knowledge
        """
        if not self.model:
            return self._mock_interaction_check(medications, new_item)

        prompt = f"""You are a clinical pharmacist AI checking drug interactions for transplant patients.

Current medications: {", ".join(medications)}
New item to check: {new_item}

Important interactions for transplant medications:
- Tacrolimus + Grapefruit = 2-3x increase in levels (CYP3A4 inhibition)
- Tacrolimus + NSAIDs = Increased nephrotoxicity
- Mycophenolate + Antacids = Decreased absorption

Check for interactions and provide JSON response with:
1. has_interaction: true or false
2. severity: "none", "mild", "moderate", "severe", or "contraindicated"
3. mechanism: How the interaction occurs
4. clinical_effect: What happens to the patient
5. recommendation: What the patient should do

Format as valid JSON only."""

        try:
            response = self.flash_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Very low for drug safety
                    max_output_tokens=500,
                ),
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            result = json.loads(response_text)
            result["ai_model"] = "gemini-2.0-flash"
            return result

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self._mock_interaction_check(medications, new_item)

    def _mock_response(self, medication: str, hours_late: float) -> dict[str, Any]:
        """Fallback mock response when API unavailable"""
        if hours_late <= 6:
            return {
                "recommendation": "Take dose now",
                "reasoning_steps": [
                    f"{medication} has a 12-hour therapeutic window",
                    f"Patient is {hours_late:.1f} hours late - within safe window",
                    "Taking now maintains therapeutic blood levels",
                    "Risk of rejection outweighs timing irregularity",
                    "Set alarm for next dose to maintain schedule",
                ],
                "risk_level": "medium" if hours_late > 4 else "low",
                "confidence": 0.85,
                "next_steps": [
                    "Take the medication immediately",
                    "Set alarm for next scheduled dose",
                    "Log this incident in medication diary",
                ],
                "ai_model": "mock_response",
            }
        else:
            return {
                "recommendation": "Skip dose",
                "reasoning_steps": [
                    f"More than 6 hours late for {medication}",
                    "Taking now would be too close to next dose",
                    "Could cause medication level spike",
                    "Better to maintain regular schedule",
                    "Contact transplant team if concerned",
                ],
                "risk_level": "high",
                "confidence": 0.80,
                "next_steps": [
                    "Skip this dose",
                    "Take next dose at regular time",
                    "Contact transplant coordinator",
                ],
                "ai_model": "mock_response",
            }

    def _mock_symptom_analysis(self, symptoms: list[str]) -> dict[str, Any]:
        """Mock symptom analysis response"""
        high_risk = any(
            s in str(symptoms).lower() for s in ["fever", "decreased urine", "weight gain"]
        )

        return {
            "rejection_risk": "high" if high_risk else "low",
            "urgency": "emergency" if high_risk else "routine",
            "reasoning": [
                "Symptoms analyzed for rejection indicators",
                "Checked against known rejection patterns",
                "Risk stratified based on symptom severity",
            ],
            "actions": [
                "Contact transplant team immediately" if high_risk else "Monitor symptoms",
                "Check temperature and weight",
                "Document symptoms for next appointment",
            ],
            "differential": ["Infection", "Medication side effects", "Dehydration"],
            "ai_model": "mock_response",
        }

    def _mock_interaction_check(self, medications: list[str], new_item: str) -> dict[str, Any]:
        """Mock drug interaction check"""
        if "tacrolimus" in [m.lower() for m in medications] and "grapefruit" in new_item.lower():
            return {
                "has_interaction": True,
                "severity": "severe",
                "mechanism": "Grapefruit inhibits CYP3A4 enzyme",
                "clinical_effect": "Tacrolimus levels increase 2-3x, risk of toxicity",
                "recommendation": "Avoid grapefruit and grapefruit juice completely",
                "ai_model": "mock_response",
            }

        return {
            "has_interaction": False,
            "severity": "none",
            "mechanism": "No known interaction",
            "clinical_effect": "Safe to use together",
            "recommendation": "No special precautions needed",
            "ai_model": "mock_response",
        }


# Factory function
def get_gemini_client():
    """Get Gemini client with proper configuration"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY not set, using mock responses")
    return GeminiClient(api_key=api_key)
