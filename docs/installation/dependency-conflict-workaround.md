# Dependency Conflict Workaround for Google ADK

## Issue
When installing `google-adk>=1.17.0`, you may encounter this error:

```
ERROR: Cannot install -r requirements.txt (line 4), google-adk and google-cloud-aiplatform[agent-engines]==1.121.0
because these package versions have conflicting dependencies.

The conflict is caused by:
    google-adk 1.17.0 depends on opentelemetry-sdk<=1.37.0 and >=1.37.0
    google-cloud-aiplatform[agent-engines] 1.121.0 depends on opentelemetry-sdk<2
```

## Root Cause
- `google-adk` requires **exactly** `opentelemetry-sdk==1.37.0`
- `google-cloud-aiplatform[agent-engines]` (dependency of ADK) has conflicting OpenTelemetry requirements
- Multiple OpenTelemetry exporters have incompatible version ranges

## Solution 1: Install Without Agent Engines Extra (Recommended)

Since we're deploying to Cloud Run (not Vertex AI Agent Engine), we don't need the `agent-engines` extra.

**Step 1**: Install google-adk without extras first

```bash
pip install --no-deps google-adk==1.17.0
```

**Step 2**: Install ADK dependencies manually (skipping agent-engines)

```bash
pip install \
  "google-generativeai>=0.8.3" \
  "google-genai>=1.0.0" \
  "absl-py>=1.0.0,<3.0.0" \
  "protobuf>=3.20.3,!=4.25.0,!=4.25.1,!=4.25.2,!=4.25.3,<6.0.0dev" \
  "opentelemetry-sdk==1.37.0" \
  "opentelemetry-api==1.37.0" \
  "opentelemetry-exporter-otlp-proto-http==1.37.0" \
  "aiohttp>=3.8.0"
```

**Step 3**: Install remaining requirements

```bash
pip install -r requirements.txt --no-deps
pip install Flask flask-cors google-cloud-firestore gunicorn
```

## Solution 2: Install Dependencies Separately

```bash
# 1. Install google-adk and its dependencies first
pip install google-adk==1.17.0 --no-deps
pip install "opentelemetry-sdk==1.37.0" "opentelemetry-api==1.37.0"

# 2. Install other dependencies
pip install google-cloud-firestore google-generativeai Flask flask-cors gunicorn
```

## Solution 3: Use pip-tools (Most Reliable)

Create `requirements.in`:
```txt
google-adk>=1.17.0
google-cloud-firestore==2.13.0
google-generativeai==0.3.0
Flask==3.0.0
flask-cors>=4.0.2
gunicorn>=23.0.0
```

Then:
```bash
pip install pip-tools
pip-compile requirements.in
pip-sync requirements.txt
```

## Verification After Installation

```bash
# Verify ADK is installed
python -c "import google.adk; print(google.adk.__version__)"

# Run verification script
python scripts/verify_adk_installation.py

# Test agent creation
python -m services.agents.test_agent
```

## Known Issues

This is a known issue in the ADK repository:
- GitHub Issue: [#1670 - OpenTelemetry context errors](https://github.com/google/adk-python/issues/1670)
- Status: Fixed in ADK v1.11.0+  for most use cases
- The dependency conflict is separate from the context detachment issue

## Alternative: Wait for Updated google-adk

The google-adk team may release a version with relaxed OpenTelemetry constraints. Check:
- [google-adk releases](https://github.com/google/adk-python/releases)
- [google-adk on PyPI](https://pypi.org/project/google-adk/)

## For This Project

Since we're deploying to Cloud Run (not Vertex AI), we don't need `google-cloud-aiplatform` at all. The conflict can be avoided by installing ADK dependencies manually.

**Recommended installation order**:
1. Create virtual environment
2. Install google-adk with `--no-deps`
3. Install specific OpenTelemetry versions
4. Install remaining dependencies
5. Verify installation

This approach gives us full control over dependency resolution and avoids the pip resolver conflict.
