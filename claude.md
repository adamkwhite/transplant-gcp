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

**Phase**: Task 1.0 Complete - Ready to implement agent classes
**Last Session**: 2025-10-30
**Current Branch**: `main` (all work merged)

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

### Next Steps
- **Task 2.0**: Implement Core Agent Classes (4 agents)
- **Task 3.0**: Build Multi-Agent Communication Layer
- **Task 4.0**: Create Backward-Compatible REST API
- **Task 5.0**: Deploy to Cloud Run
- **Task 6.0**: Testing and Validation
- **Task 7.0**: Documentation and Demo

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

## Recent Changes (Last Session: 2025-10-30)

### PR #4: Task 1.0 - ADK Installation ✅
- Installed Google ADK with 100+ dependencies
- Created agent configurations with medical knowledge
- Set up project structure for agents
- Created verification scripts
- Added comprehensive documentation
- **Status**: Merged to main, all checks passing

### PR #6: CI/CD Infrastructure Fix ✅
- Identified root cause: pip "resolution-too-deep" error
- Applied legacy resolver fix
- Added pip caching to all workflows
- Removed unnecessary timeouts after confirming fix
- **Status**: Merged to main, ~1 minute CI runs

### Files Modified
- `.github/workflows/ci.yml`: Added legacy resolver, pip caching
- `.github/workflows/security.yml`: Same optimizations
- `.github/workflows/sonarcloud.yml`: Same optimizations
- `.gitignore`: Added ADK-specific exclusions
- `CHANGELOG.md`: Documented v1.1.0 changes

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

**Last Updated**: 2025-10-30
**Last Session Focus**: Task 1.0 (ADK Installation) + CI/CD Fix
**Current Status**: Ready for Task 2.0 (Implement Agent Classes)
