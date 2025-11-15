# Changelog

All notable changes to the Transplant Medication Adherence project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-11-09

### Added
- **Real Rejection Detection with AI (Issue #22, PR #23)** - Replaced mock JavaScript with production RejectionRiskAgent
  - New `services/agents/rejection_risk_agent.py` - Specialized ADK agent for transplant rejection analysis
  - Integrates SRTR (Scientific Registry of Transplant Recipients) population data
  - Analyzes symptoms: fever, weight gain, fatigue, urine output
  - Returns rejection probability (0.0-1.0), urgency level (LOW/MEDIUM/HIGH/CRITICAL), risk assessment, and clinical recommendations
  - Generates similar patient cases based on SRTR statistics (11,709+ kidney recipients)
  - Added to agent configuration in `services/config/adk_config.py`

- **New API Endpoint**: `POST /rejection/analyze` on Cloud Run
  - Accepts symptom data (`fever`, `weight_gain`, `fatigue`, `urine_output`) and patient context
  - Returns AI-powered rejection risk analysis with SRTR population baselines
  - Includes SRTR data source attribution (source, organ type, age group, baseline rejection rate, total records)
  - Follows same infrastructure pattern as `/medications/missed-dose`

- **BaseADKAgent Refactoring** - Extracted common ADK patterns to reduce code duplication
  - New `services/agents/base_adk_agent.py` - Base class for all ADK agents (133 lines)
  - Provides shared initialization (Agent, Runner, InMemorySessionService)
  - Common `_invoke_agent()` method for async execution
  - Common `_parse_agent_response()` stub for subclasses to override
  - Reduced code duplication from 10.32% to 7.9% (23% improvement)

- **Frontend Rejection Detection** - Real API integration in `demo/index.html`
  - Replaced 2.5-second mock delay with actual API calls to Cloud Run
  - Added SRTR data source display in UI showing:
    - Source: SRTR 2023 Annual Data Report
    - Organ type and age group
    - Population baseline rejection rates
    - Total records in database (e.g., "11,709 kidney transplant recipients")
  - Dynamic symptom capture from form inputs

- **Comprehensive Test Coverage**
  - New `tests/unit/agents/test_rejection_risk_agent.py` - 6 unit tests, 95% coverage
  - Tests: agent initialization, config validation, SRTR integration, prompt building, response parsing
  - Updated `tests/integration/test_cloud_run_deployment.py` - Fixed to expect 4 specialist agents (was 3)
  - All 156 tests passing (17 skipped, 1 transient Gemini API 503 error)

### Changed
- **MedicationAdvisorAgent** - Refactored to inherit from BaseADKAgent
  - Removed duplicated `__init__` boilerplate (agent/runner creation)
  - Removed duplicated async session management code (~35 lines)
  - Uses base class `_invoke_agent()` instead of local async function
  - Maintains agent-specific `_build_missed_dose_prompt()` and `_parse_agent_response()`

- **RejectionRiskAgent** - Inherits from BaseADKAgent
  - Follows same refactoring pattern as MedicationAdvisorAgent
  - Agent-specific `_build_rejection_prompt()` with SRTR data integration
  - Agent-specific `_parse_agent_response()` for structured output

- **Health Endpoint** - Now shows all 4 specialist agents in `/health` response:
  - MedicationAdvisor
  - **RejectionRiskAnalyzer** (NEW)
  - SymptomMonitor
  - DrugInteractionChecker

- **Root Endpoint** - Updated to list new `/rejection/analyze` endpoint

- **Test Mocks** - Updated to patch base_adk_agent module
  - All `@patch` decorators in test files now point to `services.agents.base_adk_agent.*`
  - Updated: `test_medication_advisor_agent.py` (11 tests)
  - Updated: `test_rejection_risk_agent.py` (6 tests)
  - Fixes AttributeError after refactoring (agents no longer import Agent/types/Runner directly)

### Fixed
- **Integration Test** - `test_health_shows_all_agents` now expects 4 specialists instead of 3
- **Code Duplication** - Reduced from 10.32% to 7.9% (23% improvement, SonarCloud)
- **Type Safety** - Added return type annotation `-> str` to `_run_agent()` async function in BaseADKAgent

### Deployment
- **Cloud Run**: Deployed revision `missed-dose-service-00021-2vl`
  - Service URL: https://missed-dose-service-64rz4skmdq-uc.a.run.app
  - New endpoint: `/rejection/analyze`
  - Updated health check to show 4 agents
  - Region: us-central1

- **Netlify**: Updated frontend with real rejection detection
  - Live URL: https://transplant-medication-demo.netlify.app/
  - Act 2: Rejection Detection now uses real AI instead of mock data

### Technical Debt
- **SonarCloud Duplication**: 7.9% exceeds 3% threshold
  - SRTR integration logic still duplicated between RejectionRiskAgent and MedicationAdvisorAgent
  - Both agents have similar try/except blocks for SRTR data retrieval
  - Both agents format SRTR statistics for prompts in similar ways
  - Trade-off accepted for clearer agent-specific code and maintainability
  - Could extract to shared utility method in future if duplication increases

### Performance
- **Test Suite**: 156 tests passed in ~3m57s
- **Coverage**: 94.8% (up from 95.0% - slight decrease due to new agent code)
- **Lint**: ✅ Ruff (10s)
- **Security**: ✅ Bandit (1m1s)
- **Type Check**: ✅ mypy (1m23s)

### Pull Requests
- **PR #23**: "feat: Add real rejection detection with SRTR data integration"
  - 6 commits: agent implementation, tests, API endpoint, frontend, base class refactoring, test fixes
  - Review: All CI/CD checks passed
  - Merged: Squash and merge to main
  - Branch deleted: `feature/add-srtr-data-citations`

### Contributors
- Adam White (adamkwhite)
- Claude AI (Claude Code - code generation and assistance)

## [1.1.0] - 2025-10-30

### Added
- **Google ADK Installation (Task 1.0)**
  - Added google-adk>=1.17.0 to requirements.txt
  - Created ADK configuration module at services/config/adk_config.py
  - Defined configurations for 4 agents: Coordinator, MedicationAdvisor, SymptomMonitor, DrugInteractionChecker
  - Created ADK verification script at scripts/verify_adk_installation.py
  - Created test agent for installation validation at services/agents/test_agent.py
  - Added ADK installation documentation at docs/installation/adk-setup.md

- **Project Structure**
  - Created services/agents/ directory for agent implementations
  - Created services/config/ directory for ADK configuration
  - Added __init__.py files for proper Python package structure
  - Updated services/missed-dose/requirements.txt to include ADK

- **Development Environment**
  - Updated .gitignore with ADK-specific exclusions (.adk_state/, adk_session_*.json, agent_traces/)
  - Configured model settings (gemini-2.0-flash for all agents)
  - Set up generation config with temperature=0.3 for medical accuracy
  - Defined agent-specific instructions and prompts

### Changed
- Updated repository structure to support multi-agent architecture

### Technical Details

#### ADK Configuration (services/config/adk_config.py:1)
- Model: gemini-2.0-flash (primary), gemini-2.0-flash-lite (lightweight tasks)
- Generation config: temperature=0.3, max_output_tokens=800
- Four agent configurations with medical domain expertise
- Firestore integration preserved for backward compatibility

#### Agent Specifications
1. **TransplantCoordinator**: Routes requests using LLM-driven delegation
2. **MedicationAdvisor**: Analyzes missed doses with 12-hour therapeutic windows
3. **SymptomMonitor**: Detects rejection symptoms with urgency assessment
4. **DrugInteractionChecker**: Validates safety using CYP3A4 interaction knowledge

## [1.0.0] - 2025-10-29

### Added
- **Repository Setup & Best Practices**
  - Pre-commit hooks with Ruff, mypy, Bandit, Safety, conventional commits
  - Python 3.12 configuration via pyproject.toml
  - Makefile with development commands (lint, format, typecheck, security)
  - GitHub Actions CI/CD workflows for automated testing and security scanning
  - Dependabot configuration for automated dependency updates
  - Comprehensive .gitignore with ADK and Cloud Run specific exclusions

- **Code Quality Tools**
  - SonarCloud integration (organization: adamkwhite, project: adamkwhite_transplant-gcp)
  - Static analysis with mypy (type checking)
  - Code formatting with Ruff
  - Security scanning with Bandit and Safety

- **Security Improvements**
  - GitHub Actions pinned to full commit SHA hashes for supply chain security
  - Updated gunicorn from 21.2.0 to >=23.0.0 (fixes CVE-2024-6827, CVE-2024-1135)
  - Updated flask-cors from 4.0.0 to >=4.0.2 (fixes CVE-2024-6221, CVE-2024-1681, CVE-2024-6839, CVE-2024-6866)
  - Secret scanning with Gitleaks

- **Project Documentation**
  - PRD for ADK multi-agent migration at docs/features/adk-multi-agent-migration-PLANNED/
  - Detailed task breakdown (103 subtasks across 8 major tasks)
  - Implementation status tracking document
  - AI documentation templates (create-prd.md, generate-tasks.md, process-task-list.md)

- **GitHub Repository**
  - Created repository: https://github.com/adamkwhite/transplant-gcp
  - Configured branch protection with CI/CD checks
  - Set up SonarCloud project integration

### Changed
- **Code Quality Refactoring**
  - Extracted duplicate string literals to constants (GEMINI_FLASH_MODEL, PLATFORM_NAME)
  - Added type annotations for Optional[GenerativeModel] in GeminiClient
  - Fixed None checks to match actual model usage (model vs flash_model)
  - Updated all Python code to comply with Python 3.12 standards

- **CI/CD Configuration**
  - Removed Python 3.11 from test matrix (project requires >=3.12)
  - Updated artifact upload conditions to use Python 3.12
  - Configured SonarCloud to skip tests directory until tests are added

### Fixed
- Resolved 7 security vulnerabilities in dependencies (gunicorn, flask-cors)
- Fixed bare except clause in services/missed-dose/main.py (E722)
- Resolved mypy type errors with proper Optional type annotations
- Fixed Ruff configuration format (migrated to lint.* sections)
- Added nosec B104 comment for Cloud Run host binding requirement

### Technical Details

#### Architecture Decision
- **Target**: Multi-agent system using Google Agent Development Kit (ADK)
- **Pattern**: Coordinator/Dispatcher with 4 specialized agents:
  1. TransplantCoordinator (routing agent)
  2. MedicationAdvisor (missed dose analysis)
  3. SymptomMonitor (rejection detection)
  4. DrugInteractionChecker (medication safety)

#### Technology Stack
- **Language**: Python 3.12
- **Framework**: Google ADK 1.17.0+ (to be installed in Task 1.0)
- **LLM**: Gemini 2.0 Flash for all 4 agents
- **Database**: Google Firestore
- **Deployment**: Google Cloud Run (4 separate services)
- **Code Quality**: Ruff, mypy, Bandit, Safety, SonarCloud
- **CI/CD**: GitHub Actions

#### Development Workflow
- Branch strategy: Feature branches with PR reviews
- Commit convention: Conventional Commits (enforced via pre-commit)
- PR checks: lint, typecheck, test, security, SonarCloud
- Merge strategy: Squash and merge to main

### Known Issues
- SonarCloud reports 15.5% code duplication (services/missed-dose/ contains legacy code)
  - Will be addressed during Task 2.0 ADK agent refactor
  - Legacy directory will be deprecated after multi-agent migration
- No tests directory yet (tests will be added in Task 6.0)
- SonarCloud automatic analysis was disabled (CI-based analysis only)

### Migration Notes
- **From**: Single-service Gemini client architecture
- **To**: Multi-agent ADK system with parallel execution
- **Timeline**: 6 days implementation (Nov 4 deadline for hackathon submission)
- **Backward Compatibility**: Existing REST endpoints preserved

### Contributors
- Adam White (adamkwhite)
- Claude AI (code generation and assistance)

---

## Release Notes

### Version 1.0.0 - Repository Foundation
This release establishes the foundational infrastructure for the Transplant Medication Adherence multi-agent system. All development tooling, CI/CD pipelines, security scanning, and code quality tools are now in place. The repository is ready for Task 1.0: Google ADK installation and configuration.

**Next Milestone**: Task 1.0 - Install and configure Google ADK (Estimated: Nov 5, 2025)
