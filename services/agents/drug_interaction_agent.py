"""
DrugInteractionChecker Agent Implementation

Specialized ADK agent for validating medication safety and identifying
drug-drug, drug-food, and drug-supplement interactions for transplant patients.
"""

from typing import Any

from services.agents.base_adk_agent import BaseADKAgent
from services.agents.response_parser import extract_json_from_response
from services.config.adk_config import DRUG_INTERACTION_CONFIG


class DrugInteractionCheckerAgent(BaseADKAgent):
    """
    ADK Agent for medication interaction checking and safety validation.

    This agent specializes in:
    - Checking drug-drug, drug-food, and drug-supplement interactions
    - Assessing interaction severity (none/mild/moderate/severe/contraindicated)
    - Explaining mechanisms (CYP3A4 inhibition, absorption interference)
    - Providing specific safety recommendations
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the DrugInteractionChecker agent.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
        """
        super().__init__(
            agent_config=DRUG_INTERACTION_CONFIG,
            app_name="DrugInteractionChecker",
            session_id_prefix="interaction_check",
            api_key=api_key,
        )

    def check_interaction(
        self,
        medications: list[str],
        foods: list[str] | None = None,
        supplements: list[str] | None = None,
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Check for medication, food, and supplement interactions.

        Args:
            medications: List of medication names (e.g., ["tacrolimus", "prednisone"])
            foods: Optional list of foods/beverages (e.g., ["grapefruit juice"])
            supplements: Optional list of supplements (e.g., ["St. John's Wort"])
            patient_id: Optional patient identifier for context
            patient_context: Optional dict with kidney function, liver function, other conditions

        Returns:
            Dict with:
                - has_interaction: Boolean indicating if interactions found
                - severity: Highest severity level (none/mild/moderate/severe/contraindicated)
                - interactions: List of specific interaction details
                - mechanism: Explanation of interaction mechanism
                - clinical_effect: Expected clinical impact
                - recommendation: Specific safety guidance
                - confidence: Confidence score (0.0-1.0)
        """
        # Build prompt with interaction context
        prompt = self._build_interaction_check_prompt(
            medications=medications,
            foods=foods,
            supplements=supplements,
            patient_id=patient_id,
            patient_context=patient_context,
        )

        # Invoke agent using base class method
        response = self._invoke_agent(prompt)

        # Parse agent response
        return self._parse_agent_response(response)

    def _build_interaction_check_prompt(
        self,
        medications: list[str],
        foods: list[str] | None,
        supplements: list[str] | None,
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> str:
        """Build structured prompt for interaction checking."""
        prompt_parts = [
            "Check for interactions between these substances:",
            f"- Medications: {', '.join(medications)}",
        ]

        if foods:
            prompt_parts.append(f"- Foods/Beverages: {', '.join(foods)}")

        if supplements:
            prompt_parts.append(f"- Supplements: {', '.join(supplements)}")

        if patient_id:
            prompt_parts.append(f"- Patient ID: {patient_id}")

        if patient_context:
            prompt_parts.append(f"- Patient context: {patient_context}")

        prompt_parts.append(
            "\nProvide a JSON response with: has_interaction (boolean), severity, "
            "interactions (list), mechanism, clinical_effect, recommendation, confidence (0.0-1.0)."
        )

        return "\n".join(prompt_parts)

    def _parse_agent_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK agent response into structured format.

        Args:
            response: Raw agent response from ADK

        Returns:
            Structured dict with interaction data
        """
        response_text = str(response)

        # Try to extract and parse JSON from the response
        parsed_json = extract_json_from_response(response_text)

        if parsed_json:
            # Use parsed values from AI
            return {
                "has_interaction": parsed_json.get("has_interaction", False),
                "severity": parsed_json.get("severity", "none"),
                "interactions": parsed_json.get("interactions", []),
                "mechanism": parsed_json.get("mechanism", ""),
                "clinical_effect": parsed_json.get(
                    "clinical_effect", "No significant interactions detected"
                ),
                "recommendation": parsed_json.get(
                    "recommendation", "Continue current regimen as prescribed"
                ),
                "confidence": parsed_json.get("confidence", 0.90),
                "agent_name": self.agent.name,
                "raw_response": response_text,
            }
        else:
            # Fallback if JSON parsing fails
            return {
                "has_interaction": False,
                "severity": "unknown",
                "interactions": [],
                "mechanism": response_text,
                "clinical_effect": "Unable to parse AI response",
                "recommendation": "Please review full analysis and consult pharmacist",
                "confidence": 0.50,
                "agent_name": self.agent.name,
                "raw_response": response_text,
            }

    def get_known_interactions_reference(self) -> dict[str, Any]:
        """
        Get reference information about common transplant medication interactions.

        Returns:
            Dict with known interactions categorized by severity
        """
        return {
            "contraindicated": {
                "tacrolimus_cyclosporine": {
                    "combination": ["Tacrolimus", "Cyclosporine"],
                    "mechanism": "Both are calcineurin inhibitors",
                    "effect": "Severe nephrotoxicity, contraindicated",
                    "action": "Never use together",
                },
                "tacrolimus_st_johns_wort": {
                    "combination": ["Tacrolimus", "St. John's Wort"],
                    "mechanism": "Strong CYP3A4 induction",
                    "effect": "Therapeutic failure, rejection risk",
                    "action": "Avoid St. John's Wort",
                },
            },
            "severe": {
                "tacrolimus_grapefruit": {
                    "combination": ["Tacrolimus", "Grapefruit"],
                    "mechanism": "CYP3A4 inhibition",
                    "effect": "2-3x increase in levels, toxicity risk",
                    "action": "Avoid grapefruit and grapefruit juice",
                },
                "tacrolimus_ketoconazole": {
                    "combination": ["Tacrolimus", "Ketoconazole"],
                    "mechanism": "Strong CYP3A4 inhibition",
                    "effect": "Significantly increased tacrolimus levels",
                    "action": "Dose reduction required, close monitoring",
                },
            },
            "moderate": {
                "tacrolimus_nsaids": {
                    "combination": ["Tacrolimus", "NSAIDs (ibuprofen, naproxen)"],
                    "mechanism": "Additive nephrotoxicity",
                    "effect": "Increased kidney damage risk",
                    "action": "Use acetaminophen instead",
                },
                "mycophenolate_antacids": {
                    "combination": ["Mycophenolate", "Antacids (calcium, magnesium)"],
                    "mechanism": "Decreased absorption",
                    "effect": "Reduced immunosuppression effectiveness",
                    "action": "Separate by 2 hours",
                },
            },
            "mild": {
                "prednisone_caffeine": {
                    "combination": ["Prednisone", "Caffeine"],
                    "mechanism": "Additive CNS stimulation",
                    "effect": "Increased anxiety, insomnia",
                    "action": "Limit caffeine intake",
                },
            },
            "cyp3a4_interactions": {
                "strong_inhibitors": [
                    "Ketoconazole",
                    "Itraconazole",
                    "Clarithromycin",
                    "Erythromycin",
                    "Grapefruit juice",
                ],
                "strong_inducers": [
                    "Rifampin",
                    "Phenytoin",
                    "Carbamazepine",
                    "St. John's Wort",
                ],
                "effect_on_tacrolimus": "Inhibitors increase levels, inducers decrease levels",
            },
        }
