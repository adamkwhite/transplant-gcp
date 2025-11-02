# Pub/Sub Multi-Agent Communication Architecture

## Overview

This document describes the Google Pub/Sub-based asynchronous multi-agent communication implementation for the Transplant Medication Adherence system. This is one of three parallel implementations being developed (in-process, Pub/Sub, ADK orchestration).

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Coordinator Agent                            │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │            CoordinatorPublisher                           │      │
│  │  - publish_medication_request()                          │      │
│  │  - publish_symptom_request()                             │      │
│  │  - publish_interaction_request()                         │      │
│  │  - publish_multi_agent_request()                         │      │
│  └──────────────────────────────────────────────────────────┘      │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │     Google Cloud Pub/Sub                │
        │                                          │
        │  ┌────────────────────────────────┐     │
        │  │  Topics:                       │     │
        │  │  • medication-requests         │     │
        │  │  • symptom-requests            │     │
        │  │  • interaction-requests        │     │
        │  │  • coordinator-responses       │     │
        │  └────────────────────────────────┘     │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Medication  │      │   Symptom    │      │ Interaction  │
│   Subscriber │      │  Subscriber  │      │  Subscriber  │
│              │      │              │      │              │
│   Invokes:   │      │   Invokes:   │      │   Invokes:   │
│ Medication   │      │  Symptom     │      │ Drug         │
│ Advisor      │      │  Monitor     │      │ Interaction  │
│ Agent        │      │  Agent       │      │ Checker      │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    coordinator-responses
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │       ResponseAggregator                 │
        │  - Tracks responses by request_id        │
        │  - Implements 10-second timeout          │
        │  - Synthesizes final recommendations     │
        └─────────────────────────────────────────┘
```

### Message Flow Sequence

```
Coordinator                Pub/Sub              Specialist         Agent
    │                         │                     │               │
    │ 1. Publish Request      │                     │               │
    ├────────────────────────>│                     │               │
    │   (request_id, params)  │                     │               │
    │                         │                     │               │
    │                         │ 2. Deliver Message  │               │
    │                         ├────────────────────>│               │
    │                         │                     │               │
    │                         │                     │ 3. Invoke     │
    │                         │                     ├──────────────>│
    │                         │                     │               │
    │                         │                     │ 4. Response   │
    │                         │                     │<──────────────┤
    │                         │                     │               │
    │                         │ 5. Publish Response │               │
    │                         │<────────────────────┤               │
    │                         │  (request_id, result)              │
    │                         │                     │               │
    │ 6. Deliver Response     │                     │               │
    │<────────────────────────┤                     │               │
    │                         │                     │               │
    │ 7. Aggregate & Synthesize                    │               │
    ├─────────────────────────────────────────────────────────────>│
```

## Components

### 1. CoordinatorPublisher

**Location**: `services/pubsub/coordinator_publisher.py`

**Responsibilities**:
- Publishes request messages to specialist-specific topics
- Generates unique request_id for correlation
- Supports single and multi-agent requests

**Message Schema**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "patient-123",
  "request_type": "medication_advice|symptom_check|interaction_check",
  "parameters": {
    // Request-specific parameters
  },
  "patient_context": {
    "transplant_type": "kidney",
    "days_post_transplant": 45
  },
  "timestamp": 1704096000.0
}
```

**API**:
- `publish_medication_request(patient_id, medication_name, scheduled_time, actual_time, patient_context)` → request_id
- `publish_symptom_request(patient_id, symptoms, severity, duration_hours, patient_context)` → request_id
- `publish_interaction_request(patient_id, current_medications, new_medication, patient_context)` → request_id
- `publish_multi_agent_request(patient_id, request_types, parameters, patient_context)` → [request_ids]

### 2. SpecialistSubscribers

**Location**: `services/pubsub/specialist_subscribers.py`

**Responsibilities**:
- Subscribe to specialist-specific topics
- Invoke appropriate specialist agents
- Publish results to coordinator-responses topic

**Subscriber Functions**:
- `on_medication_request()` → Invokes MedicationAdvisorAgent
- `on_symptom_request()` → Invokes SymptomMonitorAgent
- `on_drug_interaction_request()` → Invokes DrugInteractionCheckerAgent

**Response Schema**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_id": "patient-123",
  "agent_type": "MedicationAdvisor",
  "agent_response": {
    // Agent-specific response data
  },
  "processing_time": 2.45,
  "timestamp": 1704096002.45,
  "status": "success|error"
}
```

### 3. ResponseAggregator

**Location**: `services/pubsub/response_aggregator.py`

**Responsibilities**:
- Subscribe to coordinator-responses topic
- Track responses by request_id
- Implement timeout handling (default: 10 seconds)
- Synthesize final recommendations from multiple specialists

**API**:
- `wait_for_responses(request_ids, expected_count, callback)` → aggregated_result

**Timeout Behavior**:
- Waits up to 10 seconds for all expected responses
- Returns partial results if timeout occurs
- Includes timeout flag in synthesis

## Infrastructure Setup

### Local Development (Emulator)

1. **Install gcloud SDK**:
   ```bash
   # Install if not already present
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Run Setup Script**:
   ```bash
   bash scripts/setup_pubsub_emulator.sh
   ```

   This script:
   - Installs Pub/Sub emulator component
   - Starts emulator on localhost:8085
   - Creates required topics and subscriptions
   - Exports PUBSUB_EMULATOR_HOST environment variable

3. **Verify Setup**:
   ```bash
   echo $PUBSUB_EMULATOR_HOST  # Should show: localhost:8085
   ```

### Production (Google Cloud Pub/Sub)

1. **Create GCP Project**:
   ```bash
   gcloud projects create transplant-medication-prod
   gcloud config set project transplant-medication-prod
   ```

2. **Enable Pub/Sub API**:
   ```bash
   gcloud services enable pubsub.googleapis.com
   ```

3. **Create Topics**:
   ```bash
   gcloud pubsub topics create medication-requests
   gcloud pubsub topics create symptom-requests
   gcloud pubsub topics create interaction-requests
   gcloud pubsub topics create coordinator-responses
   ```

4. **Create Subscriptions**:
   ```bash
   gcloud pubsub subscriptions create medication-requests-sub \
     --topic=medication-requests \
     --ack-deadline=60

   gcloud pubsub subscriptions create symptom-requests-sub \
     --topic=symptom-requests \
     --ack-deadline=60

   gcloud pubsub subscriptions create interaction-requests-sub \
     --topic=interaction-requests \
     --ack-deadline=60

   gcloud pubsub subscriptions create coordinator-responses-sub \
     --topic=coordinator-responses \
     --ack-deadline=60
   ```

5. **Configure Authentication**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

## Testing

### Integration Tests

**Location**: `tests/integration/test_pubsub_communication.py`

**Test Coverage**:
- End-to-end medication request flow
- End-to-end symptom request flow
- End-to-end interaction request flow
- Multi-agent request coordination
- Timeout handling with partial responses
- Message retry on subscriber failure
- Concurrent requests from multiple patients
- End-to-end latency measurement

**Run Tests**:
```bash
# Start emulator first
bash scripts/setup_pubsub_emulator.sh

# In another terminal, export emulator host
export PUBSUB_EMULATOR_HOST=localhost:8085

# Run integration tests
pytest tests/integration/test_pubsub_communication.py -v -m integration
```

### Benchmarks

**Location**: `scripts/benchmark_pubsub.py`

**Metrics Measured**:
- Single-agent request latency
- Multi-agent request latency
- Agent processing time vs message overhead
- Parallelism benefit (speedup from concurrent processing)
- Success rate

**Run Benchmarks**:
```bash
# Ensure emulator is running
export PUBSUB_EMULATOR_HOST=localhost:8085

# Run benchmark (10 iterations by default)
python scripts/benchmark_pubsub.py

# Run with custom iterations and output
python scripts/benchmark_pubsub.py -n 20 -o benchmarks/custom_results.json
```

## Cost Analysis

### Production Pub/Sub Costs (Estimated)

**Pricing** (as of 2024):
- Message publish/subscribe: $0.06 per GB (first 10 GB free per month)
- Message storage: $0.27 per GB-month (messages retained for redelivery)

**Usage Estimates** (1000 patients, 10 requests/patient/day):
- Daily requests: 10,000
- Messages per request (avg): 4 (3 specialist requests + 1 aggregated response)
- Total messages/day: 40,000
- Average message size: 2 KB
- Daily data: 80 MB (0.08 GB)
- Monthly data: ~2.4 GB

**Monthly Cost Estimate**:
- Message operations: 2.4 GB × $0.06 = **$0.14/month**
- Storage (negligible for short-lived messages): **~$0.01/month**
- **Total: ~$0.15/month** (well within free tier for small-scale deployments)

**Scaling Considerations**:
- 10,000 patients: ~$1.50/month
- 100,000 patients: ~$15/month
- Very cost-effective compared to alternatives

## Pros and Cons

### Advantages ✅

1. **Asynchronous & Non-Blocking**
   - Coordinator doesn't block waiting for agents
   - Better resource utilization
   - Supports true parallel processing

2. **Scalability**
   - Horizontally scalable (add more subscribers)
   - Auto-scaling subscriber instances
   - Queue buffering handles traffic spikes

3. **Reliability**
   - Built-in retry mechanism (nack → redelivery)
   - Message persistence (at-least-once delivery)
   - Graceful degradation (partial responses with timeout)

4. **Decoupling**
   - Loose coupling between coordinator and specialists
   - Easy to add/remove specialist agents
   - Each component can be deployed independently

5. **Observability**
   - Message-level tracing via request_id
   - Built-in metrics (message throughput, latency)
   - Dead-letter queues for failed messages

6. **Cost-Effective**
   - Very low cost at small-medium scale
   - No infrastructure to manage (serverless)

### Disadvantages ❌

1. **Latency Overhead**
   - Message serialization/deserialization
   - Network round-trips (publish → deliver → respond)
   - Typically 100-500ms overhead vs in-process

2. **Complexity**
   - More moving parts (topics, subscriptions, emulator)
   - Harder to debug (distributed tracing needed)
   - Requires infrastructure setup

3. **Emulator Limitations**
   - Emulator behavior may differ from production
   - No exactly-once delivery guarantee (duplicate messages possible)
   - Testing requires emulator to be running

4. **State Management**
   - Response aggregation requires tracking state
   - Timeout handling adds complexity
   - Need to handle partial responses

5. **Network Dependency**
   - Requires network connectivity
   - Potential for network failures
   - Latency varies with network conditions

6. **Operational Overhead**
   - Need to monitor topic health
   - Manage subscription backlog
   - Handle duplicate message scenarios

## Comparison: Pub/Sub vs In-Process

| Aspect | Pub/Sub | In-Process |
|--------|---------|------------|
| **Latency** | ~2-5s (includes message overhead) | ~1-3s (direct function calls) |
| **Scalability** | Excellent (horizontal) | Limited (vertical) |
| **Reliability** | High (retry, persistence) | Moderate (no retry by default) |
| **Complexity** | High (distributed system) | Low (single process) |
| **Cost** | ~$0.15-15/month (usage-based) | Free (compute only) |
| **Debugging** | Hard (distributed traces) | Easy (single stack trace) |
| **Deployment** | Independent services | Monolithic |
| **Parallelism** | True parallel (separate workers) | Pseudo-parallel (threading) |

## When to Use Pub/Sub

**Use Pub/Sub when**:
- ✅ Need horizontal scalability
- ✅ Traffic is spiky/unpredictable
- ✅ Require guaranteed delivery with retries
- ✅ Want independent deployments of coordinator/specialists
- ✅ Need to support multiple subscribers per topic (fan-out)

**Use In-Process when**:
- ✅ Latency is critical (<1s end-to-end)
- ✅ Simple deployment is important
- ✅ Traffic is low-moderate and predictable
- ✅ Don't need horizontal scaling
- ✅ Minimal operational overhead is desired

## Future Enhancements

1. **Dead-Letter Queue**
   - Handle permanently failed messages
   - Alert on repeated failures

2. **Message Deduplication**
   - Track processed request_ids
   - Prevent duplicate processing

3. **Priority Queues**
   - Separate topics for urgent vs routine requests
   - Ensure critical requests processed first

4. **Metrics & Monitoring**
   - Export latency metrics to Cloud Monitoring
   - Alert on high latency or low success rate

5. **Circuit Breaker**
   - Detect and handle specialist agent failures
   - Graceful degradation when agents unavailable

6. **Message Batching**
   - Batch multiple requests for efficiency
   - Reduce per-message overhead

## References

- [Google Cloud Pub/Sub Documentation](https://cloud.google.com/pubsub/docs)
- [Pub/Sub Emulator](https://cloud.google.com/pubsub/docs/emulator)
- [Python Client Library](https://googleapis.dev/python/pubsub/latest/)
- [Best Practices for Cloud Pub/Sub](https://cloud.google.com/pubsub/docs/publisher)
