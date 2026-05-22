"""Unit tests for BaseADKAgent — covers session-creation branch and default parse."""

from unittest.mock import AsyncMock, MagicMock, patch


class TestBaseADKAgentInvokeSessionCreation:
    @patch("services.agents.base_adk_agent.Runner")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_invoke_agent_creates_session_when_none(self, mock_types, mock_agent, mock_runner_cls):
        from services.agents.base_adk_agent import BaseADKAgent

        mock_runner = MagicMock()
        mock_runner_cls.return_value = mock_runner
        mock_runner.app_name = "test"

        mock_session_svc = AsyncMock()
        mock_session_svc.get_session.return_value = None
        mock_runner.session_service = mock_session_svc

        async def _gen():
            event = MagicMock()
            event.content.parts = [MagicMock(text="hello")]
            yield event

        mock_runner.run_async.return_value = _gen()

        agent = BaseADKAgent(
            agent_config={"name": "T", "model": "m", "description": "d", "instruction": "i"},
            app_name="test",
            session_id_prefix="pfx",
            api_key="k",
        )

        result = agent._invoke_agent("prompt")

        assert result == "hello"
        mock_session_svc.create_session.assert_called_once()


class TestBaseADKAgentDefaultParse:
    @patch("services.agents.base_adk_agent.Runner")
    @patch("services.agents.base_adk_agent.Agent")
    @patch("services.agents.base_adk_agent.types")
    def test_default_parse_agent_response(self, mock_types, mock_agent_cls, mock_runner_cls):
        from services.agents.base_adk_agent import BaseADKAgent

        mock_agent_inst = MagicMock()
        mock_agent_inst.name = "TestAgent"
        mock_agent_cls.return_value = mock_agent_inst

        agent = BaseADKAgent(
            agent_config={"name": "T", "model": "m", "description": "d", "instruction": "i"},
            app_name="test",
            session_id_prefix="pfx",
        )

        result = agent._parse_agent_response("raw text")

        assert result["agent_name"] == "TestAgent"
        assert result["raw_response"] == "raw text"
