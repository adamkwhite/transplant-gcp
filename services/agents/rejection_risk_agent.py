"""
RejectionRisk Agent Implementation

Specialized ADK agent for analyzing transplant rejection symptoms and providing
evidence-based risk assessments using SRTR population data.

Integrates real clinical outcomes data from SRTR (Scientific Registry of
Transplant Recipients) to provide population-based rejection risk scores.
"""

from typing import Any

from services.agents.base_adk_agent import BaseADKAgent
from services.agents.response_parser import extract_json_from_response
from services.config.adk_config import REJECTION_RISK_CONFIG
from services.data.srtr_outcomes import get_srtr_data


class RejectionRiskAgent(BaseADKAgent):
    """
    ADK Agent for transplant rejection risk analysis.

    This agent specializes in:
    - Analyzing rejection symptoms (fever, weight gain, fatigue, urine output)
    - Calculating rejection probability using SRTR population baselines
    - Providing urgent clinical recommendations
    - Generating similar patient cases based on SRTR statistics
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the RejectionRisk agent.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
        """
        super().__init__(
            agent_config=REJECTION_RISK_CONFIG,
            app_name="RejectionRiskAnalyzer",
            session_id_prefix="rejection_analysis",
            api_key=api_key,
        )

    def analyze_rejection_risk(
        self,
        symptoms: dict[str, Any],
        patient_id: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze transplant rejection risk based on symptoms.

        Args:
            symptoms: Dict with fever (°F), weight_gain (lbs), fatigue, urine_output
            patient_id: Optional patient identifier for context
            patient_context: Optional dict with organ type, age group, months post-tx

        Returns:
            Dict with:
                - rejection_probability: Probability of rejection (0.0-1.0)
                - urgency: Urgency level (LOW/MEDIUM/HIGH/CRITICAL)
                - risk_level: Risk assessment (low/medium/high/critical)
                - recommended_action: Specific action to take
                - reasoning_steps: Chain of reasoning
                - similar_cases: List of similar patient cases
                - srtr_data_source: Data source attribution
        """
        # Build prompt with patient context and SRTR data
        prompt = self._build_rejection_prompt(
            symptoms=symptoms,
            patient_id=patient_id,
            patient_context=patient_context,
        )

        # Invoke agent using base class method
        response = self._invoke_agent(prompt)

        # Parse agent response
        return self._parse_agent_response(response)

    def _build_rejection_prompt(
        self,
        symptoms: dict[str, Any],
        patient_id: str | None,
        patient_context: dict[str, Any] | None,
    ) -> str:
        """Build structured prompt for rejection risk analysis with SRTR data."""
        prompt_parts = [
            "Analyze this transplant rejection risk scenario:",
            f"- Fever: {symptoms.get('fever', 'N/A')}°F",
            f"- Weight gain: {symptoms.get('weight_gain', 'N/A')} lbs (this week)",
            f"- Fatigue: {symptoms.get('fatigue', 'N/A')}",
            f"- Urine output: {symptoms.get('urine_output', 'N/A')}",
        ]

        if patient_id:
            prompt_parts.append(f"- Patient ID: {patient_id}")

        if patient_context:
            prompt_parts.append(f"- Patient context: {patient_context}")

        # Add SRTR population statistics if patient context includes required fields
        srtr_data_available = False
        if patient_context:
            organ = patient_context.get("organ_type", "kidney")
            age_group = patient_context.get("age_group", "50-64")
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
                        "\nIMPORTANT: Include in your JSON response:",
                        "1. 'rejection_probability' (0.0-1.0) - based on symptom severity and SRTR baseline",
                        "2. 'urgency' (LOW/MEDIUM/HIGH/CRITICAL)",
                        "3. 'risk_level' (low/medium/high/critical)",
                        "4. 'recommended_action' - specific clinical action",
                        "5. 'reasoning_steps' (list) - your clinical reasoning",
                        "6. 'similar_cases' (list of 3) - generate realistic cases based on SRTR data",
                        "   Each case: {symptoms: str, outcome: str, similarity: float}",
                        "7. 'srtr_data_source' with:",
                        "   - source: SRTR 2023 Annual Data Report",
                        f"   - organ: {organ.capitalize()}",
                        f"   - age_group: {age_group}",
                        f"   - baseline_rejection_rate: {rejection_rate}",
                        f"   - total_records: {srtr._summary.get('total_records', 'N/A')}",  # type: ignore[union-attr]
                    ]
                )
                srtr_data_available = True
            except Exception:
                # If SRTR data unavailable, continue without it
                prompt_parts.append("\n--- WARNING: SRTR data unavailable (demo mode) ---")

        if not srtr_data_available:
            prompt_parts.append(
                "\nProvide a JSON response with: rejection_probability, urgency, "
                "risk_level, recommended_action, reasoning_steps (list), "
                "similar_cases (list of 3 dicts)."
            )

        return "\n".join(prompt_parts)

    def _parse_agent_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK agent response into structured format.

        Args:
            response: Raw agent response from ADK

        Returns:
            Structured dict with rejection risk data
        """
        response_text = str(response)

        # Try to extract and parse JSON from the response
        parsed_json = extract_json_from_response(response_text)

        if parsed_json:
            # Use parsed values from AI (organ-specific, patient-specific)
            return {
                "rejection_probability": parsed_json.get("rejection_probability", 0.5),
                "urgency": parsed_json.get("urgency", "MEDIUM"),
                "risk_level": parsed_json.get("risk_level", "medium"),
                "recommended_action": parsed_json.get(
                    "recommended_action", "Monitor symptoms and contact team if worsens"
                ),
                "reasoning_steps": parsed_json.get("reasoning_steps", []),
                "similar_cases": parsed_json.get("similar_cases", []),
                "srtr_data_source": parsed_json.get("srtr_data_source"),
                "agent_name": self.agent.name,
                "raw_response": response_text,
            }
        else:
            # Fallback if JSON parsing fails
            return {
                "rejection_probability": 0.5,
                "urgency": "MEDIUM",
                "risk_level": "medium",
                "recommended_action": "Unable to parse AI response. Review full analysis and contact team.",
                "reasoning_steps": [response_text],
                "similar_cases": [],
                "agent_name": self.agent.name,
                "raw_response": response_text,
            }
