"""Edge-case tests for response_parser — covers unclosed code blocks and incomplete JSON."""

from services.agents.response_parser import extract_json_from_response


class TestExtractCodeBlockEdges:
    def test_unclosed_code_block_falls_through_to_raw_json(self):
        response = '```json\n{"key": "value"}'
        result = extract_json_from_response(response)
        assert result is not None
        assert result["key"] == "value"

    def test_unclosed_plain_code_block_falls_through_to_raw_json(self):
        response = '```\n{"key": "value"}'
        result = extract_json_from_response(response)
        assert result is not None
        assert result["key"] == "value"


class TestFindJsonObjectEdges:
    def test_incomplete_json_braces(self):
        response = '{"key": "value"'
        result = extract_json_from_response(response)
        assert result is None

    def test_json_with_escaped_quotes(self):
        response = r'{"msg": "she said \"hello\""}'
        result = extract_json_from_response(response)
        assert result is not None
        assert result["msg"] == 'she said "hello"'

    def test_json_with_backslash_not_before_quote(self):
        response = r'{"path": "C:\\Users\\test"}'
        result = extract_json_from_response(response)
        assert result is not None

    def test_no_braces_at_all(self):
        response = "Just plain text with no JSON"
        result = extract_json_from_response(response)
        assert result is None
