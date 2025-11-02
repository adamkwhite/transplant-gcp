# Running Pub/Sub Integration Tests

## Prerequisites Completed ✅
- API key configured in `.env` file
- Python dependencies installed
- Code implementation complete

## What You Need to Do

### Step 1: Install Pub/Sub Emulator (One-time setup)
```bash
sudo apt-get install -y google-cloud-cli-pubsub-emulator
```

### Step 2: Open 3 Terminal Windows

#### Terminal 1: Start the Emulator
```bash
cd /home/adam/Code/transplant-gcp-pubsub
bash scripts/setup_pubsub_emulator.sh
```

**Wait for this message:**
```
=== Setup Complete ===
Emulator is running on: localhost:8085
```

Keep this terminal open! The emulator must stay running.

#### Terminal 2: Start Specialist Subscribers
```bash
cd /home/adam/Code/transplant-gcp-pubsub
source ../transplant-gcp/venv/bin/activate
set -a && source .env && set +a
export PUBSUB_EMULATOR_HOST=localhost:8085

python services/pubsub/specialist_subscribers.py
```

**Wait for this message:**
```
Subscribers running. Press Ctrl+C to stop.
```

Keep this terminal open! Subscribers must stay running.

#### Terminal 3: Run Integration Tests
```bash
cd /home/adam/Code/transplant-gcp-pubsub
source ../transplant-gcp/venv/bin/activate
set -a && source .env && set +a
export PUBSUB_EMULATOR_HOST=localhost:8085

# Run integration tests
pytest tests/integration/test_pubsub_communication.py -v -m integration

# After tests pass, run benchmarks
python scripts/benchmark_pubsub.py -n 10
```

## Expected Test Results

### Integration Tests (9 tests)
- ✅ `test_end_to_end_medication_request` - Single medication request flow
- ✅ `test_end_to_end_symptom_request` - Single symptom request flow
- ✅ `test_end_to_end_interaction_request` - Single interaction request flow
- ✅ `test_multi_agent_request` - All 3 agents coordinating
- ✅ `test_timeout_handling` - Partial response after timeout
- ✅ `test_message_retry_on_nack` - Retry mechanism
- ✅ `test_concurrent_requests` - Multiple patients simultaneously
- ✅ `test_end_to_end_latency` - Performance measurement

### Benchmark Results
You'll get output showing:
- **Single-agent latency**: Mean, median, min, max
- **Multi-agent latency**: With 3 specialists
- **Parallelism benefit**: Speedup from concurrent processing
- **Message overhead**: Pub/Sub vs agent processing time

Results saved to: `benchmarks/pubsub_results.json`

## Troubleshooting

### "Port 8085 already in use"
```bash
lsof -ti:8085 | xargs kill -9
```

### "PUBSUB_EMULATOR_HOST not set"
Make sure you ran:
```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
```
in **every** terminal window.

### "No module named google.cloud.pubsub"
```bash
source ../transplant-gcp/venv/bin/activate
pip install google-cloud-pubsub==2.18.4
```

### Tests timeout
Make sure Terminal 2 (subscribers) is running!

## Quick Test (Alternative)

If you just want to verify the code works, run this quick test:

```bash
cd /home/adam/Code/transplant-gcp-pubsub
source ../transplant-gcp/venv/bin/activate
set -a && source .env && set +a

# Test that agents can be instantiated
python3 -c "
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent
from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent

print('✓ All agents import successfully')
print('✓ API key configured')
print('Ready for integration testing!')
"
```

## After Testing

1. **Compare Results**: Check `benchmarks/pubsub_results.json`
2. **Analyze Latency**: Compare to in-process implementation (if available)
3. **Provide Feedback**: Comment on PR #11

## Notes

- Integration tests require ~2-5 minutes to run
- Benchmarks take ~3-5 minutes (10 iterations)
- All tests should pass if emulator + subscribers are running
- DO NOT merge PR #11 - it's for comparison only
