# Product Requirements Document: ADK Multi-Agent System Migration

## Overview

Refactor the existing single-service Transplant Medication Adherence application into a multi-agent system using Google's Agent Development Kit (ADK) to qualify for the Cloud Run Hackathon "Best of AI Agents" category ($8,000 prize). The migration will transform three existing use cases (missed dose analysis, rejection detection, drug interaction checking) into specialized AI agents orchestrated by a coordinator agent, while maintaining backward compatibility with existing REST APIs and UI.

## Problem Statement

The current implementation uses a monolithic service with a single Gemini client for all medical reasoning tasks. While functional, this architecture:
- Does not qualify for the Cloud Run Hackathon "AI Agents Category" (requires Google ADK + 2+ communicating agents)
- Lacks modularity for specialized medical reasoning tasks
- Cannot leverage ADK's advanced orchestration patterns (parallel execution, agent delegation)
- Misses opportunity for $8,000 "Best of AI Agents" prize + Grand Prize eligibility

The hackathon requires:
- ✅ Built with Google's Agent Development Kit (ADK)
- ✅ Minimum 2 AI agents that communicate
- ✅ Deployed to Cloud Run
- ⏰ Deadline: November 10, 2025

## Goals

### Primary Goals
1. Migrate architecture to Google ADK multi-agent system with 4+ specialized agents
2. Qualify for Cloud Run Hackathon "Best of AI Agents" category
3. Maintain 100% backward compatibility with existing REST API endpoints
4. Deploy all agents to Google Cloud Run as separate services
5. Demonstrate agent-to-agent communication using ADK patterns

### Secondary Goals
6. Maximize hackathon scoring potential (technical implementation, demo quality, innovation)
7. Integrate ADK's built-in development UI for agent testing
8. Enable parallel agent execution for improved performance
9. Create architecture diagram showing multi-agent communication

## Success Criteria

- [ ] 4 ADK agents implemented: Coordinator, Medication Advisor, Symptom Monitor, Drug Interaction Checker
- [ ] All agents deployed to Cloud Run as separate services
- [ ] Agents communicate using ADK's parallel execution pattern
- [ ] Existing `/medications/missed-dose` endpoint works identically (same JSON response)
- [ ] Firestore integration preserved for session/state management
- [ ] ADK development UI accessible for testing
- [ ] Full test suite passes with no regressions
- [ ] Architecture diagram created showing agent hierarchy and communication
- [ ] Project qualifies for AI Agents category (verified against hackathon rules)
- [ ] Deployable demo ready by November 10, 2025

## Requirements

### Functional Requirements

**FR1: Four Specialized AI Agents**
- FR1.1: **Coordinator Agent** - Routes patient requests to appropriate specialist agents using ADK's LLM-driven delegation or parallel execution
- FR1.2: **Medication Advisor Agent** - Handles missed dose analysis using existing Gemini logic
- FR1.3: **Symptom Monitor Agent** - Performs rejection risk assessment based on reported symptoms
- FR1.4: **Drug Interaction Checker Agent** - Analyzes medication interactions using existing Gemini logic

**FR2: Agent Communication Patterns**
- FR2.1: Implement ADK parallel execution pattern for simultaneous agent queries
- FR2.2: Coordinator agent determines which specialist agent(s) to invoke based on request type
- FR2.3: Agents share state via ADK's session state mechanism (`session.state`)
- FR2.4: Support multi-agent responses (e.g., missed dose analysis + drug interaction check in one request)

**FR3: REST API Backward Compatibility**
- FR3.1: Maintain existing endpoint: `POST /medications/missed-dose`
- FR3.2: Preserve current JSON response structure:
```json
{
  "recommendation": "string",
  "reasoning_chain": ["step1", "step2"],
  "risk_level": "low|medium|high|critical",
  "confidence": 0.85,
  "next_steps": ["action1", "action2"],
  "adherence_metrics": {...},
  "infrastructure": {...}
}
```
- FR3.3: Add new endpoints for direct agent access (optional):
  - `POST /agents/medication-advisor`
  - `POST /agents/symptom-monitor`
  - `POST /agents/drug-interaction`

**FR4: Firestore Integration**
- FR4.1: Preserve existing Firestore collections: `patients`, `patient_history`
- FR4.2: Maintain current state management for patient context
- FR4.3: Record agent invocations to Firestore for audit trail

**FR5: ADK Development UI**
- FR5.1: Enable ADK's built-in development UI for agent testing
- FR5.2: Allow testing individual agents via UI
- FR5.3: Display agent communication flow in UI

### Technical Requirements

**TR1: Google ADK Framework**
- TR1.1: Install `google-adk` Python package (version 1.17.0+)
- TR1.2: Use `LlmAgent` class for all 4 agents with Gemini 2.0 Flash model
- TR1.3: Implement using ADK's `ParallelAgent` or `SequentialAgent` workflow patterns
- TR1.4: Follow ADK's agent hierarchy pattern (coordinator with `sub_agents`)

**TR2: Gemini Integration**
- TR2.1: Preserve existing `gemini_client.py` medical prompting logic
- TR2.2: Wrap existing Gemini calls in ADK agent implementations
- TR2.3: Use ADK's native Gemini integration where appropriate
- TR2.4: Maintain temperature=0.3 for medical reasoning accuracy

**TR3: Cloud Run Deployment**
- TR3.1: Deploy each agent as a separate Cloud Run service:
  - `coordinator-service`
  - `medication-advisor-service`
  - `symptom-monitor-service`
  - `drug-interaction-service`
- TR3.2: Configure service-to-service authentication between agents
- TR3.3: Set environment variables: `GEMINI_API_KEY`, `GOOGLE_CLOUD_PROJECT`
- TR3.4: Use containerization (Dockerfile per service)

**TR4: Performance**
- TR4.1: Parallel agent execution should complete in < 5 seconds for multi-agent requests
- TR4.2: Maintain current response times for backward-compatible endpoints
- TR4.3: Cold start time < 3 seconds per Cloud Run service

### Non-Functional Requirements

**NFR1: Reliability**
- NFR1.1: Graceful degradation if individual agents fail (return partial results)
- NFR1.2: Error handling preserves existing error response format
- NFR1.3: Retry logic for Gemini API failures (existing behavior)

**NFR2: Maintainability**
- NFR2.1: Clear agent separation of concerns (one agent = one medical domain)
- NFR2.2: Reusable agent definitions (agents can be composed in different workflows)
- NFR2.3: Comprehensive inline documentation explaining ADK patterns used

**NFR3: Security**
- NFR3.1: GEMINI_API_KEY stored as Cloud Run secret (existing pattern)
- NFR3.2: Service-to-service auth using Google Cloud IAM
- NFR3.3: No PHI logged in agent communication traces

## User Stories

### As a Hackathon Judge
- **US1**: As a hackathon judge, I want to see clear use of Google ADK framework so that I can verify eligibility for "Best of AI Agents" category
- **US2**: As a hackathon judge, I want to observe agent-to-agent communication so that I can assess technical implementation quality
- **US3**: As a hackathon judge, I want to view an architecture diagram so that I can understand the multi-agent system design

### As a Transplant Patient (End User)
- **US4**: As a patient, I want to ask "I missed my 8am dose, it's 2pm now" and receive the same quality guidance as before so that the migration doesn't disrupt my care
- **US5**: As a patient, I want to report symptoms and get rejection risk assessment so that I know when to contact my doctor urgently

### As a Developer (Maintainer)
- **US6**: As a developer, I want to test individual agents using ADK's dev UI so that I can debug medical reasoning logic independently
- **US7**: As a developer, I want to add new medical agents (e.g., lab result analyzer) so that I can extend functionality modularly
- **US8**: As a developer, I want to see which agents were invoked for each request so that I can troubleshoot multi-agent workflows

## Technical Specifications

### Agent Architecture

```python
# Coordinator Agent (Root)
coordinator = LlmAgent(
    name="TransplantCoordinator",
    model="gemini-2.0-flash",
    instruction="""
    You coordinate transplant patient medical queries. Route requests as follows:
    - Medication timing questions → MedicationAdvisor
    - Symptom reports → SymptomMonitor
    - Drug/food interaction questions → DrugInteractionChecker
    - Use ParallelAgent to consult multiple specialists when needed
    """,
    description="Routes transplant patient requests to specialist agents",
    sub_agents=[medication_advisor, symptom_monitor, drug_interaction_checker]
)

# Medication Advisor Agent
medication_advisor = LlmAgent(
    name="MedicationAdvisor",
    model="gemini-2.0-flash",
    instruction="Analyze missed medication doses for transplant patients. Use existing medical reasoning from gemini_client.py",
    description="Handles missed dose analysis and medication scheduling guidance",
    tools=[find_medication_tool, calculate_adherence_tool]
)

# Symptom Monitor Agent
symptom_monitor = LlmAgent(
    name="SymptomMonitor",
    model="gemini-2.0-flash",
    instruction="Assess transplant rejection risk based on reported symptoms. Use existing symptom analysis logic.",
    description="Evaluates symptoms for rejection indicators and urgency",
    tools=[analyze_symptoms_tool, assess_rejection_risk_tool]
)

# Drug Interaction Checker Agent
drug_interaction_checker = LlmAgent(
    name="DrugInteractionChecker",
    model="gemini-2.0-flash",
    instruction="Check for drug-drug and drug-food interactions in transplant medications.",
    description="Analyzes medication interactions and contraindications",
    tools=[check_interactions_tool, query_interaction_db_tool]
)
```

### ADK Workflow Patterns

**Pattern 1: Parallel Consultation (Multi-Agent Request)**
```python
# When patient asks: "I missed my dose and have a fever"
parallel_workflow = ParallelAgent(
    name="MultiSpecialistConsult",
    sub_agents=[medication_advisor, symptom_monitor]
)
# Both agents execute simultaneously, results combined
```

**Pattern 2: Sequential Pipeline (Chained Analysis)**
```python
# When one agent's output feeds another
sequential_workflow = SequentialAgent(
    name="MedicationThenInteraction",
    sub_agents=[medication_advisor, drug_interaction_checker]
)
# MedicationAdvisor runs first, saves to state, then DrugInteractionChecker reads state
```

### REST API Integration Layer

```python
# Flask wrapper preserving existing endpoints
@app.route('/medications/missed-dose', methods=['POST'])
def missed_dose_endpoint():
    """Backward-compatible endpoint using ADK agents"""
    data = request.get_json()

    # Initialize ADK session
    session = Session(state={"patient_id": data.get('patient_id')})
    ctx = InvocationContext(session=session, user_message=format_request(data))

    # Invoke medication advisor agent
    result = await medication_advisor.run_async(ctx)

    # Transform ADK response to legacy format
    return jsonify(transform_to_legacy_format(result))
```

### Firestore State Management

```python
# Preserve existing Firestore integration
def get_patient_context(patient_id):
    """Existing function - integrate with ADK state"""
    doc = db.collection('patients').document(patient_id).get()
    return doc.to_dict()

# ADK session initialization
session = Session(state={
    "patient_context": get_patient_context(patient_id),
    "adherence_history": calculate_adherence(patient_id)
})
```

### Cloud Run Deployment Architecture

```yaml
# services/coordinator/cloudbuild.yaml
services:
  - name: coordinator-service
    image: gcr.io/transplant-prediction/coordinator:latest
    env:
      - GEMINI_API_KEY: ${GEMINI_API_KEY}
      - MEDICATION_ADVISOR_URL: https://medication-advisor-xxx.run.app
      - SYMPTOM_MONITOR_URL: https://symptom-monitor-xxx.run.app
      - DRUG_INTERACTION_URL: https://drug-interaction-xxx.run.app
```

## Dependencies

### External Dependencies
1. **Google ADK**: `google-adk>=1.17.0` (Apache 2.0 license)
2. **Gemini API**: Existing API key, free tier sufficient for hackathon
3. **Google Cloud Run**: Existing project `transplant-prediction`
4. **Firestore**: Existing collections and data
5. **Flask**: Existing REST API framework

### Internal Dependencies
1. **Existing codebase**: `gemini_client.py` medical prompting logic
2. **Medication database**: Hardcoded medication info in `main.py`
3. **Patient context functions**: Firestore query helpers
4. **Docker infrastructure**: Existing Dockerfiles as templates

## Timeline

### Phase 1: ADK Setup & Agent Scaffolding (2 days - Nov 4-5)
- Install `google-adk` and verify compatibility
- Create base agent classes for 4 agents
- Set up ADK development UI for testing
- **Deliverable**: 4 empty ADK agents that can be invoked

### Phase 2: Agent Implementation (3 days - Nov 6-8)
- Migrate MedicationAdvisor logic from existing `gemini_client.py`
- Implement SymptomMonitor agent (existing `analyze_symptoms` logic)
- Implement DrugInteractionChecker agent (existing `check_drug_interactions` logic)
- Build Coordinator agent with routing logic
- **Deliverable**: All 4 agents functional individually

### Phase 3: Multi-Agent Communication (1 day - Nov 8)
- Implement ParallelAgent workflow for simultaneous consultation
- Test agent-to-agent state sharing
- Verify coordinator routing logic
- **Deliverable**: Agents communicate successfully

### Phase 4: Deployment & Integration (1 day - Nov 9)
- Create Dockerfiles for 4 services
- Deploy to Cloud Run with service-to-service auth
- Integrate backward-compatible REST endpoints
- Test production deployment
- **Deliverable**: All services deployed and accessible

### Phase 5: Documentation & Demo (1 day - Nov 10)
- Create architecture diagram
- Record demo video showing agent communication
- Update README with ADK details
- Final testing and submission
- **Deliverable**: Hackathon submission package

**Total Duration**: 6 days (Nov 4-10, 2025)

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| ADK learning curve steeper than expected | High | Medium | Start with simplest agent (MedicationAdvisor) first, use ADK documentation examples |
| Service-to-service auth complexity on Cloud Run | Medium | Medium | Use Cloud Run's built-in IAM authentication, test locally first |
| Backward compatibility breaks existing clients | High | Low | Comprehensive integration tests, keep legacy code path available |
| Cold starts impact demo performance | Medium | High | Pre-warm services before demo, use minimum instances=1 |
| Gemini API rate limits during parallel execution | Medium | Low | Implement exponential backoff, use existing retry logic |
| Time constraint (6 days to deadline) | High | Medium | Focus on core requirements first, cut optional features if needed |

## Out of Scope

The following are explicitly **not** included in this migration:

1. **New medical features**: No new clinical functionality beyond existing 3 use cases
2. **Mobile app**: Marked as stretch goal, not required for hackathon
3. **Frontend UI changes**: Existing web UI preserved as-is, no redesign
4. **Database migration**: Keep Firestore schema unchanged
5. **Authentication/authorization**: No new user auth system
6. **Real-time notifications**: No push notifications or alerts
7. **Lab result analysis**: Future agent, not in scope
8. **Multi-language support**: English only
9. **HIPAA compliance certification**: Demo/hackathon project only
10. **Production scaling optimizations**: Focus on demo functionality

## Acceptance Criteria

### Architecture Validation
- [ ] Architecture includes exactly 4 ADK agents as specified
- [ ] Coordinator agent successfully routes to specialist agents
- [ ] Agents demonstrate parallel execution capability
- [ ] Agent hierarchy visible in ADK dev UI

### Functional Validation
- [ ] `POST /medications/missed-dose` returns same JSON structure as before
- [ ] All 3 use cases work: missed dose, rejection detection, drug interaction
- [ ] Firestore patient context retrieved correctly by agents
- [ ] Error responses match existing format

### Deployment Validation
- [ ] All 4 services deployed to Cloud Run
- [ ] Service-to-service authentication works
- [ ] Health checks pass for all services
- [ ] Environment variables configured correctly

### Hackathon Qualification
- [ ] Uses Google ADK framework (verifiable in code)
- [ ] Minimum 2 agents communicate (we have 4)
- [ ] Deployed to Cloud Run (all services)
- [ ] Demo video shows agent communication
- [ ] Architecture diagram included in README

### Performance Validation
- [ ] Single-agent request completes in < 2 seconds
- [ ] Multi-agent parallel request completes in < 5 seconds
- [ ] No regressions in response time vs. existing system

### Code Quality
- [ ] Full test suite passes (unit + integration)
- [ ] Code coverage remains at 80%+
- [ ] Inline documentation explains ADK patterns
- [ ] No linting errors

## Related Work

- **Hackathon**: [Cloud Run Hackathon - AI Agents Category](https://run.devpost.com/)
- **ADK Documentation**: [Google ADK Docs](https://google.github.io/adk-docs/)
- **GitHub Repository**: https://github.com/google/adk-python
- **Existing Implementation**: `services/missed-dose/main.py`, `services/gemini_client.py`

## Design Decisions (Resolved)

1. **Service discovery**: ✅ **APPROVED** - Use environment variables for Cloud Run service URLs
   - Enables easier local testing and flexible deployment
   - Variables: `MEDICATION_ADVISOR_URL`, `SYMPTOM_MONITOR_URL`, `DRUG_INTERACTION_URL`

2. **State persistence**: ✅ **APPROVED** - Save agent invocations to Firestore
   - New collection: `agent_invocations` with fields: `timestamp`, `agent_name`, `patient_id`, `request`, `response`, `duration_ms`
   - Enables audit trail and debugging of multi-agent workflows

3. **ADK deployment**: ✅ **APPROVED** - Custom Dockerfiles for Cloud Run
   - Each agent gets its own Dockerfile extending Python 3.12 base image
   - ADK's FastAPI server will be containerized per agent

4. **Error aggregation**: ✅ **APPROVED** - Return partial results with error flags
   - Response format: `{"success": true/false, "agents": {"MedicationAdvisor": {...}, "SymptomMonitor": {"error": "..."}}, "partial": true}`
   - Graceful degradation: if 2/3 agents succeed, return their results

5. **Demo focus**: ✅ **APPROVED** - Hybrid approach (architecture + use case)
   - Part 1: Show architecture diagram with agent communication flow (30 seconds)
   - Part 2: Live patient scenario walkthrough (2 minutes)
   - Part 3: ADK dev UI showing multi-agent execution (30 seconds)

---

**Status**: PLANNED
**Created**: 2025-10-28
**Target Completion**: 2025-11-10
**Hackathon Category**: AI Agents (Best of AI Agents - $8,000 prize)
**GitHub Issue**: TBD (to be created after PRD approval)
