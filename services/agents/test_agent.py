"""
Test Agent for ADK Installation Verification

This simple agent can be used to test that ADK is properly installed and configured.
Run after installing google-adk to verify the installation.

Usage:
    python -m services.agents.test_agent
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def create_test_agent():
    """Create a simple test agent to verify ADK installation."""
    try:
        from google.adk.agents import Agent

        print("Creating test agent...")

        # Create a simple agent (won't actually call API without user input)
        test_agent = Agent(
            name="test_agent",
            model="gemini-2.0-flash",
            instruction="You are a test agent for verifying ADK installation.",
            description="A simple test agent",
        )

        print(f"✅ Successfully created test agent: {test_agent.name}")
        print(f"   Model: {test_agent.model}")
        print(f"   Description: {test_agent.description}")
        return test_agent

    except ImportError as e:
        print(f"❌ Failed to import ADK: {e}")
        print("   Make sure google-adk is installed: pip install google-adk>=1.17.0")
        return None
    except Exception as e:
        print(f"❌ Failed to create test agent: {e}")
        return None


def test_agent_with_config():
    """Test agent creation with our configuration."""
    try:
        from google.adk.agents import Agent

        from services.config.adk_config import MEDICATION_ADVISOR_CONFIG

        print("\nTesting agent creation with project configuration...")

        # Create agent using our config
        config = MEDICATION_ADVISOR_CONFIG
        test_agent = Agent(
            name=config["name"],
            model=config["model"],
            instruction=config["instruction"],
            description=config["description"],
        )

        print(f"✅ Successfully created {test_agent.name} using project config")
        return test_agent

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to create agent with config: {e}")
        return None


def main():
    """Run test agent verification."""
    print("=" * 60)
    print("ADK Test Agent Verification")
    print("=" * 60)
    print()

    # Test 1: Basic agent creation
    agent1 = create_test_agent()

    # Test 2: Agent creation with project config
    agent2 = test_agent_with_config()

    print()
    print("=" * 60)
    if agent1 and agent2:
        print("🎉 All tests passed! ADK is ready for Task 2.0")
        print()
        print("Next Steps:")
        print("1. Set GEMINI_API_KEY environment variable")
        print("2. Begin Task 2.0: Implement Core Agent Classes")
        return 0
    else:
        print("⚠️  Tests failed. Please install ADK:")
        print("   pip install google-adk>=1.17.0")
        print()
        print("Or run the verification script:")
        print("   python scripts/verify_adk_installation.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
