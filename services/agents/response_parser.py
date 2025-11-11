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
    # Pattern 1: ```json ... ``` - match JSON in code block
    # Use [^`]+ to match non-backtick characters, preventing catastrophic backtracking
    json_match = re.search(r"```json\s*([^`]+)```", response_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Pattern 2: ``` ... ``` (without json tag)
    # Use [^`]+ to match non-backtick characters, preventing catastrophic backtracking
    json_match = re.search(r"```\s*([^`]+)```", response_text)
    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Pattern 3: Raw JSON object anywhere in text
    # Find first '{' and use brace counting to find matching '}'
    # This avoids regex backtracking issues entirely
    brace_index = response_text.find("{")
    if brace_index != -1:
        # Count braces to find matching closing brace
        depth = 0
        in_string = False
        escape_next = False

        for i in range(brace_index, len(response_text)):
            char = response_text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        # Found matching closing brace
                        try:
                            candidate = response_text[brace_index : i + 1]
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict):
                                return parsed
                        except json.JSONDecodeError:
                            pass
                        break

    return None
