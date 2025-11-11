"""
Shared JSON parsing utilities for ADK agent responses.

All agents receive AI responses that contain JSON. This module provides
standardized parsing logic to extract structured data from those responses.
"""

import json
from typing import Any


def _try_parse_json_dict(text: str) -> dict[str, Any] | None:
    """Try to parse text as JSON dict, return None if fails."""
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _extract_code_block(text: str, marker: str) -> str | None:
    """Extract content between marker and closing ```."""
    start = text.find(marker)
    if start == -1:
        return None

    content_start = start + len(marker)
    # Skip whitespace
    while content_start < len(text) and text[content_start].isspace():
        content_start += 1

    # Find closing ```
    content_end = text.find("```", content_start)
    if content_end == -1:
        return None

    return text[content_start:content_end]


def _find_json_object(text: str) -> str | None:
    """Find first complete JSON object by counting braces."""
    brace_index = text.find("{")
    if brace_index == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False

    for i in range(brace_index, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[brace_index : i + 1]

    return None


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

    # Try ```json ... ``` code block
    content = _extract_code_block(response_text, "```json")
    if content:
        result = _try_parse_json_dict(content)
        if result:
            return result

    # Try ``` ... ``` code block
    content = _extract_code_block(response_text, "```")
    if content:
        result = _try_parse_json_dict(content)
        if result:
            return result

    # Try raw JSON object
    content = _find_json_object(response_text)
    if content:
        result = _try_parse_json_dict(content)
        if result:
            return result

    return None
