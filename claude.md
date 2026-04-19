# Claude Project Context - Transplant Medication Adherence

## Project Overview

**Name**: Transplant Medication Adherence Multi-Agent System
**Goal**: Migrate existing monolithic transplant medication adherence application to a multi-agent system using Google's Agent Development Kit (ADK) to qualify for Cloud Run Hackathon "Best of AI Agents" category ($8,000 prize).

**Core Purpose**: Help kidney transplant patients manage their complex medication regimens by providing AI-powered guidance for:
- Missed dose analysis (what to do when medication is taken late)
- Rejection symptom monitoring
- Drug interaction checking

**Hackathon Requirements**:
- Built with Google's Agent Development Kit (ADK)
- Minimum 2 AI agents that communicate
- Deployed to Cloud Run
- Deadline: November 10, 2025

## Current Status

**Phase**: Planning - Honeycomb.io observability integration
**Last Session**: 2025-11-30
**Current Branch**: `main` (planning artifacts added)

### Completed Milestones
- ✅ **Task 1.0**: ADK Installation and Configuration
  - Installed google-adk==1.17.0 with 100+ dependencies
  - Created agent configurations with medical domain knowledge
  - Set up project structure (`services/agents/`, `services/config/`)
  - Created verification scripts and comprehensive documentation
  - **PR #4 merged**: All CI checks passing

- ✅ **Issue #5**: CI/CD Infrastructure Fix
  - Fixed pip "resolution-too-deep" error using legacy resolver
  - Added pip caching to all workflows
  - Reduced CI runtime from 16+ minute timeout to ~1 minute
  - **PR #6 merged**: All workflows optimized

- ✅ **Issue #22**: Real Rejection Detection with SRTR Data (**PR #23 merged**)
  - Created RejectionRiskAgent with SRTR population data (11,709+ kidney recipients)
  - Implemented `/rejection/analyze` API endpoint
  - Replaced frontend mock with real AI-powered analysis
  - Created BaseADKAgent to reduce code duplication (10.32% → 7.9%)
  - Refactored MedicationAdvisorAgent to use BaseADKAgent
  - Added 6 unit tests for RejectionRiskAgent (95% coverage)
  - Updated integration tests for 4 specialist agents
  - **Deployed to Cloud Run**: revision `missed-dose-service-00021-2vl`
  - **Updated Netlify frontend**: https://transplant-medication-demo.netlify.app/
  - **156 tests passing**, 17 skipped, 1 transient API error

### Next Steps
- **Current**: Honeycomb.io observability integration (planning complete, ready for implementation)
  - PRD: `docs/features/honeycomb-observability-PLANNED/prd.md`
  - Tasks: 84 sub-tasks across 6 phases (11-15 hours estimated)
  - Purpose: Interview demonstration + production monitoring
- **Future**: Extract SRTR integration logic to shared utility (reduce duplication from 7.9% to <3%)
- **Future**: Implement SymptomMonitor, DrugInteractionChecker, and Coordinator agents

## Technology Stack

### Core Framework
- **Python**: 3.12+ (Ubuntu 24.04+ requires virtual environments)
- **Google ADK**: 1.17.0 (Agent Development Kit for multi-agent orchestration)
- **Gemini 2.0 Flash**: LLM model for all 4 agents

### Backend Services
- **Flask**: 3.0.0 (REST API framework)
- **Firestore**: 2.13.0 (Patient data and session state)
- **Cloud Run**: Deployment target (not Vertex AI)

### Development Tools
- **Ruff**: Linting and formatting
- **mypy**: Type checking
- **pytest**: Testing framework with coverage
- **Bandit/Safety**: Security scanning
- **Pre-commit hooks**: Automated code quality checks

### CI/CD
- **GitHub Actions**: All workflows optimized with pip caching
- **SonarCloud**: Code quality analysis
- **Legacy pip resolver**: Required for ADK's complex dependency graph

## Architecture

### Current Architecture (Monolithic)
```
REST API → Single Gemini Client → Firestore
```

### Target Architecture (Multi-Agent)
```
REST API → Coordinator Agent → [MedicationAdvisor, SymptomMonitor, DrugInteractionChecker]
                           ↓
                      Firestore (shared state)
```

### Agent Specifications

#### 1. Coordinator Agent (TransplantCoordinator)
- **Role**: Routes requests to appropriate specialist agents
- **Pattern**: ADK parallel execution or LLM-driven delegation
- **Model**: Gemini 2.0 Flash
- **Temperature**: 0.3 (medical accuracy)

#### 2. Medication Advisor Agent
- **Role**: Missed dose analysis
- **Knowledge**:
  - Tacrolimus: 12-hour therapeutic window
  - Mycophenolate: 12-hour window
  - Prednisone: 24-hour window
- **Outputs**: Recommendation, risk level, next steps

#### 3. Symptom Monitor Agent
- **Role**: Rejection detection
- **Knowledge**: Kidney transplant rejection symptoms
- **Outputs**: Risk assessment, urgency level

#### 4. Drug Interaction Checker Agent
- **Role**: Medication interaction analysis
- **Knowledge**: CYP3A4 interactions (e.g., Tacrolimus + Grapefruit)
- **Outputs**: Interaction warnings, severity

### Project Structure
```
transplant-gcp/
├── .github/workflows/       # CI/CD (optimized with legacy resolver)
├── docs/
│   ├── ai-docs/            # AI-specific documentation
│   ├── features/           # PRD and feature specs
│   └── installation/       # ADK setup guides
├── scripts/                # Verification and build scripts
├── services/
│   ├── agents/            # Agent implementations (NEW)
│   │   ├── __init__.py
│   │   └── test_agent.py  # Verification script
│   ├── config/            # Agent configurations (NEW)
│   │   ├── __init__.py
│   │   └── adk_config.py  # Agent prompts and settings
│   └── missed-dose/       # Legacy service (to be deprecated)
├── tests/                 # Test suite
├── requirements.txt       # Dependencies (includes ADK)
├── pyproject.toml        # Project configuration
└── README.md             # Project overview
```

## Implementation Details

### ADK Configuration (`services/config/adk_config.py`)
- **Model**: `gemini-2.0-flash` for all agents
- **Temperature**: 0.3 (medical accuracy over creativity)
- **Max Tokens**: 800 (concise medical guidance)
- **Agent Prompts**: Include medical domain knowledge
  - Therapeutic windows for immunosuppressants
  - CYP3A4 interaction knowledge
  - Rejection symptom recognition

### Key Files Created (Task 1.0)

1. **`requirements.txt`**: Main dependencies
   ```python
   google-adk==1.17.0
   google-cloud-firestore==2.13.0
   google-generativeai==0.3.0
   Flask==3.0.0
   flask-cors>=4.0.2
   gunicorn>=23.0.0
   ```

2. **`services/config/adk_config.py`**: Agent configurations
   - Model constants and generation config
   - 4 agent-specific configurations with medical prompts
   - Temperature, token limits, top-p/top-k settings

3. **`scripts/verify_adk_installation.py`**: Installation verification
   - 4 verification checks
   - Tests ADK import, agent creation, config loading

4. **`docs/installation/adk-setup.md`**: Installation guide
   - Simple 2-step installation process
   - Verification instructions
   - Troubleshooting tips

### CI/CD Configuration

**Problem Solved**: Pip's new resolver couldn't handle ADK's complex dependency graph (100+ packages), causing "resolution-too-deep" error and 16-minute timeouts.

**Solution Applied**:
```yaml
# All workflows now use:
- cache: 'pip'
- cache-dependency-path: 'requirements.txt'
- pip install --use-deprecated=legacy-resolver -r requirements.txt
```

**Results**:
- Installation time: 16+ minutes → ~1 minute
- All checks passing consistently
- Cache working correctly

## Recent Changes

### Session: 2025-11-30 - Honeycomb.io Observability Planning

**Objective**: Create comprehensive PRD and task breakdown for Honeycomb.io observability integration to support Honeycomb Signals team interview preparation and production monitoring.

**Deliverables Created**:
1. **PRD** (`docs/features/honeycomb-observability-PLANNED/prd.md`)
   - Comprehensive engineering PRD (Option 2 structure)
   - Dual-purpose: Interview demonstration + production observability
   - 10 Functional Requirements (FR1-FR10)
   - 6 Technical Requirements (TR1-TR6)
   - 5 Non-Functional Requirements (NFR1-NFR5)
   - Complete code examples for all major components
   - 7 interview-ready Honeycomb queries with talking points
   - Risk analysis with mitigation strategies

2. **Task List** (`docs/features/honeycomb-observability-PLANNED/tasks.md`)
   - 84 actionable sub-tasks across 6 parent tasks
   - Task 1.0: OpenTelemetry infrastructure (10 sub-tasks)
   - Task 2.0: PII/PHI filtering (9 sub-tasks)
   - Task 3.0: Flask + core agents (18 sub-tasks)
   - Task 4.0: Gemini API tracing (11 sub-tasks)
   - Task 5.0: Production hardening (25 sub-tasks)
   - Task 6.0: Interview prep (15 sub-tasks)

3. **Status Tracker** (`docs/features/honeycomb-observability-PLANNED/status.md`)
   - Progress tracking by phase
   - Milestone checkpoints
   - Implementation notes

4. **Honeycomb Account Setup**
   - Created account at honeycomb.io
   - Generated API key with "Environments: Write" scope
   - Stored securely in `pass`

**Key Decisions**:
- **Dual-mode exporter**: Support both OTLP and HTTP API (feature flag)
- **PII/PHI filtering**: Production-safe with patient ID hashing and symptom sanitization
- **MVP scope**: Focus on core agents (TransplantCoordinator + MedicationAdvisor)
- **Interview focus**: Demonstrate "visible product engineering" for Honeycomb Signals team

**Estimated Effort**: 11-15 hours over 2-3 days

**Status**: Planning complete, ready for implementation

---

### Session: 2025-11-09 - Real Rejection Detection

### PR #23: Real Rejection Detection with SRTR Data ✅
- **Created RejectionRiskAgent** (`services/agents/rejection_risk_agent.py`)
  - Analyzes symptoms: fever, weight gain, fatigue, urine output
  - Integrates SRTR population data (11,709+ kidney recipients)
  - Returns rejection probability, urgency, risk level, clinical recommendations
  - Generates similar patient cases based on SRTR statistics

- **Created BaseADKAgent** (`services/agents/base_adk_agent.py`)
  - Base class for all ADK agents (133 lines)
  - Provides shared initialization (Agent, Runner, InMemorySessionService)
  - Common `_invoke_agent()` method for async execution
  - Reduced code duplication from 10.32% to 7.9% (23% improvement)

- **Refactored MedicationAdvisorAgent**
  - Now inherits from BaseADKAgent
  - Removed ~35 lines of duplicated initialization/session code
  - Maintains agent-specific prompt building and response parsing

- **Added API Endpoint**: `POST /rejection/analyze` on Cloud Run
  - Accepts symptom data and patient context
  - Returns AI-powered rejection risk analysis
  - Includes SRTR data source attribution

- **Frontend Integration** (`demo/index.html`)
  - Replaced 2.5-second mock delay with real API calls
  - Added SRTR data source display showing population baselines
  - Act 2: Rejection Detection now uses real AI

- **Test Coverage**
  - New: `tests/unit/agents/test_rejection_risk_agent.py` (6 tests, 95% coverage)
  - Updated: `tests/integration/test_cloud_run_deployment.py` (4 specialists instead of 3)
  - Updated: Test mocks to patch `base_adk_agent` module
  - **156 tests passing**, 17 skipped

- **Deployments**
  - Cloud Run: revision `missed-dose-service-00021-2vl`
  - Netlify: https://transplant-medication-demo.netlify.app/

- **Status**: Merged to main with squash commit

### Files Modified
- `services/agents/rejection_risk_agent.py` (NEW - 231 lines)
- `services/agents/base_adk_agent.py` (NEW - 133 lines)
- `services/agents/medication_advisor_agent.py` (refactored to use BaseADKAgent)
- `services/config/adk_config.py` (added REJECTION_RISK_CONFIG)
- `services/missed-dose/main.py` (added `/rejection/analyze` endpoint)
- `demo/index.html` (replaced mock with real API)
- `tests/unit/agents/test_rejection_risk_agent.py` (NEW - 234 lines)
- `tests/unit/agents/test_medication_advisor_agent.py` (updated mocks)
- `tests/integration/test_cloud_run_deployment.py` (expect 4 agents)
- `CHANGELOG.md` (documented v1.2.0 changes)

## Dependencies

### External Services
- **Google Cloud Platform**:
  - Firestore (patient data storage)
  - Cloud Run (deployment target)
  - Gemini 2.0 Flash API (LLM model)

### Python Packages (Key Dependencies)
- `google-adk==1.17.0` - Agent Development Kit framework
- `google-cloud-firestore==2.13.0` - Database
- `google-generativeai==0.3.0` - Gemini API
- `Flask==3.0.0` - REST API framework

### Development Dependencies
- `pytest>=7.4.0` - Testing
- `ruff>=0.3.0` - Linting
- `mypy>=1.5.0` - Type checking
- `bandit[toml]` - Security scanning
- `pre-commit` - Git hooks

## Known Issues

### Resolved
- ✅ CI/CD timeouts (fixed with legacy pip resolver)
- ✅ Dependency resolution errors (fixed with legacy resolver)
- ✅ ADK installation complexity (simplified to 2-step process)

### Current
None

### Future Considerations
- SonarCloud Quality Gate failures due to insufficient code coverage (acceptable - infrastructure work)
- Legacy resolver may not catch edge-case dependency conflicts (acceptable - we verify locally first)

## Development Workflow

### Branch Strategy
- **Main branch**: Production-ready code only
- **Feature branches**: All development work
  - Pattern: `feature/task-X.Y-description`
  - Example: `feature/task-1.0-adk-installation`
  - Pattern: `fix/issue-description`
  - Example: `fix/ci-dependency-caching`

### Git Workflow (MANDATORY)
1. Create feature branch for all work
2. Make changes and test locally
3. Commit with meaningful messages
4. Push branch to remote
5. Create PR with comprehensive description
6. Monitor CI checks
7. Wait for user approval before merging
8. Squash merge to keep history clean

### Pre-commit Hooks
- Ruff linting and formatting
- mypy type checking
- Trailing whitespace removal
- YAML validation
- Bandit security scan (high severity only)

### Testing
- Unit tests in `tests/`
- Coverage reporting with pytest-cov
- Type checking with mypy
- Security scanning with Bandit/Safety

## Key Learnings

### 1. Pip Dependency Resolution
**Problem**: ADK has 100+ dependencies with complex interdependencies. Pip's new resolver does deep backtracking which can exceed maximum depth, causing "resolution-too-deep" error.

**Solution**: Use `--use-deprecated=legacy-resolver` in CI/CD workflows. Legacy resolver uses simpler algorithm (faster, less precise) which works fine when dependencies are known to be compatible.

**Trade-off**: May not catch some edge-case conflicts, but acceptable since we test locally with modern resolver first.

### 2. GitHub Actions Timeouts
**Learning**: GitHub Actions has multiple timeout levels:
- Workflow-level timeout (default 360 minutes)
- Job-level timeout (configurable)
- Step-level timeout (default varies by runner)

The issue was NOT a timeout but a dependency resolution error that took ~16 minutes before failing.

### 3. ADK Installation Best Practices
**Key Insight**: Let pip handle all dependencies automatically. Complex workarounds with `--no-deps` are fragile and unnecessary.

**Best Practice**:
```bash
# Simple approach that works:
pip install google-adk==1.17.0
pip install -r requirements.txt

# Don't do complex workarounds with --no-deps
```

### 4. Virtual Environment Management
**Ubuntu 24.04+ Requirement**: System Python requires virtual environments (externally-managed-environment).

**Best Practice**: Always use descriptively named venvs:
```bash
python3 -m venv transplant-gcp-venv
source transplant-gcp-venv/bin/activate
```

### 5. Medical Domain Knowledge in Prompts
**Key Insight**: Include specific medical knowledge in agent prompts:
- Therapeutic windows (Tacrolimus: 12h, Prednisone: 24h)
- Drug interactions (CYP3A4 inducers/inhibitors)
- Rejection symptoms specific to kidney transplants

This improves agent accuracy and reduces hallucination.

### 6. BaseADK Agent Pattern (Session: 2025-11-09)
**Problem**: Code duplication between RejectionRiskAgent and MedicationAdvisorAgent (10.32% duplication - SonarCloud threshold: 3%)
- Both agents had identical `__init__` boilerplate (~30 lines)
- Both agents had identical async session management code (~35 lines)
- Only difference was agent-specific prompt building and response parsing

**Solution**: Extract common patterns to `BaseADKAgent` base class
- Shared initialization (Agent, Runner, InMemorySessionService)
- Common `_invoke_agent(prompt: str) -> str` method
- Stub `_parse_agent_response()` for subclasses to override
- **Result**: Reduced duplication from 10.32% to 7.9% (23% improvement)

**Key Learning**: Inheritance works well for ADK agents when:
- Agent initialization is identical
- Async execution pattern is identical
- Only prompts and response parsing differ
- Trade-off: 7.9% still exceeds 3% threshold due to SRTR integration logic, but accepted for code clarity

### 7. Test Mocking After Refactoring
**Problem**: After extracting BaseADKAgent, 17 unit tests failed with `AttributeError: module has no attribute 'Agent'`

**Root Cause**: Tests were mocking `services.agents.medication_advisor_agent.Agent` but refactored code no longer imports Agent directly (imports from BaseADKAgent instead)

**Solution**: Update all `@patch` decorators to point to base class:
```python
# Before refactoring:
@patch("services.agents.medication_advisor_agent.Agent")
@patch("services.agents.medication_advisor_agent.types")

# After refactoring:
@patch("services.agents.base_adk_agent.Agent")
@patch("services.agents.base_adk_agent.types")
```

**Key Learning**: When extracting base classes, update test mocks to patch the new import location, not the subclass module.

### 8. SonarCloud Quality Gate Trade-offs
**Context**: SonarCloud failed with duplication: 7.9% (threshold: 3%)
- SRTR integration logic duplicated between agents
- Both agents have similar try/except blocks
- Both agents format SRTR stats for prompts similarly

**Decision**: Accept 7.9% duplication (merged PR anyway)
**Reasoning**:
- Agent-specific code is clearer and more maintainable
- Extracting to utility would add complexity
- 23% improvement from BaseADKAgent refactoring
- Can revisit if duplication increases further

**Key Learning**: Quality gates are guidelines, not absolutes. Sometimes code clarity and maintainability > hitting exact metrics.

## Documentation References

- **PRD**: `docs/features/adk-multi-agent-migration-PLANNED/prd.md`
- **ADK Setup**: `docs/installation/adk-setup.md`
- **Dependency Workaround**: `docs/installation/dependency-conflict-workaround.md` (historical reference)
- **Changelog**: `CHANGELOG.md`
- **TODO**: `todo.md`

## Contact & Resources

- **Repository**: https://github.com/adamkwhite/transplant-gcp
- **Hackathon**: Cloud Run Hackathon - AI Agents Category
- **Deadline**: November 10, 2025
- **Prize**: $8,000 (Best of AI Agents) + Grand Prize eligibility

---

**Last Updated**: 2025-11-30
**Last Session Focus**: Honeycomb.io Observability Planning
**Current Status**: Planning - Comprehensive PRD and 84 tasks ready for implementation
