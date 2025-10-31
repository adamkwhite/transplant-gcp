#!/usr/bin/env python3
"""
Verify Google ADK installation and test basic functionality.
Run this script after installing google-adk to ensure everything is working.
"""

import sys


def verify_adk_import():
    """Test that ADK can be imported."""
    try:
        import google.adk

        print("✅ google-adk successfully imported")
        print(f"   Version: {google.adk.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import google-adk: {e}")
        return False


def verify_adk_agents():
    """Test that ADK agents module is available."""
    try:
        from google.adk.agents import Agent, LlmAgent  # noqa: F401

        print("✅ ADK agents module available (Agent, LlmAgent)")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ADK agents: {e}")
        return False


def verify_adk_tools():
    """Test that ADK tools module is available."""
    try:
        from google.adk.tools import Tool  # noqa: F401

        print("✅ ADK tools module available")
        return True
    except ImportError as e:
        print(f"❌ Failed to import ADK tools: {e}")
        return False


def test_simple_agent_creation():
    """Test creating a simple agent (without API key)."""
    try:
        from google.adk.agents import Agent

        # Create a simple agent without actually calling any APIs
        test_agent = Agent(
            name="test_agent",
            model="gemini-2.0-flash",
            instruction="You are a test agent.",
            description="A simple test agent to verify ADK installation.",
        )
        print(f"✅ Successfully created test agent: {test_agent.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to create test agent: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Google ADK Installation Verification")
    print("=" * 60)
    print()

    checks = [
        ("Import google.adk", verify_adk_import),
        ("Import ADK agents", verify_adk_agents),
        ("Import ADK tools", verify_adk_tools),
        ("Create test agent", test_simple_agent_creation),
    ]

    results = []
    for name, check_func in checks:
        print(f"Running: {name}")
        result = check_func()
        results.append(result)
        print()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All checks passed! ADK is ready to use.")
        return 0
    else:
        print("⚠️  Some checks failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
