# Google ADK 1.17.0 Multi-Agent Orchestration Research

**Date:** 2025-11-01
**ADK Version:** 1.17.0
**Research Focus:** Multi-agent orchestration capabilities for transplant medication adherence system

## Executive Summary

Google ADK 1.17.0 provides **comprehensive built-in multi-agent orchestration** through:

1. **Workflow Agents** - `SequentialAgent`, `ParallelAgent`, `LoopAgent` for structured execution flow
2. **LLM-Driven Delegation** - `transfer_to_agent()` function for dynamic routing
3. **AgentTool** - Wrapping agents as callable tools with automatic parameter extraction
4. **Shared Session State** - Automatic context/state sharing across agent hierarchy
5. **Agent Hierarchy** - Parent/child relationships with `sub_agents` parameter

**Key Finding:** ADK has built-in orchestration, so we will use **Path A** (ADK's native orchestration API) rather than building a custom layer.

---

## ADK Multi-Agent Primitives

### 1. Agent Hierarchy (Parent-Child Relationships)

ADK uses `sub_agents` parameter to establish agent hierarchies:

```python
from google.adk.agents import LlmAgent

# Define specialist agents
medication_advisor = LlmAgent(
    name="MedicationAdvisor",
    description="Handles missed doses, medication timing questions"
)

symptom_monitor = LlmAgent(
    name="SymptomMonitor",
    description="Handles symptoms, side effects, rejection concerns"
)

# Create coordinator with sub-agents
coordinator = LlmAgent(
    name="TransplantCoordinator",
    model="gemini-2.0-flash",
    description="Routes patient requests to appropriate specialists",
    instruction="Route requests based on specialist descriptions",
    sub_agents=[medication_advisor, symptom_monitor]  # Establishes hierarchy
)

# Framework automatically sets:
# - medication_advisor.parent_agent = coordinator
# - symptom_monitor.parent_agent = coordinator
```

**Key Features:**
- Single parent rule (agent can only have one parent)
- Automatic parent_agent attribute setting
- Navigation via `agent.find_agent(name)` for finding descendants
- Defines scope for workflow agents and LLM delegation

---

### 2. Workflow Agents (Execution Orchestrators)

ADK provides three workflow agents that don't perform tasks but orchestrate sub-agents:

#### 2.1 SequentialAgent

Executes sub-agents one after another in order:

```python
from google.adk.agents import SequentialAgent, LlmAgent

step1 = LlmAgent(name="ValidateInput", output_key="validation_status")
step2 = LlmAgent(name="ProcessData", instruction="Process if {validation_status} is valid")
step3 = LlmAgent(name="ReportResult")

pipeline = SequentialAgent(
    name="DataPipeline",
    sub_agents=[step1, step2, step3]  # Runs in order
)
```

**Use Case for Our System:**
- Multi-step workflows: validate input → analyze → provide recommendations
- State flows through pipeline via shared `InvocationContext`

#### 2.2 ParallelAgent

Executes sub-agents concurrently:

```python
from google.adk.agents import ParallelAgent, LlmAgent

fetch_drug_interactions = LlmAgent(name="DrugChecker", output_key="interactions")
fetch_symptom_analysis = LlmAgent(name="SymptomAnalyzer", output_key="symptoms")

parallel_gatherer = ParallelAgent(
    name="ConcurrentAnalysis",
    sub_agents=[fetch_drug_interactions, fetch_symptom_analysis]
)
```

**Key Features:**
- Modifies `InvocationContext.branch` for each child (e.g., `parent.child_name`)
- All children share same `session.state` (use distinct keys to avoid race conditions)
- Events from sub-agents may be interleaved

**Use Case for Our System:**
- When multiple specialists needed simultaneously
- Parallel safety checks (drug interactions + symptom monitoring)

#### 2.3 LoopAgent

Executes sub-agents sequentially in a loop:

```python
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions
from typing import AsyncGenerator

class CheckCondition(BaseAgent):
    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("status", "pending")
        is_done = (status == "completed")
        yield Event(
            author=self.name,
            actions=EventActions(escalate=is_done)  # Exit loop if done
        )

poller = LoopAgent(
    name="StatusPoller",
    max_iterations=10,
    sub_agents=[process_step, CheckCondition(name="Checker")]
)
```

**Termination:**
- `max_iterations` reached
- Any sub-agent returns event with `escalate=True`

**Use Case for Our System:**
- Iterative refinement of recommendations
- Multi-turn conversations with follow-ups

---

### 3. LLM-Driven Delegation (Agent Transfer)

ADK's `transfer_to_agent()` enables **dynamic LLM-driven routing** without keyword matching:

```python
from google.adk.agents import LlmAgent

billing_agent = LlmAgent(
    name="Billing",
    description="Handles billing inquiries and payment issues"
)

support_agent = LlmAgent(
    name="Support",
    description="Handles technical support and login problems"
)

coordinator = LlmAgent(
    name="HelpDeskCoordinator",
    model="gemini-2.0-flash",
    instruction="Route user requests: Use Billing for payment issues, Support for technical problems",
    sub_agents=[billing_agent, support_agent]
    # AutoFlow handles transfer_to_agent() automatically
)
```

**How It Works:**
1. LLM generates function call: `transfer_to_agent(agent_name='Billing')`
2. AutoFlow (default flow handler) intercepts the call
3. Uses `root_agent.find_agent()` to locate target agent
4. Updates `InvocationContext` to switch execution focus
5. Target agent processes request

**Requirements:**
- Clear `description` on each specialist agent (for LLM to choose)
- Clear `instruction` on coordinator (when to transfer)
- Transfer scope configurable (parent, sub-agents, siblings)

**Advantages for Our System:**
- **No keyword matching** - Pure LLM understanding of natural language
- **Context-aware routing** - LLM considers full conversation context
- **Multi-concern handling** - Can transfer to multiple specialists in sequence
- **Automatic parameter extraction** - LLM extracts parameters from user request

---

### 4. AgentTool (Explicit Invocation)

Wrap an agent as a callable tool for explicit invocation:

```python
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

# Define specialist as standalone agent
medication_advisor = LlmAgent(
    name="MedicationAdvisor",
    description="Analyzes missed medication doses",
    input_schema=MedicationQuery  # Pydantic model for parameters
)

# Wrap as tool
medication_tool = AgentTool(agent=medication_advisor)

# Coordinator uses specialist as tool
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="Use MedicationAdvisor tool for missed dose questions",
    tools=[medication_tool]  # Include as tool
)
```

**How It Works:**
1. `AgentTool` generates function declaration from agent's `input_schema`
2. Parent LLM generates function call with extracted parameters
3. `AgentTool.run_async()` executes the wrapped agent
4. Agent's response returned as tool result
5. State/artifact changes forwarded to parent context

**Advantages:**
- **Structured parameters** - Uses Pydantic schemas for validation
- **Synchronous flow** - Tool execution within parent's control
- **Explicit control** - Parent decides when to invoke
- **Result integration** - Response directly available to parent

**vs. LLM Transfer:**
- **AgentTool**: Explicit, synchronous, structured parameters, tool-like
- **transfer_to_agent**: Dynamic, transfers control, conversational routing

---

### 5. Shared Session State

All agents in the same invocation share `session.state`:

```python
# Agent A writes to state
agent_A.output_key = "capital_city"  # Saves result to state['capital_city']

# Agent B reads from state
agent_B.instruction = "Tell me about {capital_city}"  # Reads state['capital_city']
```

**State Features:**
- **Persistent across agents** - State flows through sequential workflows
- **Temporary state** - `temp:` prefix for turn-specific data
- **Automatic tracking** - State changes tracked via CallbackContext
- **Thread-safe** - Safe for parallel agents (use distinct keys)

**Use Case for Our System:**
- Pass patient context between specialists
- Store intermediate analysis results
- Maintain conversation history
- Track multi-turn follow-ups

---

## Multi-Agent Patterns for Transplant System

### Pattern 1: Coordinator/Dispatcher (Recommended)

**Structure:**
- Central coordinator agent with specialist sub-agents
- LLM-driven delegation for dynamic routing
- Shared session state for context passing

**Implementation:**
```python
from google.adk.agents import LlmAgent

medication_advisor = LlmAgent(
    name="MedicationAdvisor",
    description="Handles missed doses, medication timing, therapeutic windows"
)

symptom_monitor = LlmAgent(
    name="SymptomMonitor",
    description="Handles symptoms, side effects, rejection risk assessment"
)

drug_interaction_checker = LlmAgent(
    name="DrugInteractionChecker",
    description="Handles drug-drug, drug-food, drug-supplement interactions"
)

coordinator = LlmAgent(
    name="TransplantCoordinator",
    model="gemini-2.0-flash",
    instruction="""You are a transplant care coordinator.
    Route patient requests to appropriate specialists:
    - MedicationAdvisor: missed doses, timing questions
    - SymptomMonitor: symptoms, rejection concerns
    - DrugInteractionChecker: drug interactions, new medications

    Use transfer_to_agent() to route requests.""",
    sub_agents=[medication_advisor, symptom_monitor, drug_interaction_checker]
)
```

**Advantages:**
- Pure LLM routing (no keyword matching)
- Multi-turn conversation support via AutoFlow
- Automatic context preservation
- Minimal custom code needed

---

### Pattern 2: Sequential Pipeline (For Multi-Step Workflows)

**Structure:**
- SequentialAgent orchestrates fixed workflow
- Each step builds on previous via shared state

**Implementation:**
```python
from google.adk.agents import SequentialAgent, LlmAgent

validate_input = LlmAgent(
    name="ValidateInput",
    instruction="Validate patient request is clear and safe",
    output_key="validation_status"
)

route_to_specialist = LlmAgent(
    name="Router",
    instruction="Based on {validation_status}, route to appropriate specialist",
    sub_agents=[medication_advisor, symptom_monitor, drug_interaction_checker]
)

synthesize_response = LlmAgent(
    name="Synthesizer",
    instruction="Combine specialist responses into patient-friendly guidance"
)

pipeline = SequentialAgent(
    name="CareWorkflow",
    sub_agents=[validate_input, route_to_specialist, synthesize_response]
)
```

**Use Case:**
- Validate → Route → Synthesize workflow
- Multi-step safety protocols
- Standardized care pathways

---

### Pattern 3: Parallel Fan-Out/Gather (For Complex Cases)

**Structure:**
- ParallelAgent runs multiple specialists concurrently
- Synthesizer gathers results

**Implementation:**
```python
from google.adk.agents import ParallelAgent, SequentialAgent, LlmAgent

# Run multiple specialists in parallel
parallel_analysis = ParallelAgent(
    name="ConcurrentAnalysis",
    sub_agents=[medication_advisor, symptom_monitor, drug_interaction_checker]
)

# Synthesize results
synthesizer = LlmAgent(
    name="Synthesizer",
    instruction="Combine specialist analyses and prioritize by urgency"
)

# Sequential: parallel analysis → synthesis
complex_case_workflow = SequentialAgent(
    name="ComplexCaseAnalysis",
    sub_agents=[parallel_analysis, synthesizer]
)
```

**Use Case:**
- Complex patient cases requiring multiple specialists
- Comprehensive safety assessment
- Reduced latency via parallelization

---

## Implementation Decision: Path A (ADK Native Orchestration)

Based on research, ADK provides all needed orchestration capabilities:

### ✅ What ADK Provides

1. **LLM-Driven Routing** - `transfer_to_agent()` with AutoFlow
2. **Multi-Turn Conversations** - AutoFlow maintains conversation context
3. **Parameter Extraction** - LLM automatically extracts from natural language
4. **Context Management** - Shared session state across agent hierarchy
5. **Workflow Control** - Sequential, Parallel, Loop agents
6. **Event Streaming** - Built-in event system for progress tracking

### ❌ What We Need to Build

1. **Conversation History Manager** - Track multi-turn conversations per patient
2. **Integration Layer** - Connect ADK agents to our existing agent classes
3. **Benchmarking** - Measure token usage and latency
4. **Testing** - Integration tests for routing accuracy

### Implementation Plan

**Approach:** Use ADK's coordinator/dispatcher pattern with LLM-driven delegation

**Architecture:**
```
TransplantCoordinator (LlmAgent)
├── MedicationAdvisor (LlmAgent, sub-agent)
├── SymptomMonitor (LlmAgent, sub-agent)
└── DrugInteractionChecker (LlmAgent, sub-agent)

Routing: LLM-driven via transfer_to_agent()
State: Shared session.state
Conversations: ConversationManager wrapper
```

**Files to Create:**
1. `services/orchestration/adk_orchestrator.py` - Wrapper around ADK coordinator
2. `services/orchestration/conversation_manager.py` - Multi-turn conversation tracking
3. `tests/integration/test_adk_orchestration.py` - Integration tests
4. `scripts/benchmark_adk.py` - Benchmark token usage and latency

---

## Advantages vs. Custom Orchestration

### ADK Native (Path A)

**Pros:**
- ✅ **LLM-driven routing** - No brittle keyword matching
- ✅ **Context-aware** - LLM considers full conversation history
- ✅ **Multi-turn support** - AutoFlow handles follow-ups automatically
- ✅ **Less code** - No custom routing logic needed
- ✅ **Built-in patterns** - Sequential, Parallel, Loop workflows
- ✅ **Production-ready** - Google's maintained orchestration

**Cons:**
- ❌ **Token overhead** - LLM routing adds ~100-200 tokens per request
- ❌ **Latency** - Extra LLM call for routing decision
- ❌ **Less control** - Routing logic in LLM prompts, not code
- ❌ **Debugging** - Harder to trace why LLM chose specific route

### Custom Orchestration (Path B)

**Pros:**
- ✅ **Deterministic** - Exact routing logic in code
- ✅ **Fast** - No LLM overhead for routing
- ✅ **Debuggable** - Clear routing decision trail
- ✅ **Efficient** - Lower token usage

**Cons:**
- ❌ **Brittle** - Keyword matching fragile to input variations
- ❌ **More code** - Custom routing, parameter extraction, context management
- ❌ **Less flexible** - Hard-coded routing rules
- ❌ **Maintenance burden** - Update routing logic as system grows

---

## Decision Matrix

| Criterion | ADK Native | Custom | Winner |
|-----------|------------|--------|--------|
| Routing Accuracy | High (LLM understanding) | Medium (keywords) | ADK |
| Token Usage | Medium (routing overhead) | Low (no overhead) | Custom |
| Latency | Medium (extra LLM call) | Low (direct routing) | Custom |
| Maintainability | High (prompts) | Medium (code) | ADK |
| Flexibility | High (LLM adaptive) | Low (hard-coded) | ADK |
| Multi-turn Support | Native | Custom build | ADK |
| Development Time | Low (built-in) | High (build from scratch) | ADK |
| Production Readiness | High (Google-maintained) | Medium (custom) | ADK |

**Winner: ADK Native Orchestration (Path A)**

---

## Next Steps

1. ✅ Research completed - ADK has comprehensive orchestration
2. ⏭️ Implement ADK orchestrator wrapper
3. ⏭️ Build conversation manager for multi-turn support
4. ⏭️ Create integration tests with real Gemini API
5. ⏭️ Benchmark token usage and latency
6. ⏭️ Document architecture and findings
7. ⏭️ Create PR (do not merge)

---

## References

- [ADK Multi-Agent Systems Documentation](https://google.github.io/adk-docs/agents/multi-agents/)
- [ADK Sequential Agents](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)
- [ADK Parallel Agents](https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/)
- [ADK Loop Agents](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/)
- [Google Cloud Blog: Build Multi-Agentic Systems with ADK](https://cloud.google.com/blog/products/ai-machine-learning/build-multi-agentic-systems-using-google-adk)

---

**Author:** Claude Code
**Review Status:** Draft
**Implementation Status:** Research Complete → Moving to Implementation
