"""
Base ADK Agent Implementation

Provides common functionality for all ADK-based agents to reduce code duplication.
Handles agent initialization, session management, and async execution patterns.
"""

import asyncio
from typing import Any

from google.adk.agents import Agent  # type: ignore[import-untyped]
from google.adk.runners import Runner  # type: ignore[import-untyped]
from google.adk.sessions.in_memory_session_service import (
    InMemorySessionService,  # type: ignore[import-untyped]
)
from google.genai import types  # type: ignore[import-untyped]

from services.config.adk_config import DEFAULT_GENERATION_CONFIG, GEMINI_API_KEY


class BaseADKAgent:
    """
    Base class for Google ADK agents.

    Provides common functionality:
    - Agent and Runner initialization
    - Session management
    - Async execution pattern
    - Response parsing interface
    """

    def __init__(
        self,
        agent_config: dict[str, Any],
        app_name: str,
        session_id_prefix: str,
        api_key: str | None = None,
    ):
        """
        Initialize base ADK agent.

        Args:
            agent_config: Dict with name, model, description, instruction
            app_name: Application name for Runner
            session_id_prefix: Prefix for session IDs (e.g., "medication_analysis")
            api_key: Gemini API key (defaults to config if not provided)
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.session_id_prefix = session_id_prefix

        # Create ADK agent instance with generation config
        generate_config = types.GenerateContentConfig(
            temperature=DEFAULT_GENERATION_CONFIG["temperature"],
            max_output_tokens=int(DEFAULT_GENERATION_CONFIG["max_output_tokens"]),
            top_p=DEFAULT_GENERATION_CONFIG["top_p"],
            top_k=DEFAULT_GENERATION_CONFIG["top_k"],
        )

        self.agent = Agent(
            name=agent_config["name"],
            model=agent_config["model"],
            description=agent_config["description"],
            instruction=agent_config["instruction"],
            generate_content_config=generate_config,
        )

        # Create Runner with in-memory session service
        self.runner = Runner(
            app_name=app_name,
            agent=self.agent,
            session_service=InMemorySessionService(),
        )

    def _invoke_agent(self, prompt: str) -> str:
        """
        Invoke agent with a prompt and return response.

        Args:
            prompt: User prompt for the agent

        Returns:
            Agent response text
        """

        async def _run_agent() -> str:
            response_text = ""
            user_message = types.Content(role="user", parts=[types.Part(text=prompt)])

            # Create session if it doesn't exist
            session = await self.runner.session_service.get_session(  # type: ignore[attr-defined]
                app_name=self.runner.app_name,  # type: ignore[attr-defined]
                user_id="system",
                session_id=self.session_id_prefix,
            )
            if not session:
                await self.runner.session_service.create_session(  # type: ignore[attr-defined]
                    app_name=self.runner.app_name,  # type: ignore[attr-defined]
                    user_id="system",
                    session_id=self.session_id_prefix,
                )

            async for event in self.runner.run_async(  # type: ignore[attr-defined]
                user_id="system",
                session_id=self.session_id_prefix,
                new_message=user_message,
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            return response_text

        return asyncio.run(_run_agent())

    def _parse_agent_response(self, response: Any) -> dict[str, Any]:
        """
        Parse ADK agent response into structured format.

        Subclasses should override this method to provide agent-specific parsing.

        Args:
            response: Raw agent response from ADK

        Returns:
            Structured dict with agent response data
        """
        # Default implementation - subclasses should override
        response_text = str(response)

        return {
            "agent_name": self.agent.name,
            "raw_response": response_text,
        }
