# Pub/Sub Setup Guide

## Quick Start

### 1. Install Pub/Sub Emulator

The emulator is needed for local development and testing.

**Option A: Using gcloud component manager** (if available):
```bash
gcloud components install pubsub-emulator
```

**Option B: Using apt** (for managed gcloud installations):
```bash
sudo apt-get install -y google-cloud-cli-pubsub-emulator
```

### 2. Install Python Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install Pub/Sub client library
pip install google-cloud-pubsub==2.18.4
```

### 3. Start the Emulator

```bash
# Run the setup script
bash scripts/setup_pubsub_emulator.sh
```

This script will:
- Check if emulator is installed
- Start emulator on localhost:8085
- Create required topics and subscriptions
- Export PUBSUB_EMULATOR_HOST environment variable

### 4. Verify Setup

```bash
# Check emulator is running
echo $PUBSUB_EMULATOR_HOST  # Should show: localhost:8085

# Test publisher
source venv/bin/activate
python services/pubsub/coordinator_publisher.py
```

## Running the System

### Terminal 1: Start Emulator
```bash
bash scripts/setup_pubsub_emulator.sh
```

### Terminal 2: Start Specialist Subscribers
```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
source venv/bin/activate
python services/pubsub/specialist_subscribers.py
```

### Terminal 3: Test Full Flow
```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
source venv/bin/activate
python services/pubsub/response_aggregator.py
```

## Running Tests

```bash
# Ensure emulator is running in Terminal 1
export PUBSUB_EMULATOR_HOST=localhost:8085
source venv/bin/activate

# Run integration tests
pytest tests/integration/test_pubsub_communication.py -v -m integration

# Run benchmarks
python scripts/benchmark_pubsub.py -n 10
```

## Troubleshooting

### Emulator Won't Start

**Problem**: `gcloud components install` fails with "component manager is disabled"

**Solution**: Install via apt:
```bash
sudo apt-get install -y google-cloud-cli-pubsub-emulator
```

### Port Already in Use

**Problem**: Emulator fails to start on port 8085

**Solution**: Kill existing process:
```bash
lsof -ti:8085 | xargs kill -9
```

### PUBSUB_EMULATOR_HOST Not Set

**Problem**: Tests connect to real Pub/Sub instead of emulator

**Solution**: Export environment variable in every terminal:
```bash
export PUBSUB_EMULATOR_HOST=localhost:8085
```

### Topics Not Created

**Problem**: Subscribers fail with "Topic not found"

**Solution**: Re-run setup script to create topics:
```bash
bash scripts/setup_pubsub_emulator.sh
```

## Production Deployment

For production deployment to Google Cloud Pub/Sub, see:
- [docs/architecture/pubsub-communication.md](architecture/pubsub-communication.md)
