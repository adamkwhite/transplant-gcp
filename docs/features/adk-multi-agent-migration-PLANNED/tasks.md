# ADK Multi-Agent System Migration - Task List

**PRD**: `docs/features/adk-multi-agent-migration-PLANNED/prd.md`
**Status**: PLANNED
**Target Completion**: November 10, 2025

## Relevant Files

### New Files to Create
- `services/agents/coordinator.py` - Coordinator agent with routing logic for specialist agents
- `services/agents/medication_advisor.py` - Medication advisor agent for missed dose analysis
- `services/agents/symptom_monitor.py` - Symptom monitor agent for rejection risk assessment
- `services/agents/drug_interaction.py` - Drug interaction checker agent
- `services/agents/base_tools.py` - Shared ADK tools (FunctionTool wrappers for existing functions)
- `services/agents/adk_session.py` - ADK session management with Firestore integration
- `services/coordinator/main.py` - Flask API wrapper for coordinator agent (backward compatibility)
- `services/coordinator/Dockerfile` - Container for coordinator service
- `services/coordinator/requirements.txt` - Python dependencies including google-adk
- `services/medication-advisor/main.py` - Standalone medication advisor service
- `services/medication-advisor/Dockerfile` - Container for medication advisor service
- `services/symptom-monitor/main.py` - Standalone symptom monitor service
- `services/symptom-monitor/Dockerfile` - Container for symptom monitor service
- `services/drug-interaction/main.py` - Standalone drug interaction service
- `services/drug-interaction/Dockerfile` - Container for drug interaction service
- `deploy-agents.sh` - Deployment script for all 4 agent services
- `docs/architecture-diagram.png` - Multi-agent system architecture diagram

### Files to Modify
- `services/gemini_client.py` - Extract reusable prompting logic for ADK agents
- `services/missed-dose/main.py` - Add backward-compatible endpoint routing to coordinator
- `README.md` - Update with ADK architecture details and deployment instructions

### Test Files
- `tests/agents/test_coordinator.py` - Unit tests for coordinator agent
- `tests/agents/test_medication_advisor.py` - Unit tests for medication advisor agent
- `tests/agents/test_symptom_monitor.py` - Unit tests for symptom monitor agent
- `tests/agents/test_drug_interaction.py` - Unit tests for drug interaction agent
- `tests/integration/test_multi_agent.py` - Integration tests for agent communication
- `tests/integration/test_backward_compatibility.py` - Tests for legacy endpoint compatibility

### Notes
- All agent files use Python 3.12 and follow existing project structure
- Tests use pytest framework (existing project standard)
- ADK version: `google-adk>=1.17.0`
- Run tests: `pytest tests/` or `pytest tests/agents/test_coordinator.py` for specific tests

## Tasks

- [ ] 0.0 Repository Setup with Best Practices
  - [ ] 0.1 Configure pre-commit hooks
    - [ ] 0.1.1 Copy `.pre-commit-config.yaml` from project_template (Ruff, mypy, bandit, safety, conventional commits)
    - [ ] 0.1.2 Update Python version to `3.12` in pre-commit config
    - [ ] 0.1.3 Install pre-commit: `pip install pre-commit && pre-commit install`
    - [ ] 0.1.4 Run initial pre-commit check: `pre-commit run --all-files` and fix any issues
  - [ ] 0.2 Set up pyproject.toml configuration
    - [ ] 0.2.1 Copy `pyproject.toml` from project_template
    - [ ] 0.2.2 Update project metadata: name="transplant-medication-adherence", version="1.0.0", authors
    - [ ] 0.2.3 Configure Ruff settings: line-length=100, target-version="py312"
    - [ ] 0.2.4 Configure pytest settings: testpaths=["tests"], coverage source=["services"]
    - [ ] 0.2.5 Configure mypy settings for type checking
    - [ ] 0.2.6 Configure Bandit security scanning exclusions
  - [ ] 0.3 Create Makefile for common tasks
    - [ ] 0.3.1 Copy `Makefile` from project_template
    - [ ] 0.3.2 Update targets to match project structure (src/ → services/)
    - [ ] 0.3.3 Add make targets: `install`, `install-dev`, `test`, `lint`, `format`, `typecheck`, `security`, `clean`
    - [ ] 0.3.4 Test all Makefile targets work correctly
  - [ ] 0.4 Set up GitHub Actions CI/CD workflows
    - [ ] 0.4.1 Create `.github/workflows/` directory
    - [ ] 0.4.2 Copy `ci.yml` from project_template (lint, typecheck, test on Python 3.11 & 3.12)
    - [ ] 0.4.3 Update ci.yml paths: `src/` → `services/` for coverage and mypy
    - [ ] 0.4.4 Copy `security.yml` from project_template (Bandit, Safety, Gitleaks)
    - [ ] 0.4.5 Copy `dependabot.yml` from project_template for automated dependency updates
    - [ ] 0.4.6 Test workflows by creating a test branch and pushing
  - [ ] 0.5 Update .gitignore
    - [ ] 0.5.1 Copy comprehensive `.gitignore` from project_template
    - [ ] 0.5.2 Add ADK-specific ignores: `.adk_cache/`, `agent_logs/`
    - [ ] 0.5.3 Ensure `.env` is ignored (already should be, but verify)
    - [ ] 0.5.4 Add Cloud Run specific ignores: `*.log`, `gcr-credentials.json`
  - [ ] 0.6 Create requirements files structure
    - [ ] 0.6.1 Create `requirements-dev.txt` with: pytest, pytest-cov, pytest-html, ruff, mypy, pre-commit, bandit, safety
    - [ ] 0.6.2 Update main `requirements.txt` to include google-adk (will be done in task 1.3)
    - [ ] 0.6.3 Create `requirements-test.txt` if needed for test-only dependencies
  - [ ] 0.7 Configure SonarQube (if applicable)
    - [ ] 0.7.1 Check if project_template has SonarQube configuration (sonar-project.properties)
    - [ ] 0.7.2 If exists, copy and adapt for this project
    - [ ] 0.7.3 Configure code coverage report paths for SonarQube
    - [ ] 0.7.4 Add SonarQube GitHub Action to ci.yml if configured
  - [ ] 0.8 Verify repository setup
    - [ ] 0.8.1 Run `make lint` and ensure it passes
    - [ ] 0.8.2 Run `make format` and commit any formatting changes
    - [ ] 0.8.3 Run `make test` (will have minimal tests at this stage)
    - [ ] 0.8.4 Run `make security` and address any high-severity findings
    - [ ] 0.8.5 Commit all repository setup files with message: "chore: add repository best practices from project_template"

- [ ] 1.0 Set Up ADK Framework and Dependencies
  - [ ] 1.1 Install `google-adk>=1.17.0` in virtual environment and verify installation
  - [ ] 1.2 Create `services/agents/` directory structure for agent implementations
  - [ ] 1.3 Create base `requirements.txt` with ADK dependencies: `google-adk`, `google-generativeai`, `flask`, `google-cloud-firestore`
  - [ ] 1.4 Test ADK installation by running simple LlmAgent example from documentation
  - [ ] 1.5 Configure ADK development UI and verify it launches successfully

- [ ] 2.0 Implement Core Agent Classes
  - [ ] 2.1 Create `services/agents/base_tools.py` with ADK FunctionTool wrappers for existing functions (`find_medication`, `get_patient_context`, `calculate_adherence`, `record_interaction`)
  - [ ] 2.2 Implement `services/agents/medication_advisor.py` with LlmAgent for missed dose analysis
    - [ ] 2.2.1 Extract medical prompting logic from `gemini_client.py:analyze_missed_dose()`
    - [ ] 2.2.2 Configure agent with `name="MedicationAdvisor"`, `model="gemini-2.0-flash"`, instruction for missed dose guidance
    - [ ] 2.2.3 Add tools: `find_medication_tool`, `calculate_adherence_tool`
    - [ ] 2.2.4 Set `output_key="medication_recommendation"` for state sharing
  - [ ] 2.3 Implement `services/agents/symptom_monitor.py` with LlmAgent for rejection risk assessment
    - [ ] 2.3.1 Extract symptom analysis logic from `gemini_client.py:analyze_symptoms()`
    - [ ] 2.3.2 Configure agent with instruction for rejection risk evaluation
    - [ ] 2.3.3 Add tools: `analyze_symptoms_tool`, `assess_rejection_risk_tool`
    - [ ] 2.3.4 Set `output_key="symptom_assessment"`
  - [ ] 2.4 Implement `services/agents/drug_interaction.py` with LlmAgent for interaction checking
    - [ ] 2.4.1 Extract interaction checking logic from `gemini_client.py:check_drug_interactions()`
    - [ ] 2.4.2 Configure agent with instruction for drug/food interaction analysis
    - [ ] 2.4.3 Add tools: `check_interactions_tool`, `query_interaction_db_tool`
    - [ ] 2.4.4 Set `output_key="interaction_results"`
  - [ ] 2.5 Implement `services/agents/coordinator.py` with LlmAgent as parent coordinator
    - [ ] 2.5.1 Define coordinator instruction for routing: "medication timing → MedicationAdvisor, symptoms → SymptomMonitor, interactions → DrugInteractionChecker"
    - [ ] 2.5.2 Configure `sub_agents=[medication_advisor, symptom_monitor, drug_interaction_checker]`
    - [ ] 2.5.3 Set up ParallelAgent for multi-specialist consultation when needed

- [ ] 3.0 Build Multi-Agent Communication Layer
  - [ ] 3.1 Create `services/agents/adk_session.py` for ADK Session integration with Firestore
    - [ ] 3.1.1 Implement `create_adk_session(patient_id)` that loads patient context from Firestore into ADK session state
    - [ ] 3.1.2 Implement `save_agent_invocation(agent_name, request, response, duration_ms)` to new Firestore collection `agent_invocations`
    - [ ] 3.1.3 Create helper `format_request_for_agent(request_data)` to convert REST API requests to ADK InvocationContext
  - [ ] 3.2 Implement ParallelAgent workflow for simultaneous agent consultation
    - [ ] 3.2.1 Create `parallel_consult = ParallelAgent(name="MultiSpecialistConsult", sub_agents=[...])`
    - [ ] 3.2.2 Test parallel execution with mock patient request requiring 2+ agents
  - [ ] 3.3 Implement error handling and partial result aggregation
    - [ ] 3.3.1 Wrap agent invocations in try-except blocks
    - [ ] 3.3.2 Create `aggregate_agent_results(results_dict)` function to combine successful responses
    - [ ] 3.3.3 Add error flags to response: `{"success": bool, "agents": {...}, "partial": bool}`

- [ ] 4.0 Integrate ADK Agents into Existing REST API
  - [ ] 4.1 Update `services/missed-dose/main.py` to use ADK coordinator agent
    - [ ] 4.1.1 Import TransplantCoordinator from `services/agents/coordinator_agent.py`
    - [ ] 4.1.2 Initialize coordinator agent with GEMINI_API_KEY on app startup
    - [ ] 4.1.3 Replace `gemini.analyze_missed_dose()` call with `coordinator.route_request()`
    - [ ] 4.1.4 Transform user request into coordinator-compatible format
    - [ ] 4.1.5 Extract relevant fields from ADK response to maintain existing JSON structure
  - [ ] 4.2 Update health check endpoint
    - [ ] 4.2.1 Add agent status to `/health` response (coordinator + 3 specialists)
    - [ ] 4.2.2 Show ADK version and agent model information
  - [ ] 4.3 Test backward compatibility
    - [ ] 4.3.1 Verify existing `/medications/missed-dose` request/response format unchanged
    - [ ] 4.3.2 Test with sample requests from original API documentation
    - [ ] 4.3.3 Verify Firestore integration still works (patient context, history recording)

- [ ] 5.0 Deploy Agents to Google Cloud Run
  - [ ] 5.1 Create Dockerfiles for each agent service
    - [ ] 5.1.1 Create `services/coordinator/Dockerfile` based on python:3.12-slim
    - [ ] 5.1.2 Create `services/medication-advisor/Dockerfile`
    - [ ] 5.1.3 Create `services/symptom-monitor/Dockerfile`
    - [ ] 5.1.4 Create `services/drug-interaction/Dockerfile`
    - [ ] 5.1.5 Ensure all Dockerfiles install google-adk and copy agent code
  - [ ] 5.2 Create requirements.txt for each service
    - [ ] 5.2.1 `services/coordinator/requirements.txt` with ADK, Flask, Firestore, genai
    - [ ] 5.2.2 Copy and customize requirements.txt for other 3 services
  - [ ] 5.3 Create `deploy-agents.sh` deployment script
    - [ ] 5.3.1 Build and push Docker images to GCR: `gcr.io/transplant-prediction/{service}:latest`
    - [ ] 5.3.2 Deploy coordinator-service to Cloud Run (us-central1)
    - [ ] 5.3.3 Deploy medication-advisor-service to Cloud Run
    - [ ] 5.3.4 Deploy symptom-monitor-service to Cloud Run
    - [ ] 5.3.5 Deploy drug-interaction-service to Cloud Run
  - [ ] 5.4 Configure service-to-service authentication
    - [ ] 5.4.1 Enable Cloud Run IAM invoker role for coordinator → specialist services
    - [ ] 5.4.2 Set environment variables on coordinator: `MEDICATION_ADVISOR_URL`, `SYMPTOM_MONITOR_URL`, `DRUG_INTERACTION_URL`
  - [ ] 5.5 Configure environment variables for all services
    - [ ] 5.5.1 Set `GEMINI_API_KEY` secret on all 4 services
    - [ ] 5.5.2 Set `GOOGLE_CLOUD_PROJECT=transplant-prediction` on all services
    - [ ] 5.5.3 Verify all services start and pass health checks

- [ ] 6.0 Testing and Validation
  - [ ] 6.1 Write unit tests for individual agents
    - [ ] 6.1.1 Create `tests/agents/test_coordinator.py` testing routing logic with mock sub-agents
    - [ ] 6.1.2 Create `tests/agents/test_medication_advisor.py` testing missed dose scenarios
    - [ ] 6.1.3 Create `tests/agents/test_symptom_monitor.py` testing rejection risk assessment
    - [ ] 6.1.4 Create `tests/agents/test_drug_interaction.py` testing interaction detection
  - [ ] 6.2 Write integration tests for multi-agent communication
    - [ ] 6.2.1 Create `tests/integration/test_multi_agent.py` testing parallel agent execution
    - [ ] 6.2.2 Test coordinator routing: medication question → MedicationAdvisor only
    - [ ] 6.2.3 Test parallel consultation: "missed dose + fever" → MedicationAdvisor + SymptomMonitor
    - [ ] 6.2.4 Test error handling: one agent fails, partial results returned
  - [ ] 6.3 Write backward compatibility tests
    - [ ] 6.3.1 Create `tests/integration/test_backward_compatibility.py`
    - [ ] 6.3.2 Test `POST /medications/missed-dose` returns exact same JSON structure as before
    - [ ] 6.3.3 Test all existing request/response scenarios from original implementation
    - [ ] 6.3.4 Verify Firestore `patients` and `patient_history` collections still work
  - [ ] 6.4 Run full test suite and verify coverage
    - [ ] 6.4.1 Run `pytest tests/` and ensure all tests pass
    - [ ] 6.4.2 Check code coverage: `pytest --cov=services/agents --cov-report=html`
    - [ ] 6.4.3 Ensure coverage ≥ 80% (per PRD requirements)
  - [ ] 6.5 Manual testing on deployed services
    - [ ] 6.5.1 Test coordinator service health check via Cloud Run URL
    - [ ] 6.5.2 Send test request: missed dose analysis (single agent)
    - [ ] 6.5.3 Send test request: missed dose + symptoms (parallel agents)
    - [ ] 6.5.4 Verify Firestore `agent_invocations` collection records are created
    - [ ] 6.5.5 Test ADK development UI (if accessible on Cloud Run)

- [ ] 7.0 Documentation and Demo Preparation
  - [ ] 7.1 Create architecture diagram
    - [ ] 7.1.1 Draw multi-agent system diagram showing: Coordinator → 3 specialist agents
    - [ ] 7.1.2 Show ADK patterns used: ParallelAgent, sub_agents hierarchy, state sharing
    - [ ] 7.1.3 Indicate Cloud Run services and communication paths
    - [ ] 7.1.4 Save as `docs/architecture-diagram.png` and embed in README
  - [ ] 7.2 Update README.md
    - [ ] 7.2.1 Add "Multi-Agent Architecture" section describing 4 ADK agents
    - [ ] 7.2.2 Update deployment instructions to reference `deploy-agents.sh`
    - [ ] 7.2.3 Add architecture diagram image
    - [ ] 7.2.4 Update "Hackathon Category" section to explicitly state ADK usage
    - [ ] 7.2.5 Add example curl commands for new agent endpoints
  - [ ] 7.3 Prepare demo video content (3 minutes)
    - [ ] 7.3.1 Script Part 1: Architecture overview (30 sec) - show diagram, explain agent roles
    - [ ] 7.3.2 Script Part 2: Live demo (2 min) - patient scenario "I missed my 8am tacrolimus dose, it's 2pm, and I have a fever"
    - [ ] 7.3.3 Script Part 3: ADK dev UI (30 sec) - show agent communication in UI, state sharing
    - [ ] 7.3.4 Record screen capture of live demo hitting Cloud Run endpoints
  - [ ] 7.4 Verify hackathon submission requirements
    - [ ] 7.4.1 Confirm ADK usage is evident in code (imports, LlmAgent classes)
    - [ ] 7.4.2 Confirm 4 agents communicate (visible in logs/UI)
    - [ ] 7.4.3 Confirm all services deployed to Cloud Run (provide URLs)
    - [ ] 7.4.4 Prepare public GitHub repository link
    - [ ] 7.4.5 Finalize demo video (upload to YouTube/Vimeo)
  - [ ] 7.5 Create status.md tracking file
    - [ ] 7.5.1 Document implementation status and completion percentage
    - [ ] 7.5.2 List any known issues or future enhancements
    - [ ] 7.5.3 Add PR link when created
