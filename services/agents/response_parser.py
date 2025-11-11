"""
Shared JSON parsing utilities for ADK agent responses.

All agents receive AI responses that contain JSON. This module provides
standardized parsing logic to extract structured data from those responses.
"""

import json
import re
from typing import Any


def extract_json_from_response(response_text: str) -> dict[str, Any] | None:
    """
    Extract and parse JSON from an AI response.

    The AI may wrap JSON in markdown code blocks or return it raw.
    This function tries multiple extraction patterns.

    Args:
        response_text: Raw text response from the AI

    Returns:
        Parsed JSON dict if successful, None if parsing fails
    """
    if not response_text:
        return None

    # Try to extract JSON from markdown code blocks
    # Pattern 1: ```json ... ```
    json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Pattern 2: ``` ... ``` (without json tag)
    json_match = re.search(r"```\s*([\s\S]*?)\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Pattern 3: Raw JSON object anywhere in text
    json_match = re.search(r"(\{[\s\S]*\})", response_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return None
