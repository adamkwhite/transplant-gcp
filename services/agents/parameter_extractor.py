"""
Parameter Extractor for Multi-Agent Communication

Extracts structured parameters from natural language patient requests using LLM.
Supports extraction of medication names, times, symptoms, and vital signs.
"""

import asyncio
import json
import re
from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.genai import types  # type: ignore[import-untyped]

from services.config.adk_config import (
    DEFAULT_GENERATION_CONFIG,
    GEMINI_API_KEY,
)


class ParameterExtractor:
    """
    LLM-based parameter extraction for natural language requests.

    Extracts:
    - Medication names (e.g., tacrolimus, mycophenolate, prednisone)
    - Scheduled times (e.g., "8:00 AM", "morning dose")
    - Current times (e.g., "2:00 PM", "now")
    - Symptoms (e.g., fever, decreased urine, pain)
    - Vital signs (e.g., temperature, weight, blood pressure)
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the parameter extractor.

        Args:
            api_key: Gemini API key (defaults to config if not provided)
        """
        self.api_key = api_key or GEMINI_API_KEY

        # Create lightweight ADK agent for extraction
        generate_config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for consistent extraction
            max_output_tokens=1024,
            top_p=DEFAULT_GENERATION_CONFIG["top_p"],
            top_k=DEFAULT_GENERATION_CONFIG["top_k"],
        )

        self.agent = Agent(
            name="ParameterExtractor",
            model="gemini-2.0-flash-001",  # Fast model for extraction
            description="Extracts structured parameters from patient requests",
            instruction="""You are a parameter extraction specialist for transplant patient care.
Your job is to extract structured information from natural language patient requests.

Extract the following when present:
- medication_names: List of medication names mentioned
- scheduled_time: When medication should have been taken (24-hour or 12-hour format)
- current_time: Current time mentioned by patient
- time_late_hours: Calculate hours late if both times present
- symptoms: List of symptoms mentioned
- vital_signs: Dict of vital signs (temperature, weight, blood_pressure, etc.)

ALWAYS respond with valid JSON only, no extra text.
""",
            generate_content_config=generate_config,
        )

    def extract_parameters(self, request: str, extraction_type: str = "all") -> dict[str, Any]:
        """
        Extract structured parameters from natural language request.

        Args:
            request: Natural language patient request
            extraction_type: Type of extraction ("all", "medication", "symptoms", "vitals")

        Returns:
            Dict with extracted parameters:
                - medication_names: List[str]
                - scheduled_time: str | None
                - current_time: str | None
                - time_late_hours: float | None
                - symptoms: List[str]
                - vital_signs: Dict[str, Any]
                - confidence: float
        """
        prompt = self._build_extraction_prompt(request, extraction_type)

        try:
            # Use run_async() which works with both ADK 1.16.0 and 1.17.0
            response = asyncio.run(self.agent.run_async(prompt))  # type: ignore[attr-defined]
            response_text = str(response)

            # Extract JSON from response
            extracted = self._parse_json_response(response_text)

            # Add confidence score
            extracted["confidence"] = self._calculate_confidence(extracted)

            return extracted

        except Exception:
            # Fallback to simple extraction on error
            return self._fallback_extraction(request)

    def _build_extraction_prompt(self, request: str, extraction_type: str) -> str:
        """Build prompt for parameter extraction."""

        schema: dict[str, Any]
        if extraction_type == "medication":
            schema = {
                "medication_names": ["list of medication names"],
                "scheduled_time": "scheduled time or null",
                "current_time": "current time or null",
                "time_late_hours": "hours late as float or null",
            }
        elif extraction_type == "symptoms":
            schema = {
                "symptoms": ["list of symptoms"],
                "vital_signs": {
                    "temperature": "value or null",
                    "weight": "value or null",
                    "blood_pressure": "value or null",
                },
            }
        else:  # "all"
            schema = {
                "medication_names": ["list of medication names or empty list"],
                "scheduled_time": "scheduled time or null",
                "current_time": "current time or null",
                "time_late_hours": "hours late as float or null",
                "symptoms": ["list of symptoms or empty list"],
                "vital_signs": {},
            }

        prompt = f"""Extract parameters from this patient request:

Request: "{request}"

Expected JSON schema:
{json.dumps(schema, indent=2)}

Rules:
1. Extract medication names (tacrolimus, mycophenolate, prednisone, etc.)
2. Extract times in consistent format (e.g., "8:00 AM", "14:00")
3. Calculate time_late_hours if both scheduled and current times present
4. Extract all symptoms mentioned
5. Extract vital sign values with units
6. Use null for missing values
7. Return ONLY valid JSON, no markdown, no extra text

JSON response:"""

        return prompt

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

    def _calculate_confidence(self, extracted: dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality."""

        confidence = 0.5  # Base confidence

        # Increase confidence for each field successfully extracted
        if extracted.get("medication_names"):
            confidence += 0.15
        if extracted.get("scheduled_time"):
            confidence += 0.1
        if extracted.get("current_time"):
            confidence += 0.1
        if extracted.get("symptoms"):
            confidence += 0.1
        if extracted.get("vital_signs"):
            confidence += 0.05

        return min(confidence, 1.0)

    def _fallback_extraction(self, request: str) -> dict[str, Any]:
        """Simple keyword-based extraction as fallback."""

        request_lower = request.lower()

        # Extract common medications
        medications = []
        med_keywords = [
            "tacrolimus",
            "prograf",
            "mycophenolate",
            "cellcept",
            "prednisone",
            "cyclosporine",
            "sirolimus",
        ]
        for med in med_keywords:
            if med in request_lower:
                medications.append(med)

        # Extract common symptoms
        symptoms = []
        symptom_keywords = [
            "fever",
            "pain",
            "nausea",
            "vomiting",
            "diarrhea",
            "fatigue",
            "swelling",
            "decreased urine",
            "blood in urine",
        ]
        for symptom in symptom_keywords:
            if symptom in request_lower:
                symptoms.append(symptom)

        # Extract times using regex
        time_pattern = r"\b(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?\b"
        times = re.findall(time_pattern, request)

        scheduled_time = None
        current_time = None

        if times:
            if len(times) >= 1:
                scheduled_time = self._format_time(times[0])
            if len(times) >= 2:
                current_time = self._format_time(times[1])

        return {
            "medication_names": medications,
            "scheduled_time": scheduled_time,
            "current_time": current_time,
            "time_late_hours": None,
            "symptoms": symptoms,
            "vital_signs": {},
            "confidence": 0.4,  # Lower confidence for fallback
        }

    def _format_time(self, time_tuple: tuple[str, ...]) -> str:
        """Format time tuple into consistent string."""
        hour, minute, period = time_tuple
        if not minute:
            minute = "00"
        if period:
            return f"{hour}:{minute} {period.upper()}"
        return f"{hour}:{minute}"

    def extract_for_medication_advisor(self, request: str) -> dict[str, Any]:
        """Extract parameters specifically for MedicationAdvisor agent."""

        params = self.extract_parameters(request, extraction_type="medication")

        # Format for MedicationAdvisor.analyze_missed_dose()
        return {
            "medication": params["medication_names"][0]
            if params["medication_names"]
            else "unknown",
            "scheduled_time": params.get("scheduled_time", "unknown"),
            "current_time": params.get("current_time", "unknown"),
            "confidence": params.get("confidence", 0.0),
        }

    def extract_for_symptom_monitor(self, request: str) -> dict[str, Any]:
        """Extract parameters specifically for SymptomMonitor agent."""

        params = self.extract_parameters(request, extraction_type="symptoms")

        # Format for SymptomMonitor.analyze_symptoms()
        return {
            "symptoms": params.get("symptoms", []),
            "vital_signs": params.get("vital_signs", {}),
            "confidence": params.get("confidence", 0.0),
        }

    def extract_for_drug_interaction(self, request: str) -> dict[str, Any]:
        """Extract parameters specifically for DrugInteractionChecker agent."""

        params = self.extract_parameters(request, extraction_type="medication")

        # Format for DrugInteractionChecker.check_interaction()
        return {
            "medications": params.get("medication_names", []),
            "confidence": params.get("confidence", 0.0),
        }
