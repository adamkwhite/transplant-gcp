# Honeycomb.io Observability Integration - Task List

## Relevant Files

### New Files to Create
- `services/config/tracing.py` - OpenTelemetry tracer configuration with dual-mode export (OTLP + HTTP API)
- `services/utils/pii_filter.py` - PII/PHI filtering utilities for HIPAA compliance
- `services/utils/gemini_tracing.py` - Gemini API call tracing wrapper with token tracking
- `services/utils/tracing_mixin.py` - TracedAgentMixin for adding tracing to ADK agents
- `services/utils/honeycomb_http_exporter.py` - Custom HTTP API exporter (fallback mode)
- `tests/unit/test_tracing_config.py` - Unit tests for tracing configuration
- `tests/unit/test_pii_filter.py` - Unit tests for PII filtering utilities
- `tests/integration/test_honeycomb_tracing.py` - Integration tests for full trace generation
- `docs/installation/honeycomb-setup.md` - Installation and configuration guide
- `docs/features/honeycomb-observability-PLANNED/interview-prep.md` - Interview preparation materials

### Files to Modify
- `services/missed-dose/requirements.txt` - Add OpenTelemetry dependencies
- `services/missed-dose/main.py` - Add Flask auto-instrumentation and tracing initialization
- `services/agents/coordinator_agent.py` - Add TransplantCoordinator tracing instrumentation
- `services/agents/medication_advisor_agent.py` - Add MedicationAdvisor tracing instrumentation
- `services/agents/base_adk_agent.py` - Add TracedAgentMixin inheritance (optional)
- `deploy.sh` - Add environment variables for Honeycomb configuration
- `README.md` - Update with Honeycomb observability section
- `.env.example` - Add Honeycomb environment variables template

### Test Files
- `tests/unit/test_tracing_config.py` - Test OTLP mode, HTTP API mode, disabled mode
- `tests/unit/test_pii_filter.py` - Test patient_id hashing, symptom sanitization, prompt filtering
- `tests/integration/test_honeycomb_tracing.py` - Test full HTTP → Coordinator → Agent → Gemini trace
- `tests/performance/benchmark_tracing_overhead.py` - Benchmark tracing performance overhead

### Notes
- Unit tests should use mocked Honeycomb exporters to avoid real API calls in CI/CD
- Integration tests should verify span hierarchy and attributes, not actual Honeycomb export
- Performance benchmarks should compare request latency with and without tracing enabled
- Use `pytest tests/unit/test_tracing_config.py` to run specific test files

## Tasks

- [ ] 1.0 Set up OpenTelemetry infrastructure and dual-mode configuration
  - [ ] 1.1 Add OpenTelemetry dependencies to `services/missed-dose/requirements.txt` (pinned versions from PRD TR1)
  - [ ] 1.2 Create `services/config/tracing.py` with `init_tracing()` function
  - [ ] 1.3 Implement OTLP exporter mode with Honeycomb endpoint configuration
  - [ ] 1.4 Implement HTTP API exporter mode (create `services/utils/honeycomb_http_exporter.py`)
  - [ ] 1.5 Add feature flag logic for `HONEYCOMB_EXPORTER_MODE` environment variable (otlp, http_api, disabled)
  - [ ] 1.6 Configure resource attributes (service.name, service.version, deployment.environment)
  - [ ] 1.7 Add BatchSpanProcessor for async span export
  - [ ] 1.8 Implement graceful degradation if HONEYCOMB_API_KEY not set (log warning, continue)
  - [ ] 1.9 Test compatibility with google-adk 1.17.0 (verify no version conflicts)
  - [ ] 1.10 Create global tracer instance for import by other modules

- [ ] 2.0 Implement PII/PHI filtering layer for HIPAA compliance
  - [ ] 2.1 Create `services/utils/pii_filter.py` module
  - [ ] 2.2 Implement `hash_patient_id(patient_id: str) -> str` function (SHA256 with salt from env)
  - [ ] 2.3 Add `PII_HASH_SALT` environment variable (default warning if using default salt)
  - [ ] 2.4 Implement `sanitize_symptoms(symptoms: dict) -> dict` function (remove dates, names)
  - [ ] 2.5 Implement `filter_prompt(prompt: str, max_length: int) -> str` for safe LLM prompt previews
  - [ ] 2.6 Add regex patterns to detect and redact PII (SSN, full names, patient IDs)
  - [ ] 2.7 Implement `audit_span_attributes(attributes: dict) -> bool` to verify no PII before export
  - [ ] 2.8 Add logging for PII detection warnings (but don't fail requests)
  - [ ] 2.9 Document PII filtering rules in code comments with examples

- [ ] 3.0 Instrument Flask app and core agents (TransplantCoordinator, MedicationAdvisor)
  - [ ] 3.1 Add `from opentelemetry.instrumentation.flask import FlaskInstrumentor` to `main.py`
  - [ ] 3.2 Call `FlaskInstrumentor().instrument_app(app)` after Flask app creation
  - [ ] 3.3 Add `@app.before_request` hook to extract request-level attributes (patient_id hashed, organ_type)
  - [ ] 3.4 Import tracer in `main.py`: `from services.config.tracing import tracer, init_tracing`
  - [ ] 3.5 Call `init_tracing()` before Flask app starts (verify tracer initialized)
  - [ ] 3.6 Create `services/utils/tracing_mixin.py` with `TracedAgentMixin` class
  - [ ] 3.7 Implement `_traced_execution(operation, request)` method in mixin
  - [ ] 3.8 Implement `_add_request_attributes(span, request)` with PII filtering
  - [ ] 3.9 Implement `_add_result_attributes(span, result)` for safe result tracking
  - [ ] 3.10 Add TracedAgentMixin to TransplantCoordinator (modify `coordinator_agent.py`)
  - [ ] 3.11 Instrument coordinator routing logic (`coordinator.analyze_request` span)
  - [ ] 3.12 Instrument agent invocation tracking (`coordinator.invoke.<agent_name>` spans)
  - [ ] 3.13 Track parallel execution attributes (`coordinator.parallel_execution`, `coordinator.agents_invoked`)
  - [ ] 3.14 Instrument synthesis phase (`coordinator.synthesize` span)
  - [ ] 3.15 Add TracedAgentMixin to MedicationAdvisor (modify `medication_advisor_agent.py`)
  - [ ] 3.16 Instrument dose analysis with medication-specific attributes (hours_late, risk_level)
  - [ ] 3.17 Track recommendation type (take_now, skip, half_dose, contact_doctor)
  - [ ] 3.18 Verify span hierarchy: HTTP request → coordinator → agent (check parent-child relationships)

- [ ] 4.0 Add Gemini API call tracing with token tracking
  - [ ] 4.1 Create `services/utils/gemini_tracing.py` module
  - [ ] 4.2 Implement `traced_gemini_call(model, prompt, **kwargs)` wrapper function
  - [ ] 4.3 Create span with name `gemini.generate` and LLM attributes (vendor, model, prompt_length)
  - [ ] 4.4 Add `filter_prompt()` call to create safe prompt preview (first 200 chars, PII filtered)
  - [ ] 4.5 Measure API latency separately from agent processing (`llm.latency_ms`)
  - [ ] 4.6 Extract token counts from `response.usage_metadata` (prompt_tokens, candidates_tokens, total_tokens)
  - [ ] 4.7 Track response length (`llm.response_length`)
  - [ ] 4.8 Add error handling with span error status and exception recording
  - [ ] 4.9 Integrate `traced_gemini_call()` into MedicationAdvisor agent
  - [ ] 4.10 Integrate `traced_gemini_call()` into TransplantCoordinator agent
  - [ ] 4.11 Verify token counts appear in Honeycomb traces (test with real API call)

- [ ] 5.0 Production hardening (testing, benchmarking, deployment)
  - [ ] 5.1 Create `tests/unit/test_tracing_config.py` for tracing configuration tests
  - [ ] 5.2 Test OTLP mode initialization (mock OTLPSpanExporter)
  - [ ] 5.3 Test HTTP API mode initialization (mock HoneycombHTTPExporter)
  - [ ] 5.4 Test disabled mode (verify no spans exported)
  - [ ] 5.5 Test graceful degradation if HONEYCOMB_API_KEY missing
  - [ ] 5.6 Create `tests/unit/test_pii_filter.py` for PII filtering tests
  - [ ] 5.7 Test `hash_patient_id()` produces consistent hashes
  - [ ] 5.8 Test `sanitize_symptoms()` removes dates and names
  - [ ] 5.9 Test `filter_prompt()` redacts patient IDs and PII
  - [ ] 5.10 Test `audit_span_attributes()` detects PII in span attributes
  - [ ] 5.11 Create `tests/integration/test_honeycomb_tracing.py` for end-to-end trace tests
  - [ ] 5.12 Test full HTTP request generates trace with correct span hierarchy
  - [ ] 5.13 Test coordinator → agent → gemini span relationships
  - [ ] 5.14 Test span attributes contain expected values (agent.name, llm.model, etc.)
  - [ ] 5.15 Create `tests/performance/benchmark_tracing_overhead.py` for performance benchmarks
  - [ ] 5.16 Benchmark request latency with tracing disabled (baseline)
  - [ ] 5.17 Benchmark request latency with tracing enabled (measure overhead)
  - [ ] 5.18 Verify overhead < 50ms at P95 (accept criteria from PRD)
  - [ ] 5.19 Update `.env.example` with Honeycomb environment variables
  - [ ] 5.20 Update `deploy.sh` to set Honeycomb environment variables in Cloud Run
  - [ ] 5.21 Deploy to Cloud Run with `HONEYCOMB_EXPORTER_MODE=otlp`
  - [ ] 5.22 Verify traces appear in Honeycomb UI (check dataset "transplant-agents")
  - [ ] 5.23 Test fallback to HTTP API mode if OTLP fails (manually trigger conflict)
  - [ ] 5.24 Run full test suite with tracing enabled (verify no regressions)
  - [ ] 5.25 Update README.md with Honeycomb observability section

- [ ] 6.0 Create interview preparation materials (dashboard, queries, demo)
  - [ ] 6.1 Create `docs/features/honeycomb-observability-PLANNED/interview-prep.md`
  - [ ] 6.2 Document 7 interview-ready Honeycomb queries from PRD (with talking points)
  - [ ] 6.3 Create Honeycomb dashboard with key visualizations (agent performance, token costs, routing patterns)
  - [ ] 6.4 Generate test traffic to create compelling trace examples (use curl or pytest)
  - [ ] 6.5 Screenshot trace waterfall (HTTP → Coordinator → MedicationAdvisor → Gemini)
  - [ ] 6.6 Screenshot agent performance heatmap (agent.duration_ms by agent.name)
  - [ ] 6.7 Screenshot LLM token cost query (SUM(llm.total_tokens) by agent.name)
  - [ ] 6.8 Screenshot routing patterns (COUNT by coordinator.agents_invoked)
  - [ ] 6.9 Screenshot P95 latency SLO chart (duration_ms < 4000ms target)
  - [ ] 6.10 Write demo script for 5-minute walkthrough (include timing cues)
  - [ ] 6.11 Link each query to Honeycomb Signals team value props (visible product engineering)
  - [ ] 6.12 Create backup plan (screenshots + recorded video if live demo fails)
  - [ ] 6.13 Practice demo run and refine timing (target < 5 minutes)
  - [ ] 6.14 Document extension plan for remaining 3 agents (SymptomMonitor, DrugInteraction, RejectionRisk)
  - [ ] 6.15 Create `docs/installation/honeycomb-setup.md` with setup instructions

---

**Task Breakdown Complete**: All sub-tasks generated. Total: 84 actionable sub-tasks across 6 parent tasks.

**Estimated Effort**: 11-15 hours over 2-3 days (as per PRD timeline)

Would you like to process this task list using `process-task-list.md`? Reply **"yes"** or **"y"** to continue.
