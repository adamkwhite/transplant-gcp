"""
Create Pub/Sub Topics and Subscriptions for Emulator

This script creates the necessary topics and subscriptions for the
multi-agent communication system in the Pub/Sub emulator.
"""

import os

from google.cloud import pubsub_v1  # type: ignore[attr-defined]

# Configuration
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "transplant-pubsub-emulator")
EMULATOR_HOST = os.getenv("PUBSUB_EMULATOR_HOST", "localhost:8085")

# Topics and their subscriptions
TOPICS = {
    "medication-requests": ["medication-requests-sub"],
    "symptom-requests": ["symptom-requests-sub"],
    "interaction-requests": ["interaction-requests-sub"],
    "coordinator-responses": ["coordinator-responses-sub"],
}


def create_topics_and_subscriptions() -> None:
    """Create all required topics and subscriptions."""
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    print(f"Creating topics and subscriptions for project: {PROJECT_ID}")
    print(f"Using emulator: {EMULATOR_HOST}")

    for topic_name, subscription_names in TOPICS.items():
        # Create topic
        topic_path = publisher.topic_path(PROJECT_ID, topic_name)
        try:
            publisher.create_topic(request={"name": topic_path})
            print(f"✓ Created topic: {topic_name}")
        except Exception as e:
            print(f"  Topic {topic_name} already exists or error: {e}")

        # Create subscriptions
        for sub_name in subscription_names:
            subscription_path = subscriber.subscription_path(PROJECT_ID, sub_name)
            try:
                subscriber.create_subscription(
                    request={"name": subscription_path, "topic": topic_path}
                )
                print(f"✓ Created subscription: {sub_name}")
            except Exception as e:
                print(f"  Subscription {sub_name} already exists or error: {e}")

    print("\nPub/Sub setup complete!")


if __name__ == "__main__":
    create_topics_and_subscriptions()
