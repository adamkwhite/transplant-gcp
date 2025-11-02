#!/bin/bash
# Pub/Sub Emulator Setup Script
# Sets up and starts Google Pub/Sub emulator for local development and testing

set -e  # Exit on error

EMULATOR_PORT=8085
EMULATOR_HOST="localhost:${EMULATOR_PORT}"

echo "=== Google Pub/Sub Emulator Setup ==="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI is not installed"
    echo "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if emulator is already installed
if ! gcloud components list --filter="id:pubsub-emulator" --format="value(state.name)" | grep -q "Installed" 2>/dev/null; then
    echo "Installing Pub/Sub emulator component..."
    # Try gcloud components install first
    if ! gcloud components install pubsub-emulator --quiet 2>/dev/null; then
        # If that fails, try apt-get (for managed gcloud installations)
        echo "gcloud component manager disabled, trying apt-get..."
        if ! sudo apt-get install -y google-cloud-cli-pubsub-emulator 2>/dev/null; then
            echo "ERROR: Failed to install emulator"
            echo "Please run manually:"
            echo "  sudo apt-get install -y google-cloud-cli-pubsub-emulator"
            exit 1
        fi
    fi
else
    echo "Pub/Sub emulator already installed"
fi

# Kill any existing emulator process on the port
if lsof -Pi :${EMULATOR_PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Stopping existing emulator on port ${EMULATOR_PORT}..."
    kill $(lsof -t -i:${EMULATOR_PORT}) 2>/dev/null || true
    sleep 2
fi

# Start the emulator in the background
echo "Starting Pub/Sub emulator on ${EMULATOR_HOST}..."
gcloud beta emulators pubsub start \
    --host-port=${EMULATOR_HOST} \
    --log-http \
    > /tmp/pubsub-emulator.log 2>&1 &

EMULATOR_PID=$!
echo "Emulator started with PID: ${EMULATOR_PID}"

# Wait for emulator to be ready
echo "Waiting for emulator to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s "http://${EMULATOR_HOST}" > /dev/null 2>&1; then
        echo "Emulator is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 1
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Emulator failed to start within ${MAX_RETRIES} seconds"
    echo "Check logs at: /tmp/pubsub-emulator.log"
    exit 1
fi

# Export environment variable for client libraries
export PUBSUB_EMULATOR_HOST=${EMULATOR_HOST}
echo "Exported PUBSUB_EMULATOR_HOST=${EMULATOR_HOST}"

# Create topics using Python (more reliable than gcloud with emulator)
echo "Creating topics and subscriptions..."
python3 << 'EOF'
import os
from google.cloud import pubsub_v1

# Ensure emulator host is set
os.environ['PUBSUB_EMULATOR_HOST'] = 'localhost:8085'

# Project ID (can be any value for emulator)
project_id = "transplant-pubsub-emulator"

# Create publisher and subscriber clients
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# Define topics and subscriptions
topics_and_subs = {
    'medication-requests': 'medication-requests-sub',
    'symptom-requests': 'symptom-requests-sub',
    'interaction-requests': 'interaction-requests-sub',
    'coordinator-responses': 'coordinator-responses-sub',
}

# Create topics
for topic_name in topics_and_subs.keys():
    topic_path = publisher.topic_path(project_id, topic_name)
    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"✓ Created topic: {topic_name}")
    except Exception as e:
        if "ALREADY_EXISTS" in str(e):
            print(f"✓ Topic already exists: {topic_name}")
        else:
            print(f"✗ Failed to create topic {topic_name}: {e}")
            raise

# Create subscriptions
for topic_name, sub_name in topics_and_subs.items():
    topic_path = publisher.topic_path(project_id, topic_name)
    subscription_path = subscriber.subscription_path(project_id, sub_name)
    try:
        subscriber.create_subscription(
            request={
                "name": subscription_path,
                "topic": topic_path,
                "ack_deadline_seconds": 60,
            }
        )
        print(f"✓ Created subscription: {sub_name}")
    except Exception as e:
        if "ALREADY_EXISTS" in str(e):
            print(f"✓ Subscription already exists: {sub_name}")
        else:
            print(f"✗ Failed to create subscription {sub_name}: {e}")
            raise

print("\nAll topics and subscriptions created successfully!")
EOF

echo ""
echo "=== Setup Complete ==="
echo "Emulator is running on: ${EMULATOR_HOST}"
echo "Emulator PID: ${EMULATOR_PID}"
echo "Logs: /tmp/pubsub-emulator.log"
echo ""
echo "To use the emulator in your terminal session, run:"
echo "  export PUBSUB_EMULATOR_HOST=${EMULATOR_HOST}"
echo ""
echo "To stop the emulator:"
echo "  kill ${EMULATOR_PID}"
echo ""
echo "Created topics:"
echo "  - medication-requests"
echo "  - symptom-requests"
echo "  - interaction-requests"
echo "  - coordinator-responses"
