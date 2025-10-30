# Google ADK Installation and Setup Guide

## Prerequisites

- Python 3.12
- Virtual environment (required for Ubuntu 24.04+)
- GEMINI_API_KEY (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Installation Steps

### 1. Create/Activate Virtual Environment

```bash
# If you don't have a virtual environment yet
python3 -m venv transplant-gcp-venv
source transplant-gcp-venv/bin/activate

# Or activate existing venv
source /path/to/your/venv/bin/activate
```

### 2. Install Dependencies

**⚠️ Important**: Due to OpenTelemetry dependency conflicts, install in this specific order:

```bash
# Step 1: Install ADK without dependencies first
pip install --no-deps google-adk==1.17.0

# Step 2: Install OpenTelemetry with exact versions required by ADK
pip install "opentelemetry-sdk==1.37.0" "opentelemetry-api==1.37.0"

# Step 3: Install remaining dependencies
pip install -r requirements.txt
```

**Why this order?** google-adk requires `opentelemetry-sdk==1.37.0` (exact version), which conflicts with other Google Cloud packages. Installing ADK first with `--no-deps` lets us control the dependency resolution.

See `docs/installation/dependency-conflict-workaround.md` for more details and alternative solutions.

### 3. Verify Installation

Run the verification script:

```bash
python scripts/verify_adk_installation.py
```

Expected output:
```
============================================================
Google ADK Installation Verification
============================================================

Running: Import google.adk
✅ google-adk successfully imported
   Version: 1.17.0

Running: Import ADK agents
✅ ADK agents module available (Agent, LlmAgent)

Running: Import ADK tools
✅ ADK tools module available

Running: Create test agent
✅ Successfully created test agent: test_agent

============================================================
Summary
============================================================
Passed: 4/4
🎉 All checks passed! ADK is ready to use.
```

### 4. Test with Project Configuration

Run the test agent:

```bash
python -m services.agents.test_agent
```

Expected output:
```
============================================================
ADK Test Agent Verification
============================================================

Creating test agent...
✅ Successfully created test agent: test_agent
   Model: gemini-2.0-flash
   Description: A simple test agent

Testing agent creation with project configuration...
✅ Successfully created MedicationAdvisor using project config

============================================================
🎉 All tests passed! ADK is ready for Task 2.0

Next Steps:
1. Set GEMINI_API_KEY environment variable
2. Begin Task 2.0: Implement Core Agent Classes
```

### 5. Set Environment Variables

```bash
# Add to your .bashrc or .zshrc for persistence
export GEMINI_API_KEY="your-api-key-here"
export GOOGLE_CLOUD_PROJECT="transplant-prediction"

# Optional: Enable ADK Development UI
export ADK_DEV_UI="true"
export ADK_DEV_UI_PORT="8081"
```

## Troubleshooting

### ImportError: No module named 'google.adk'

**Solution**: Install ADK in your active virtual environment
```bash
# Make sure venv is activated
source /path/to/venv/bin/activate

# Install ADK
pip install google-adk>=1.17.0
```

### Permission Denied (Ubuntu 24.04)

**Problem**: Ubuntu 24.04+ requires virtual environments for pip install

**Solution**: Always use a virtual environment
```bash
python3 -m venv transplant-gcp-venv
source transplant-gcp-venv/bin/activate
pip install google-adk>=1.17.0
```

### Version Mismatch

**Problem**: Older version of ADK installed

**Solution**: Upgrade to latest version
```bash
pip install --upgrade google-adk
```

## ADK Documentation

- [Official Documentation](https://google.github.io/adk-docs/)
- [Python API Reference](https://google.github.io/adk-docs/get-started/python/)
- [GitHub Repository](https://github.com/google/adk-python)
- [Samples](https://github.com/google/adk-samples)

## Project Structure After Setup

```
transplant-gcp/
├── services/
│   ├── agents/              # ✅ Created - Agent implementations (Task 2.0)
│   │   ├── __init__.py      # ✅ Created
│   │   └── test_agent.py    # ✅ Created - Test agent
│   ├── config/              # ✅ Created - ADK configuration
│   │   ├── __init__.py      # ✅ Created
│   │   └── adk_config.py    # ✅ Created - Agent configs
│   ├── gemini_client.py     # Existing - May be integrated or replaced
│   └── missed-dose/         # Existing - Legacy service
├── scripts/
│   └── verify_adk_installation.py  # ✅ Created - Verification script
├── requirements.txt         # ✅ Updated - Added google-adk>=1.17.0
└── docs/
    └── installation/
        └── adk-setup.md     # ✅ This file
```

## Next Steps

Once ADK is installed and verified:

1. **Task 2.0**: Implement Core Agent Classes (4 agents)
   - TransplantCoordinator
   - MedicationAdvisor
   - SymptomMonitor
   - DrugInteractionChecker

2. **Task 3.0**: Build Multi-Agent Communication Layer

3. **Task 4.0**: Create Backward-Compatible REST API

## Support

If you encounter issues:
1. Check the verification script output for specific errors
2. Review the ADK documentation
3. Check GitHub issues: https://github.com/google/adk-python/issues
