"""Root conftest — mock external Google packages before any test imports."""

import sys
from unittest.mock import MagicMock

_GOOGLE_MODULES = [
    "google",
    "google.adk",
    "google.adk.agents",
    "google.adk.runners",
    "google.adk.sessions",
    "google.adk.sessions.in_memory_session_service",
    "google.genai",
    "google.genai.types",
    "google.cloud",
    "google.cloud.pubsub_v1",
    "google.cloud.pubsub_v1.subscriber",
    "google.cloud.pubsub_v1.subscriber.message",
    "google.generativeai",
]

for mod_name in _GOOGLE_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()
