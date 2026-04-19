# PRD: Honeycomb.io Observability Integration

## Overview

Add production-grade observability to the transplant-gcp multi-agent AI system using Honeycomb.io. This integration serves dual purposes: (1) demonstrating "visible product engineering" for the Honeycomb Signals team interview, and (2) providing robust production monitoring for the live Cloud Run service.

The implementation will instrument the multi-agent AI system with OpenTelemetry distributed tracing, enabling visibility into agent coordination, LLM performance, and system behavior while maintaining HIPAA compliance through PII/PHI filtering.

## Problem Statement

**Current State:**
- The transplant-gcp system has 5 specialized ADK agents orchestrating medical guidance
- No distributed tracing or observability beyond basic Cloud Run logs
- Cannot answer questions like: "Which agent is slow?", "What's the token cost per request?", "How often does agent coordination require multiple specialists?"
- Limited visibility into Gemini API performance and failures
- No SLO tracking for the critical medical guidance use case

**Impact:**
- Cannot demonstrate production observability practices in Honeycomb interview
- Difficult to diagnose performance bottlenecks or agent coordination issues
- No data-driven optimization for agent selection and routing logic
- Missing opportunity to showcase "visible product engineering" principles

**Desired Outcome:**
- Complete distributed tracing from HTTP request → Coordinator → Specialist Agents → Gemini API
- Interview-ready visualizations demonstrating multi-agent observability
- Production-safe monitoring with PII/PHI filtering for patient data
- SLO definitions and tracking for medical guidance reliability

## Goals

### Primary Goals
1. **Interview Demonstration**: Create compelling Honeycomb visualizations and talking points for Signals team interview
2. **Production Observability**: Implement production-grade distributed tracing for the live Cloud Run service
3. **Agent Performance Visibility**: Track individual agent latency, success rates, and coordination patterns
4. **LLM Cost Tracking**: Monitor Gemini API usage, token costs, and performance per agent

### Secondary Goals
1. Maintain HIPAA compliance through PII/PHI filtering
2. Minimize performance overhead (< 50ms per request)
3. Support graceful degradation if Honeycomb unavailable
4. Create foundation for instrumenting remaining 3 agents (SymptomMonitor, DrugInteraction, RejectionRisk)

## Success Criteria

### Interview Success Criteria
- [ ] Can demonstrate trace waterfall showing `HTTP Request → TransplantCoordinator → MedicationAdvisor → Gemini API` chain
- [ ] Can show SLO dashboard with P95 latency < 4000ms target
- [ ] Can demonstrate agent-specific queries (e.g., `P95(agent.duration_ms) GROUP BY agent.name`)
- [ ] Can show LLM token cost tracking per agent (`SUM(llm.total_tokens) GROUP BY agent.name`)
- [ ] Can demonstrate PII filtering (patient IDs are hashed, symptoms sanitized in traces)
- [ ] Have 5+ compelling Honeycomb queries documented for interview discussion
- [ ] Screenshot library of key visualizations prepared

### Production Success Criteria
- [ ] All HTTP requests generate distributed traces in Honeycomb
- [ ] TransplantCoordinator and MedicationAdvisor agents emit structured spans with relevant attributes
- [ ] Gemini API calls tracked with latency, token counts, prompt/response metadata, and error rates
- [ ] Patient data properly sanitized (no PII/PHI in Honeycomb - verified through audit)
- [ ] Feature flag allows switching between OTLP and HTTP API export modes
- [ ] Tracing overhead < 50ms per request (measured via benchmarks)
- [ ] SLO defined for P95 response time with 4000ms target (99.5% over 30 days)
- [ ] Graceful degradation if Honeycomb unreachable (no request failures, logged warnings)
- [ ] Full test suite passes with tracing enabled (no regression in functionality)

## Requirements

### Functional Requirements

**FR1: Dual-Mode Tracing Infrastructure**
- Support both OpenTelemetry OTLP exporter and Honeycomb HTTP API
- Feature flag controlled via `HONEYCOMB_EXPORTER_MODE` environment variable
- Modes: `otlp` (default), `http_api`, `disabled`
- Automatic fallback to HTTP API if OTLP initialization fails

**FR2: Flask HTTP Request Instrumentation**
- Auto-instrument Flask app using `opentelemetry-instrumentation-flask`
- Capture HTTP method, path, status code, duration
- Extract request-level attributes: patient_id (hashed), organ_type, request_type
- Add custom request ID tracking (`X-Request-ID` header)

**FR3: Base Agent Tracing Infrastructure**
- Create base tracing mixin/decorator for ADK agents
- Automatic span creation for agent execution (`agent.<agent_name>`)
- Track agent.name, agent.type, request.type attributes
- Record execution duration as `agent.duration_ms`
- Capture exceptions with stack traces and error status

**FR4: TransplantCoordinator Instrumentation**
- Trace routing analysis phase (`coordinator.analyze_request`)
- Track which agents are invoked (`coordinator.agents_invoked`)
- Measure parallel vs sequential execution (`coordinator.parallel_execution`)
- Trace individual agent invocations (`coordinator.invoke.<agent_name>`)
- Track synthesis phase (`coordinator.synthesize`)

**FR5: MedicationAdvisor Instrumentation**
- Track medication name, scheduled_time, hours_late
- Record recommendation type (take_now, skip, half_dose, contact_doctor)
- Capture risk_level, confidence, urgency attributes
- Track patient context (transplant_type, months_post_transplant - no patient_id raw)

**FR6: Gemini API Call Tracing**
- Wrap all Gemini API calls with tracing (`gemini.generate`)
- Track model name, prompt length, response length
- Record token counts (prompt_tokens, response_tokens, total_tokens)
- Measure API latency separately from agent processing
- Capture API errors with error type and message
- Include prompt preview (first 200 chars) and response preview (production-safe)

**FR7: PII/PHI Filtering Layer**
- Hash patient_id before adding to span attributes (SHA256 with salt)
- Redact medication names containing patient identifiers
- Sanitize symptom descriptions (remove specific dates, names, locations)
- Filter prompt/response previews to remove PII
- Audit utility to verify no PII in exported spans

**FR8: SLO Definitions and Queries**
- Define P95 latency SLO: < 4000ms (99.5% over 30 days)
- Define error rate SLO: < 1% (99% success rate)
- Define Gemini API success SLO: > 99%
- Create BurnAlert: 2% budget consumed in 1 hour
- Document 10+ interview-ready queries

**FR9: Environment Configuration**
- `HONEYCOMB_API_KEY`: Honeycomb API key (required)
- `HONEYCOMB_EXPORTER_MODE`: `otlp` | `http_api` | `disabled` (default: `otlp`)
- `HONEYCOMB_DATASET`: Dataset name (default: `transplant-agents`)
- `ENVIRONMENT`: `development` | `staging` | `production`
- `SERVICE_VERSION`: Semantic version (e.g., `1.1.0`)
- `TRACING_SAMPLE_RATE`: Sampling rate 0.0-1.0 (default: 1.0)

**FR10: Interview Preparation Materials**
- Dashboard with 5+ key visualizations
- Query library with explanations
- Screenshot library of compelling traces
- Talking points document linking visualizations to Honeycomb value props
- Demo script for walking through multi-agent coordination

### Technical Requirements

**TR1: OpenTelemetry Dependencies**
```txt
# OpenTelemetry core
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0
opentelemetry-exporter-otlp-proto-http==1.27.0

# Auto-instrumentation
opentelemetry-instrumentation-flask==0.48b0
opentelemetry-instrumentation-requests==0.48b0
```
- Pin versions to avoid google-adk 1.17.0 conflicts
- Test compatibility with Python 3.12 and Flask 2.x

**TR2: Tracing Configuration Architecture**
- Create `services/config/tracing.py` module
- Implement `init_tracing(service_name, mode)` function
- Return global tracer instance for import
- Support service.name, service.version, deployment.environment resource attributes

**TR3: PII Filtering Utilities**
- Create `services/utils/pii_filter.py` module
- `hash_patient_id(patient_id: str) -> str`: SHA256 hash with env-based salt
- `sanitize_symptoms(symptoms: dict) -> dict`: Remove PII from symptom descriptions
- `filter_prompt(prompt: str) -> str`: Redact PII from LLM prompts (keep first 200 chars safe)
- `audit_span(span) -> bool`: Verify span has no PII before export

**TR4: Gemini Tracing Wrapper**
- Create `services/utils/gemini_tracing.py` module
- `traced_gemini_call(prompt, model, **kwargs)` decorator/wrapper
- Automatically extract token counts from response.usage_metadata
- Handle API errors gracefully with span error status

**TR5: Cloud Run Deployment Configuration**
```bash
gcloud run services update missed-dose-service \
  --set-env-vars HONEYCOMB_API_KEY=<key> \
  --set-env-vars HONEYCOMB_EXPORTER_MODE=otlp \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars SERVICE_VERSION=1.1.0 \
  --region=us-central1
```

**TR6: Testing Requirements**
- Unit tests for tracing configuration (OTLP mode, HTTP API mode, disabled mode)
- Unit tests for PII filtering (patient_id hashing, symptom sanitization)
- Integration tests for full trace generation (HTTP → Coordinator → Agent → Gemini)
- Performance benchmarks measuring tracing overhead (< 50ms target)
- Mock Honeycomb exporter for CI/CD (no real API calls)

### Non-Functional Requirements

**NFR1: Performance**
- Tracing overhead < 50ms per request (measured at P95)
- Use BatchSpanProcessor for async export (non-blocking)
- Sampling support for high-traffic scenarios (configurable via `TRACING_SAMPLE_RATE`)

**NFR2: HIPAA Compliance**
- No PII/PHI in Honeycomb traces (patient_id hashed, symptoms sanitized)
- Code review checklist for HIPAA compliance before production
- Audit utility to verify compliance before enabling in production

**NFR3: Reliability**
- Graceful degradation if Honeycomb API unavailable (log error, continue processing)
- No request failures due to tracing infrastructure
- Circuit breaker pattern if needed (future enhancement)

**NFR4: Maintainability**
- Clear separation of concerns (tracing config, PII filtering, Gemini wrapper)
- Comprehensive inline documentation
- Example code snippets for adding tracing to new agents
- Migration guide for extending to remaining 3 agents

**NFR5: Interview Readiness**
- Screenshot library updated within 24 hours of implementation
- Demo script rehearsed and timing validated (< 5 minutes)
- Talking points document linked to Honeycomb Signals team focus areas
- Backup plan if live demo fails (screenshots, recorded video)

## User Stories

### As an Interview Candidate
- I want to demonstrate distributed tracing in a multi-agent AI system so that I can showcase my observability expertise to the Honeycomb Signals team
- I want to show agent-specific performance metrics so that I can discuss how Honeycomb enables data-driven optimization
- I want to prove I understand SLOs so that I can discuss reliability engineering with the Signals team
- I want to demonstrate PII filtering so that I can show I understand production security requirements

### As a Production Engineer
- I want to see which agents are slow so that I can optimize the critical path
- I want to track Gemini API costs per agent so that I can budget LLM usage
- I want to monitor error rates by agent so that I can identify reliability issues
- I want to set up SLOs on response time so that I can track service reliability

### As a Healthcare Compliance Officer
- I want to ensure no patient PII appears in observability traces so that the system remains HIPAA compliant
- I want to audit tracing data before production so that I can verify compliance
- I want configurable filtering so that I can adjust PII policies as regulations evolve

## Technical Specifications

### Tracing Configuration (services/config/tracing.py)

```python
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import logging

logger = logging.getLogger(__name__)

def init_tracing(service_name: str = "transplant-agents", mode: str = None):
    """
    Initialize OpenTelemetry tracing with Honeycomb exporter.

    Args:
        service_name: Service identifier (default: "transplant-agents")
        mode: Export mode - "otlp", "http_api", or "disabled" (default: from env)

    Returns:
        Tracer instance
    """
    # Determine export mode
    mode = mode or os.environ.get("HONEYCOMB_EXPORTER_MODE", "otlp")

    if mode == "disabled":
        logger.info("Tracing disabled via HONEYCOMB_EXPORTER_MODE=disabled")
        return trace.get_tracer(service_name)

    # Create resource with service metadata
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.environ.get("SERVICE_VERSION", "1.0.0"),
        "deployment.environment": os.environ.get("ENVIRONMENT", "development"),
    })

    provider = TracerProvider(resource=resource)

    # Configure exporter based on mode
    honeycomb_api_key = os.environ.get("HONEYCOMB_API_KEY")
    if not honeycomb_api_key:
        logger.warning("HONEYCOMB_API_KEY not set - tracing disabled")
        trace.set_tracer_provider(provider)
        return trace.get_tracer(service_name)

    try:
        if mode == "otlp":
            exporter = OTLPSpanExporter(
                endpoint="https://api.honeycomb.io/v1/traces",
                headers={
                    "x-honeycomb-team": honeycomb_api_key,
                    "x-honeycomb-dataset": os.environ.get("HONEYCOMB_DATASET", "transplant-agents"),
                }
            )
            logger.info("Initialized OTLP exporter for Honeycomb")
        elif mode == "http_api":
            from services.utils.honeycomb_http_exporter import HoneycombHTTPExporter
            exporter = HoneycombHTTPExporter(
                api_key=honeycomb_api_key,
                dataset=os.environ.get("HONEYCOMB_DATASET", "transplant-agents")
            )
            logger.info("Initialized HTTP API exporter for Honeycomb")
        else:
            logger.error(f"Unknown HONEYCOMB_EXPORTER_MODE: {mode}")
            trace.set_tracer_provider(provider)
            return trace.get_tracer(service_name)

        # Use BatchSpanProcessor for async export
        provider.add_span_processor(BatchSpanProcessor(exporter))

    except Exception as e:
        logger.error(f"Failed to initialize Honeycomb exporter: {e}")
        # Continue without exporter (graceful degradation)

    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

# Global tracer instance
tracer = init_tracing()
```

### PII Filtering (services/utils/pii_filter.py)

```python
import hashlib
import os
import re
from typing import Any, Dict

PII_SALT = os.environ.get("PII_HASH_SALT", "default-salt-change-in-prod")

def hash_patient_id(patient_id: str) -> str:
    """
    Hash patient ID for HIPAA compliance.

    Args:
        patient_id: Raw patient identifier

    Returns:
        SHA256 hash of patient_id with salt
    """
    combined = f"{patient_id}{PII_SALT}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]

def sanitize_symptoms(symptoms: dict) -> dict:
    """
    Remove PII from symptom descriptions.

    Args:
        symptoms: Raw symptom dict

    Returns:
        Sanitized symptom dict safe for tracing
    """
    sanitized = {}

    for key, value in symptoms.items():
        if isinstance(value, str):
            # Remove dates (YYYY-MM-DD, MM/DD/YYYY)
            value = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', '[DATE]', value)
            value = re.sub(r'\b\d{2}/\d{2}/\d{4}\b', '[DATE]', value)

            # Remove potential names (capitalized words in quotes)
            value = re.sub(r'"[A-Z][a-z]+ [A-Z][a-z]+"', '[NAME]', value)

        sanitized[key] = value

    return sanitized

def filter_prompt(prompt: str, max_length: int = 200) -> str:
    """
    Create safe preview of LLM prompt for tracing.

    Args:
        prompt: Full LLM prompt
        max_length: Maximum characters to include

    Returns:
        Sanitized prompt preview
    """
    # Take first max_length characters
    preview = prompt[:max_length]

    # Remove potential patient IDs (format: test_patient, patient_123)
    preview = re.sub(r'\bpatient_\w+\b', '[PATIENT_ID]', preview, flags=re.IGNORECASE)
    preview = re.sub(r'\b[A-Z]{2,}\d{4,}\b', '[ID]', preview)

    if len(prompt) > max_length:
        preview += "..."

    return preview

def audit_span_attributes(attributes: Dict[str, Any]) -> bool:
    """
    Audit span attributes for PII before export.

    Args:
        attributes: Span attributes dict

    Returns:
        True if safe, False if PII detected
    """
    unsafe_patterns = [
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Full names
        r'\bpatient_id\b',  # Raw patient_id key
    ]

    for key, value in attributes.items():
        if isinstance(value, str):
            for pattern in unsafe_patterns:
                if re.search(pattern, value):
                    return False

    return True
```

### Gemini Tracing Wrapper (services/utils/gemini_tracing.py)

```python
from opentelemetry import trace
from config.tracing import tracer
from utils.pii_filter import filter_prompt
import time
import logging

logger = logging.getLogger(__name__)

def traced_gemini_call(model, prompt: str, **kwargs):
    """
    Wrap Gemini API calls with detailed tracing.

    Args:
        model: Gemini model instance
        prompt: LLM prompt
        **kwargs: Additional model.generate_content arguments

    Returns:
        Gemini API response
    """
    with tracer.start_as_current_span(
        "gemini.generate",
        attributes={
            "llm.vendor": "google",
            "llm.model": kwargs.get("model_name", "gemini-2.0-flash-exp"),
            "llm.prompt_length": len(prompt),
            "llm.prompt_preview": filter_prompt(prompt, max_length=200),
        }
    ) as span:
        start_time = time.time()

        try:
            # Make Gemini API call
            response = model.generate_content(prompt, **kwargs)

            # Record response metrics
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("llm.latency_ms", latency_ms)

            # Extract response metadata
            if hasattr(response, 'text'):
                span.set_attribute("llm.response_length", len(response.text))

            # Token tracking (if available)
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                span.set_attribute("llm.prompt_tokens", usage.prompt_token_count)
                span.set_attribute("llm.candidates_tokens", usage.candidates_token_count)
                span.set_attribute("llm.total_tokens", usage.total_token_count)

            span.set_status(trace.Status(trace.StatusCode.OK))
            return response

        except Exception as e:
            span.set_attribute("llm.error", str(e))
            span.set_attribute("llm.error_type", type(e).__name__)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)
            logger.error(f"Gemini API error: {e}")
            raise
```

### Base Agent Tracing Mixin

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from config.tracing import tracer
from utils.pii_filter import hash_patient_id
import time

class TracedAgentMixin:
    """
    Mixin to add tracing to ADK agents.

    Usage:
        class MedicationAdvisorAgent(BaseADKAgent, TracedAgentMixin):
            def analyze_missed_dose(self, **kwargs):
                return self._traced_execution("analyze_missed_dose", kwargs)
    """

    def _traced_execution(self, operation: str, request: dict):
        """
        Execute agent operation with tracing.

        Args:
            operation: Operation name (e.g., "analyze_missed_dose")
            request: Request parameters dict

        Returns:
            Agent response
        """
        agent_name = self.__class__.__name__

        with tracer.start_as_current_span(
            f"agent.{agent_name}",
            attributes={
                "agent.name": agent_name,
                "agent.operation": operation,
            }
        ) as span:
            start_time = time.time()

            try:
                # Add request attributes (with PII filtering)
                self._add_request_attributes(span, request)

                # Execute actual agent logic
                result = self._execute_operation(operation, request)

                # Add result attributes
                self._add_result_attributes(span, result)

                span.set_status(Status(StatusCode.OK))
                return result

            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

            finally:
                duration_ms = (time.time() - start_time) * 1000
                span.set_attribute("agent.duration_ms", duration_ms)

    def _add_request_attributes(self, span, request: dict):
        """Add safe request attributes to span."""
        if "patient_id" in request:
            span.set_attribute("patient.id_hash", hash_patient_id(request["patient_id"]))

        safe_fields = ["medication", "organ_type", "transplant_type", "hours_late"]
        for field in safe_fields:
            if field in request:
                span.set_attribute(f"request.{field}", request[field])

    def _add_result_attributes(self, span, result: dict):
        """Add safe result attributes to span."""
        safe_fields = ["risk_level", "confidence", "urgency", "recommendation_type"]
        for field in safe_fields:
            if field in result:
                span.set_attribute(f"result.{field}", result[field])

    def _execute_operation(self, operation: str, request: dict):
        """Override in subclass to execute actual agent logic."""
        raise NotImplementedError
```

### Interview-Ready Honeycomb Queries

**Query 1: Agent Performance Comparison**
```
HEATMAP(agent.duration_ms)
GROUP BY agent.name
WHERE agent.name EXISTS
```
**Talking Point**: "This shows which agents are slow. We can see MedicationAdvisor is consistently faster than RejectionRisk because it doesn't need to query SRTR data."

**Query 2: LLM Token Cost by Agent**
```
SUM(llm.total_tokens)
GROUP BY agent.name
WHERE llm.total_tokens EXISTS
```
**Talking Point**: "This tracks LLM costs per agent. We can optimize prompts for high-volume agents to reduce token usage."

**Query 3: Multi-Agent Coordination Patterns**
```
COUNT
GROUP BY coordinator.agents_invoked
WHERE coordinator.agents_invoked EXISTS
```
**Talking Point**: "This shows routing patterns. 65% of requests need only one agent, but 23% trigger multi-agent consultations."

**Query 4: Error Rate by Agent**
```
COUNT
WHERE error = true
GROUP BY agent.name
```
**Talking Point**: "This tracks reliability per agent. We can see if one agent has higher failure rates and needs attention."

**Query 5: P95 Latency Trend**
```
P95(duration_ms)
GROUP BY TIME(1h)
WHERE http.route = "/medications/missed-dose"
```
**Talking Point**: "This is our SLO metric - we target P95 < 4000ms for medical guidance reliability."

**Query 6: Gemini API Performance**
```
P95(llm.latency_ms)
GROUP BY llm.model
WHERE llm.vendor = "google"
```
**Talking Point**: "This isolates Gemini API latency from our agent processing. We can see cold starts and API degradation."

**Query 7: Request Volume by Organ Type**
```
COUNT
GROUP BY request.organ_type
WHERE request.organ_type EXISTS
```
**Talking Point**: "This shows usage patterns. Kidney transplant patients are our primary users, which makes sense given kidney is the most common transplant."

## Dependencies

### External Dependencies
- **Honeycomb Account**: Free trial or paid account with API key
- **OpenTelemetry Packages**: Listed in TR1 (api, sdk, exporter, instrumentation)
- **Python 3.12**: Runtime environment (already in use)
- **Cloud Run**: Deployment platform with environment variable support

### Internal Dependencies
- **services/agents/base_adk_agent.py**: Base agent class to add tracing mixin
- **services/agents/coordinator_agent.py**: TransplantCoordinator for routing instrumentation
- **services/agents/medication_advisor_agent.py**: MedicationAdvisor for specialist instrumentation
- **services/missed-dose/main.py**: Flask app for HTTP instrumentation
- **Existing google-adk 1.17.0**: Must test OTel version compatibility

### Deployment Dependencies
- **HONEYCOMB_API_KEY**: Environment variable in Cloud Run
- **Cloud Run Service Update**: Deploy with new environment variables
- **Firestore**: No changes required (already in use)

## Timeline

### Phase 1: Foundation (3-4 hours)
**Objectives**: Set up tracing infrastructure and verify basic functionality
- [ ] Install OpenTelemetry packages (test for google-adk conflicts)
- [ ] Create `services/config/tracing.py` with dual-mode support
- [ ] Add Flask auto-instrumentation to `main.py`
- [ ] Configure environment variables in Cloud Run
- [ ] Deploy and verify basic HTTP request traces in Honeycomb
- [ ] Test OTLP mode, HTTP API mode, and disabled mode

### Phase 2: Core Agent Instrumentation (4-5 hours)
**Objectives**: Instrument TransplantCoordinator and MedicationAdvisor agents
- [ ] Create `TracedAgentMixin` in `services/utils/tracing_mixin.py`
- [ ] Instrument TransplantCoordinator routing logic
- [ ] Instrument MedicationAdvisor dose analysis
- [ ] Create Gemini tracing wrapper
- [ ] Test full trace waterfall (HTTP → Coordinator → Agent → Gemini)
- [ ] Verify span attributes and timing accuracy

### Phase 3: Production Hardening (2-3 hours)
**Objectives**: Add PII filtering, error handling, and performance validation
- [ ] Create `services/utils/pii_filter.py` with hash and sanitize functions
- [ ] Add PII filtering to agent request/result attributes
- [ ] Implement graceful degradation for Honeycomb unavailability
- [ ] Performance benchmarking (measure overhead < 50ms)
- [ ] Write unit tests for tracing config and PII filtering
- [ ] Update integration tests to verify tracing

### Phase 4: Interview Preparation (2-3 hours)
**Objectives**: Create visualizations, queries, and demo materials
- [ ] Create Honeycomb dashboard with 7 key queries
- [ ] Generate load to produce compelling trace examples
- [ ] Screenshot library (5+ visualizations)
- [ ] Document talking points linking to Honeycomb value props
- [ ] Write demo script (< 5 minute walkthrough)
- [ ] Practice demo and refine flow
- [ ] Create extension plan for remaining 3 agents

**Total Estimated Time**: 11-15 hours (can be done over 2-3 days)

## Risks and Mitigation

### Risk 1: OpenTelemetry Version Conflicts with google-adk
**Severity**: High
**Likelihood**: Medium
**Impact**: Cannot use OTLP exporter, must fall back to HTTP API

**Mitigation Strategy**:
- Dual-mode implementation with feature flag (`HONEYCOMB_EXPORTER_MODE`)
- Pin specific OTel versions known to work with google-adk 1.17.0
- Test on local development first before Cloud Run deployment
- If OTLP fails, immediately switch to HTTP API mode (no blocking)
- Document workaround in `docs/installation/honeycomb-setup.md`

### Risk 2: PII/PHI Exposure in Traces
**Severity**: Critical (HIPAA violation)
**Likelihood**: Low (with proper filtering)
**Impact**: Regulatory fines, loss of trust, interview failure

**Mitigation Strategy**:
- Implement filtering layer before any span export
- Hash all patient_id fields (never send raw IDs)
- Sanitize symptom descriptions (remove dates, names)
- Code review checklist for HIPAA compliance
- Audit utility to scan exported spans before production
- Test with production-like data to verify no leaks

### Risk 3: Performance Overhead Degrading User Experience
**Severity**: Medium
**Likelihood**: Low
**Impact**: Slower response times, poor user experience

**Mitigation Strategy**:
- Target < 50ms overhead (measure at P95)
- Use BatchSpanProcessor for async export (non-blocking)
- Feature flag to disable tracing if needed (`HONEYCOMB_EXPORTER_MODE=disabled`)
- Sampling support for high-traffic scenarios (future)
- Benchmark before and after tracing implementation

### Risk 4: Honeycomb Unavailability Causing Request Failures
**Severity**: Medium
**Likelihood**: Low
**Impact**: User requests fail due to tracing infrastructure

**Mitigation Strategy**:
- Async span export (non-blocking)
- Try/except around exporter initialization (graceful degradation)
- Log errors but never fail requests
- Circuit breaker pattern if needed (future enhancement)
- Monitor for exporter errors in Cloud Run logs

### Risk 5: Insufficient Interview-Ready Examples
**Severity**: Low
**Likelihood**: Low (with proper planning)
**Impact**: Unable to demonstrate value in interview

**Mitigation Strategy**:
- Create checklist of 7+ compelling queries
- Screenshot preparation as acceptance criteria
- Practice demo run before interview (< 5 minutes)
- Backup plan: screenshots + recorded video if live demo fails
- Link each visualization to Honeycomb Signals team focus areas

## Out of Scope

The following are explicitly excluded from this PRD:

### Not Included in MVP
- **Remaining 3 Agents**: SymptomMonitor, DrugInteraction, RejectionRisk instrumentation (extension plan documented)
- **Custom Metrics**: Only distributed tracing, no custom metrics/gauges (Honeycomb focuses on traces)
- **Log Correlation**: No structured logging integration with trace IDs (future enhancement)
- **Alerting**: No automated alerts based on SLOs (Honeycomb BurnAlerts are manual setup)
- **Cost Dashboards**: No real-time cost tracking for Gemini API (manual query required)

### Deferred to Future Phases
- **Sampling Logic**: Always trace 100% of requests in MVP (add sampling later for scale)
- **Circuit Breaker**: Graceful degradation only, no circuit breaker pattern (future)
- **Multi-Region Tracing**: Single region only (us-central1), no cross-region correlation
- **User Journey Tracking**: No patient session tracking across multiple requests
- **ML Model Performance**: No tracking of recommendation accuracy vs ground truth

### Permanently Out of Scope
- **Replacing Cloud Run Logging**: Honeycomb complements logs, doesn't replace them
- **Real-Time Alerting**: Not a monitoring/alerting platform (use Cloud Monitoring for alerts)
- **Data Warehousing**: Honeycomb is for exploration, not long-term storage
- **FHIR Integration**: No EHR system integration (out of scope for transplant-gcp)

## Acceptance Criteria

### Functional Acceptance Criteria
- [ ] OTLP exporter successfully sends traces to Honeycomb in `otlp` mode
- [ ] HTTP API exporter successfully sends traces to Honeycomb in `http_api` mode
- [ ] Disabled mode prevents any trace export
- [ ] All HTTP requests to `/medications/missed-dose` generate parent spans
- [ ] TransplantCoordinator routing generates child spans with agent invocation tracking
- [ ] MedicationAdvisor analysis generates child spans with dose guidance attributes
- [ ] Gemini API calls generate child spans with token counts and latency
- [ ] Patient IDs are hashed in all span attributes (verified via audit)
- [ ] Symptom descriptions are sanitized (no dates, names in traces)
- [ ] SLO query returns P95 latency with 4000ms comparison

### Interview Acceptance Criteria
- [ ] Can demonstrate full trace waterfall in Honeycomb UI (< 10 seconds to load)
- [ ] Can execute 7+ compelling queries with results
- [ ] Can show agent performance comparison (heatmap by agent.name)
- [ ] Can show LLM token cost tracking (sum by agent.name)
- [ ] Can demonstrate PII filtering (patient_id_hash attribute exists, patient_id does not)
- [ ] Can walk through demo script in < 5 minutes
- [ ] Have backup screenshots if live demo fails

### Production Acceptance Criteria
- [ ] Full test suite passes with tracing enabled (no regression)
- [ ] Performance benchmarks show < 50ms overhead at P95
- [ ] Tracing overhead < 10% of total request time
- [ ] Graceful degradation tested (simulate Honeycomb API failure, requests succeed)
- [ ] No PII in Honeycomb verified via audit utility
- [ ] Cloud Run deployment successful with environment variables
- [ ] SLO defined and queryable in Honeycomb (P95 < 4000ms)
- [ ] Error rates < 1% with tracing enabled (same as without)

### Code Quality Acceptance Criteria
- [ ] Unit tests for tracing configuration (3 modes)
- [ ] Unit tests for PII filtering (hash, sanitize, audit)
- [ ] Integration tests for full trace generation
- [ ] Code review by senior engineer (HIPAA compliance checklist)
- [ ] Documentation updated (README, installation guide, interview prep doc)
- [ ] Pre-commit hooks pass (Ruff, mypy, bandit)
- [ ] SonarCloud quality gate passes

## Related Work

*This section will be updated after GitHub issues are created.*

- **Issue #XX**: Foundation infrastructure (tracing config, Flask instrumentation)
- **Issue #YY**: Core agent instrumentation (TransplantCoordinator, MedicationAdvisor)
- **Issue #ZZ**: Production hardening (PII filtering, performance benchmarking)
- **Issue #AA**: Interview preparation (dashboard, queries, demo script)

## References

- Honeycomb Instrumentation Plan: Provided by user (13-section implementation guide)
- OpenTelemetry Python Docs: https://opentelemetry.io/docs/languages/python/
- Honeycomb API Docs: https://docs.honeycomb.io/api/
- HIPAA Compliance Guide: https://www.hhs.gov/hipaa/index.html
- Transplant-GCP README: /home/adam/Code/transplant-gcp/README.md
- ADK Documentation: https://google.github.io/adk-docs/
- Gemini API Docs: https://ai.google.dev/docs

---

**Created**: 2025-11-30
**Status**: PLANNED
**Priority**: High (Interview preparation)
**Estimated Effort**: 11-15 hours over 2-3 days

🤖 Generated with [Claude Code](https://claude.com/claude-code)
