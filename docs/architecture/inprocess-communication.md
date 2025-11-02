# In-Process Multi-Agent Communication Architecture

## Overview

This document describes the synchronous in-process multi-agent communication implementation for the Transplant Patient Care system. This approach routes patient requests through a coordinator agent that intelligently delegates to specialist agents and synthesizes their responses.

**Status:** ✅ Implemented (Task 3.0)
**Branch:** `feature/task-3.0-inprocess`
**Last Updated:** 2025-11-01

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        Patient Request                            │
│           "I missed my tacrolimus at 8am, now I have fever"      │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                  TransplantCoordinatorAgent                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Routing Analysis (LLM-based)                          │   │
│  │    - Parse request using Gemini 2.0 Flash               │   │
│  │    - Extract JSON routing decision                       │   │
│  │    - Identify agents needed                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 2. Parameter Extraction                                  │   │
│  │    - ParameterExtractor uses LLM                        │   │
│  │    - Extract: medications, times, symptoms, vitals      │   │
│  │    - Format parameters for each specialist              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                     │
│              ┌──────────────┴──────────────┐                     │
│              ▼                              ▼                     │
│  ┌───────────────────────┐    ┌───────────────────────┐         │
│  │ 3a. Sequential Mode    │ OR │ 3b. Parallel Mode     │         │
│  │   (single thread)      │    │   (asyncio.gather)    │         │
│  └───────────────────────┘    └───────────────────────┘         │
└────────────────┬──────────────────────────┬────────────────────-─┘
                 │                          │
      ┌──────────┴──────────┬───────────────┴───────────┬────────────┐
      ▼                     ▼                           ▼            │
┌──────────────┐  ┌──────────────────┐  ┌─────────────────────────┐│
│ Medication   │  │  Symptom         │  │ Drug Interaction        ││
│ Advisor      │  │  Monitor         │  │ Checker                 ││
│ Agent        │  │  Agent           │  │ Agent                   ││
└──────┬───────┘  └────────┬─────────┘  └───────────┬─────────────┘│
       │                   │                         │              │
       │ analyze_missed_   │ analyze_symptoms()      │ check_       │
       │ dose()            │                         │ interaction()│
       │                   │                         │              │
       └───────────────────┴─────────────────────────┴──────────────┘
                                     │
                                     ▼
       ┌─────────────────────────────────────────────────────────────┐
       │              4. Response Synthesis (LLM-based)              │
       │  - Aggregate specialist recommendations                     │
       │  - Create coherent, patient-friendly advice                 │
       │  - Prioritize safety, provide action steps                  │
       └─────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                   Synthesized Response                      │
       │  {                                                          │
       │    "agents_consulted": ["MedicationAdvisor", "Symptom..."], │
       │    "recommendations": "Based on your situation...",         │
       │    "confidence": 0.87,                                      │
       │    "specialist_responses": {...}                            │
       │  }                                                          │
       └─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. TransplantCoordinatorAgent

**File:** `services/agents/coordinator_agent.py`

Primary orchestration agent that manages the multi-agent workflow.

**Key Methods:**

- `route_request(request, patient_id, patient_context, parallel=True)`
  - Main entry point for routing
  - Supports both parallel and sequential specialist consultation

- `_analyze_routing(request)`
  - Uses LLM to determine which specialists to consult
  - Returns JSON with agents_needed, reasoning, request_type

- `_consult_specialists(routing_decision, request, patient_id, patient_context)`
  - Sequential consultation mode
  - Calls specialist agents synchronously

- `_consult_specialists_async(routing_decision, request, patient_id, patient_context)`
  - Parallel consultation mode using asyncio
  - Uses `asyncio.gather()` for concurrent execution
  - Wraps synchronous agent.run() in `asyncio.to_thread()`

- `_synthesize_response(request, routing_decision, specialist_responses)`
  - Aggregates specialist recommendations using LLM
  - Creates coherent, patient-friendly advice
  - Calculates overall confidence score

### 2. ParameterExtractor

**File:** `services/agents/parameter_extractor.py`

Extracts structured parameters from natural language using LLM.

**Capabilities:**

- Medication names (tacrolimus, mycophenolate, prednisone, etc.)
- Time extraction (scheduled time, current time, time late)
- Symptom extraction (fever, nausea, decreased urine, etc.)
- Vital signs (temperature, weight, blood pressure)

**Key Methods:**

- `extract_parameters(request, extraction_type="all")`
  - General-purpose extraction with JSON response

- `extract_for_medication_advisor(request)`
  - Format: {medication, scheduled_time, current_time}

- `extract_for_symptom_monitor(request)`
  - Format: {symptoms: [], vital_signs: {}}

- `extract_for_drug_interaction(request)`
  - Format: {medications: []}

**Design:**

- Uses Gemini 2.0 Flash (fast model) with low temperature (0.1)
- Returns JSON with confidence scores
- Fallback to keyword-based extraction on errors

### 3. Specialist Agents

**Files:**
- `services/agents/medication_advisor_agent.py`
- `services/agents/symptom_monitor_agent.py`
- `services/agents/drug_interaction_agent.py`

Each specialist has a specific domain:

**MedicationAdvisor:**
- Method: `analyze_missed_dose(medication, scheduled_time, current_time, ...)`
- Handles: Late/missed doses, timing questions, adherence

**SymptomMonitor:**
- Method: `analyze_symptoms(symptoms, vital_signs, ...)`
- Handles: Rejection symptoms, urgency assessment

**DrugInteractionChecker:**
- Method: `check_interaction(medications, foods, supplements, ...)`
- Handles: Drug-drug, drug-food, drug-supplement interactions

## Code Examples

### Basic Usage

```python
from services.agents.coordinator_agent import TransplantCoordinatorAgent
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent
from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

# Initialize coordinator with specialists
coordinator = TransplantCoordinatorAgent(
    api_key=GEMINI_API_KEY,
    medication_advisor=MedicationAdvisorAgent(api_key=GEMINI_API_KEY),
    symptom_monitor=SymptomMonitorAgent(api_key=GEMINI_API_KEY),
    drug_interaction_checker=DrugInteractionCheckerAgent(api_key=GEMINI_API_KEY),
)

# Route a patient request
request = "I missed my tacrolimus at 8am, it's now 2pm"
result = coordinator.route_request(request)

print(f"Agents consulted: {result['agents_consulted']}")
print(f"Recommendations: {result['recommendations']}")
print(f"Confidence: {result['confidence']}")
```

### Sequential vs Parallel Consultation

```python
# Sequential consultation (default for single agent)
result_seq = coordinator.route_request(
    "I missed my dose",
    parallel=False
)

# Parallel consultation (faster for multiple agents)
result_par = coordinator.route_request(
    "I missed my dose and have a fever",
    parallel=True  # Uses asyncio.gather()
)
```

### Parameter Extraction Example

```python
from services.agents.parameter_extractor import ParameterExtractor

extractor = ParameterExtractor(api_key=GEMINI_API_KEY)

request = "I forgot my tacrolimus at 8:00 AM, it's now 2:30 PM"
params = extractor.extract_for_medication_advisor(request)

# Output:
# {
#   "medication": "tacrolimus",
#   "scheduled_time": "8:00 AM",
#   "current_time": "2:30 PM",
#   "confidence": 0.85
# }
```

## Benchmark Results

**Test Configuration:**
- 10 sample requests (single and multi-agent scenarios)
- Real Gemini API calls
- Parallel mode enabled for multi-agent requests

**Latency Statistics:**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P50    | < 5.0s | TBD    | TBD    |
| Mean   | -      | TBD    | -      |
| P95    | -      | TBD    | -      |

**Category Breakdown:**

| Category | Count | Mean Latency | Notes |
|----------|-------|--------------|-------|
| single_agent_medication | 3 | TBD | MedicationAdvisor only |
| single_agent_symptom | 3 | TBD | SymptomMonitor only |
| single_agent_interaction | 2 | TBD | DrugInteractionChecker only |
| multi_agent_2 | 1 | TBD | Two specialists (parallel) |
| multi_agent_3 | 1 | TBD | Three specialists (parallel) |

**Benchmark Command:**
```bash
python scripts/benchmark_inprocess.py
```

**Results Location:** `benchmarks/inprocess_results.json`

## Integration Tests

**File:** `tests/integration/test_inprocess_communication.py`

**Test Coverage:**

1. **Single Specialist Routing** (3 tests)
   - Route to MedicationAdvisor
   - Route to SymptomMonitor
   - Route to DrugInteractionChecker

2. **Multi-Specialist Routing** (2 tests)
   - Route to multiple specialists
   - Verify parallel is faster than sequential

3. **Parameter Extraction** (2 tests)
   - Medication parameter extraction accuracy
   - Symptom parameter extraction accuracy

4. **Response Synthesis** (3 tests)
   - Synthesis coherence
   - Single agent synthesis
   - Confidence scoring

5. **Error Handling** (2 tests)
   - Missing specialist agents
   - Parameter extraction fallback

6. **End-to-End Scenarios** (3 tests)
   - Missed dose simple
   - Fever and missed dose
   - Drug interaction question

**Run Tests:**
```bash
# With API key set
export GEMINI_API_KEY="your-key"
pytest tests/integration/test_inprocess_communication.py -v -m integration

# Without API key (tests will be skipped)
pytest tests/integration/test_inprocess_communication.py -v -m integration
```

## Pros and Cons

### ✅ Pros

1. **Simple Architecture**
   - All agents in same process
   - No network overhead
   - Easy to debug and trace

2. **Fast for Single Agent**
   - Direct function calls
   - No serialization/deserialization
   - Minimal overhead

3. **Shared Memory**
   - Can share patient context efficiently
   - No data duplication
   - Easy state management

4. **Easy Development**
   - Standard Python debugging
   - No distributed systems complexity
   - Simple error handling

5. **Asyncio Optimization**
   - Parallel consultation for multiple agents
   - Good CPU utilization
   - Still simple to reason about

### ❌ Cons

1. **Scalability Limits**
   - Single process bottleneck
   - Can't distribute load across machines
   - Limited by single machine resources

2. **No Independent Scaling**
   - Can't scale individual specialists
   - All agents must run together
   - Resource contention possible

3. **Failure Coupling**
   - One agent crash affects all
   - No fault isolation
   - Single point of failure

4. **Latency for Multiple Agents**
   - Even with asyncio, still sequential API calls
   - Limited by API rate limits
   - Can't truly parallelize LLM calls (I/O bound)

5. **Deployment Complexity**
   - Must deploy all agents together
   - Can't update specialists independently
   - Harder to A/B test individual agents

## Performance Characteristics

**Time Complexity:**

- Single agent: O(1) routing + O(1) extraction + O(1) specialist call = **O(1)**
- Multiple agents (sequential): O(1) routing + O(n) specialist calls = **O(n)**
- Multiple agents (parallel): O(1) routing + O(1) parallel calls = **O(1)** *with asyncio*

**Space Complexity:**

- O(1) per request (no message queues, no persistence)

**Expected Latency:**

- Routing analysis: ~0.5-1.0s (Gemini 2.0 Flash)
- Parameter extraction: ~0.3-0.5s (Gemini 2.0 Flash)
- Specialist consultation: ~1.0-2.0s each (Gemini models)
- Response synthesis: ~0.5-1.0s (coordinator LLM)

**Total Expected:**
- Single agent: ~2.5-4.5s
- Multi-agent (2): ~3.5-6.0s (with parallel)
- Multi-agent (3): ~4.0-7.0s (with parallel)

## Comparison with Other Approaches

| Aspect | In-Process | Message Queue | HTTP APIs |
|--------|-----------|---------------|-----------|
| Latency (single) | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Better |
| Latency (multi) | ⭐⭐⭐ Good | ⭐⭐ Fair | ⭐⭐⭐⭐ Better |
| Scalability | ⭐⭐ Fair | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Better |
| Complexity | ⭐⭐⭐⭐⭐ Simple | ⭐⭐ Complex | ⭐⭐⭐ Medium |
| Fault Tolerance | ⭐⭐ Fair | ⭐⭐⭐⭐ Better | ⭐⭐⭐⭐⭐ Best |
| Development | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐ Harder | ⭐⭐⭐ Medium |

## Future Improvements

1. **Caching Layer**
   - Cache routing decisions for similar requests
   - Cache parameter extractions
   - Cache specialist responses (with TTL)

2. **Streaming Responses**
   - Stream LLM responses as they generate
   - Progressive UI updates
   - Better perceived performance

3. **Smart Batching**
   - Batch similar requests to specialists
   - Reduce API calls
   - Better throughput

4. **Response Validation**
   - Validate specialist outputs before synthesis
   - Catch hallucinations early
   - Improve reliability

5. **Metrics and Monitoring**
   - Track latency per specialist
   - Monitor extraction accuracy
   - Alert on degraded performance

## References

- [Google ADK Documentation](https://ai.google.dev/adk)
- [Gemini API Reference](https://ai.google.dev/gemini-api)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Task 2.0: Core Agent Implementation](#) (previous task)
- [Task 4.0: Message Queue Communication](#) (alternative implementation)
- [Task 5.0: HTTP API Communication](#) (alternative implementation)

## Lines of Code

**Implementation:**
- `coordinator_agent.py`: ~650 lines
- `parameter_extractor.py`: ~270 lines
- Total: ~920 lines

**Tests:**
- `test_inprocess_communication.py`: ~400 lines

**Benchmarks:**
- `benchmark_inprocess.py`: ~300 lines

**Documentation:**
- `inprocess-communication.md`: This file

**Grand Total: ~1,620 lines**
