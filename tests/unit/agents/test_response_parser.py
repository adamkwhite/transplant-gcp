"""Unit tests for response_parser module."""

from services.agents.response_parser import extract_json_from_response


class TestExtractJsonFromResponse:
    """Test suite for extract_json_from_response function."""

    def test_extracts_json_from_markdown_json_block(self) -> None:
        """Test extraction from ```json code block."""
        response = """
Here is the analysis:

```json
{
    "has_interaction": true,
    "severity": "moderate",
    "confidence": 0.85
}
```

Hope this helps!
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert result["has_interaction"] is True
        assert result["severity"] == "moderate"
        assert result["confidence"] == 0.85

    def test_extracts_json_from_plain_code_block(self) -> None:
        """Test extraction from ``` code block without json tag."""
        response = """
```
{
    "recommendation": "Take now",
    "risk_level": "low"
}
```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert result["recommendation"] == "Take now"
        assert result["risk_level"] == "low"

    def test_extracts_raw_json_object(self) -> None:
        """Test extraction of raw JSON without code blocks."""
        response = '{"urgency": "HIGH", "probability": 0.75}'
        result = extract_json_from_response(response)
        assert result is not None
        assert result["urgency"] == "HIGH"
        assert result["probability"] == 0.75

    def test_extracts_json_with_surrounding_text(self) -> None:
        """Test extraction when JSON is embedded in text."""
        response = """
Based on the analysis, here's the result:
{"status": "success", "value": 42}
Thank you!
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert result["status"] == "success"
        assert result["value"] == 42

    def test_returns_none_for_empty_string(self) -> None:
        """Test that empty string returns None."""
        result = extract_json_from_response("")
        assert result is None

    def test_returns_none_for_invalid_json(self) -> None:
        """Test that invalid JSON returns None."""
        response = "This is not JSON at all"
        result = extract_json_from_response(response)
        assert result is None

    def test_returns_none_for_malformed_json_in_block(self) -> None:
        """Test that malformed JSON in code block returns None."""
        response = """
```json
{
    "key": "value"
    missing_comma_here
    "another": "value"
}
```
"""
        result = extract_json_from_response(response)
        assert result is None

    def test_returns_none_for_non_dict_json(self) -> None:
        """Test that JSON arrays or primitives return None (only dicts accepted)."""
        # Array
        response = '```json\n["item1", "item2"]\n```'
        result = extract_json_from_response(response)
        assert result is None

        # String primitive
        response = '```json\n"just a string"\n```'
        result = extract_json_from_response(response)
        assert result is None

        # Number primitive
        response = "```json\n42\n```"
        result = extract_json_from_response(response)
        assert result is None

    def test_handles_nested_json_objects(self) -> None:
        """Test extraction of nested JSON structures."""
        response = """
```json
{
    "patient": {
        "id": "P123",
        "age": 45
    },
    "results": {
        "score": 0.92,
        "status": "good"
    }
}
```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert result["patient"]["id"] == "P123"
        assert result["patient"]["age"] == 45
        assert result["results"]["score"] == 0.92

    def test_handles_json_with_whitespace(self) -> None:
        """Test extraction handles extra whitespace."""
        response = """
```json

{
    "key1"  :  "value1"  ,
    "key2"  :  123
}

```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert result["key1"] == "value1"
        assert result["key2"] == 123

    def test_prefers_json_tagged_block_over_plain_block(self) -> None:
        """Test that ```json blocks are tried first."""
        response = """
```
{"wrong": "data"}
```

```json
{"correct": "data"}
```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert "correct" in result
        assert result["correct"] == "data"

    def test_handles_json_with_special_characters(self) -> None:
        """Test extraction of JSON with special characters."""
        response = """
```json
{
    "message": "Patient's condition improved by 50%",
    "notes": "Follow-up in 2 weeks @ clinic",
    "tags": ["urgent", "review-needed"]
}
```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert "Patient's condition" in result["message"]
        assert "@" in result["notes"]
        assert "urgent" in result["tags"]

    def test_handles_multiline_strings_in_json(self) -> None:
        """Test extraction of JSON with multiline string values."""
        response = """
```json
{
    "recommendation": "Take the medication now.\\nMonitor for side effects.\\nCall if symptoms worsen.",
    "risk": "low"
}
```
"""
        result = extract_json_from_response(response)
        assert result is not None
        assert "Take the medication now" in result["recommendation"]
        assert "Monitor for side effects" in result["recommendation"]
