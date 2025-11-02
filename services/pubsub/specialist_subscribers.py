"""
Specialist Subscriber Functions for Pub/Sub Communication

Subscriber callbacks that receive requests from coordinator and invoke specialist agents.
Each subscriber publishes results back to the coordinator-responses topic.
"""

import json
import os
import time
from typing import Any

from google.cloud import pubsub_v1

from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent


class SpecialistSubscribers:
    """
    Container for specialist subscriber callbacks.

    Each specialist agent has a dedicated subscriber that:
    1. Receives request messages from its topic
    2. Invokes the appropriate specialist agent
    3. Publishes the response to coordinator-responses topic
    """

    def __init__(self, project_id: str = "transplant-pubsub-emulator"):
        """
        Initialize specialist subscribers.

        Args:
            project_id: GCP project ID (use emulator default for local dev)
        """
        self.project_id = project_id

        # Create publisher for responses
        self.publisher = pubsub_v1.PublisherClient()
        self.response_topic = self.publisher.topic_path(project_id, "coordinator-responses")

        # Initialize specialist agents
        self.medication_advisor = MedicationAdvisorAgent()
        self.symptom_monitor = SymptomMonitorAgent()
        self.drug_interaction_checker = DrugInteractionCheckerAgent()

    def on_medication_request(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """
        Process medication advisor requests.

        Args:
            message: Pub/Sub message containing medication request
        """
        try:
            # Parse message
            request_data = json.loads(message.data.decode("utf-8"))
            request_id = request_data["request_id"]
            patient_id = request_data["patient_id"]
            parameters = request_data["parameters"]
            patient_context = request_data.get("patient_context", {})

            print(f"Processing medication request: {request_id}")

            # Invoke medication advisor agent
            start_time = time.time()
            agent_response = self.medication_advisor.analyze_missed_dose(
                medication=parameters["medication_name"],
                scheduled_time=parameters["scheduled_time"],
                current_time=parameters["actual_time"],
                patient_id=patient_id,
                patient_context=patient_context,
            )
            processing_time = time.time() - start_time

            # Build response message
            response_data = {
                "request_id": request_id,
                "patient_id": patient_id,
                "agent_type": "MedicationAdvisor",
                "agent_response": agent_response,
                "processing_time": processing_time,
                "timestamp": time.time(),
                "status": "success",
            }

            # Publish response
            self._publish_response(response_data)

            # Acknowledge message
            message.ack()
            print(f"Completed medication request: {request_id} ({processing_time:.2f}s)")

        except Exception as e:
            print(f"Error processing medication request: {e}")
            # Publish error response
            self._publish_error_response(request_data, str(e))
            message.nack()

    def on_symptom_request(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """
        Process symptom monitor requests.

        Args:
            message: Pub/Sub message containing symptom request
        """
        try:
            # Parse message
            request_data = json.loads(message.data.decode("utf-8"))
            request_id = request_data["request_id"]
            patient_id = request_data["patient_id"]
            parameters = request_data["parameters"]
            patient_context = request_data.get("patient_context", {})

            print(f"Processing symptom request: {request_id}")

            # Invoke symptom monitor agent
            start_time = time.time()
            agent_response = self.symptom_monitor.analyze_symptoms(
                symptoms=parameters["symptoms"],
                patient_id=patient_id,
                patient_context=patient_context,
                vital_signs=parameters.get("vital_signs"),
            )
            processing_time = time.time() - start_time

            # Build response message
            response_data = {
                "request_id": request_id,
                "patient_id": patient_id,
                "agent_type": "SymptomMonitor",
                "agent_response": agent_response,
                "processing_time": processing_time,
                "timestamp": time.time(),
                "status": "success",
            }

            # Publish response
            self._publish_response(response_data)

            # Acknowledge message
            message.ack()
            print(f"Completed symptom request: {request_id} ({processing_time:.2f}s)")

        except Exception as e:
            print(f"Error processing symptom request: {e}")
            # Publish error response
            self._publish_error_response(request_data, str(e))
            message.nack()

    def on_drug_interaction_request(self, message: pubsub_v1.subscriber.message.Message) -> None:
        """
        Process drug interaction check requests.

        Args:
            message: Pub/Sub message containing interaction request
        """
        try:
            # Parse message
            request_data = json.loads(message.data.decode("utf-8"))
            request_id = request_data["request_id"]
            patient_id = request_data["patient_id"]
            parameters = request_data["parameters"]
            patient_context = request_data.get("patient_context", {})

            print(f"Processing interaction request: {request_id}")

            # Build medication list for checking
            medications = parameters.get("current_medications", [])
            if parameters.get("new_medication"):
                medications = medications + [parameters["new_medication"]]

            foods = [parameters["new_food"]] if parameters.get("new_food") else None
            supplements = (
                [parameters["new_supplement"]] if parameters.get("new_supplement") else None
            )

            # Invoke drug interaction checker agent
            start_time = time.time()
            agent_response = self.drug_interaction_checker.check_interaction(
                medications=medications,
                foods=foods,
                supplements=supplements,
                patient_id=patient_id,
                patient_context=patient_context,
            )
            processing_time = time.time() - start_time

            # Build response message
            response_data = {
                "request_id": request_id,
                "patient_id": patient_id,
                "agent_type": "DrugInteractionChecker",
                "agent_response": agent_response,
                "processing_time": processing_time,
                "timestamp": time.time(),
                "status": "success",
            }

            # Publish response
            self._publish_response(response_data)

            # Acknowledge message
            message.ack()
            print(f"Completed interaction request: {request_id} ({processing_time:.2f}s)")

        except Exception as e:
            print(f"Error processing interaction request: {e}")
            # Publish error response
            self._publish_error_response(request_data, str(e))
            message.nack()

    def _publish_response(self, response_data: dict[str, Any]) -> None:
        """
        Publish response to coordinator-responses topic.

        Args:
            response_data: Response data to publish
        """
        message_bytes = json.dumps(response_data).encode("utf-8")

        future = self.publisher.publish(
            self.response_topic,
            message_bytes,
            request_id=response_data["request_id"],
            agent_type=response_data["agent_type"],
        )

        # Wait for publish to complete
        try:
            message_id = future.result(timeout=5.0)
            print(f"Published response {message_id} for request {response_data['request_id']}")
        except Exception as e:
            print(f"Failed to publish response: {e}")
            raise

    def _publish_error_response(self, request_data: dict[str, Any], error_msg: str) -> None:
        """
        Publish error response when agent processing fails.

        Args:
            request_data: Original request data
            error_msg: Error message
        """
        response_data = {
            "request_id": request_data.get("request_id", "unknown"),
            "patient_id": request_data.get("patient_id", "unknown"),
            "agent_type": "Error",
            "agent_response": {"error": error_msg},
            "processing_time": 0.0,
            "timestamp": time.time(),
            "status": "error",
        }
        self._publish_response(response_data)

    def close(self) -> None:
        """Close the publisher client."""
        self.publisher.stop()


# Standalone callback functions for use with subscriber.subscribe()
_specialist_subscribers = None


def get_specialist_subscribers() -> SpecialistSubscribers:
    """Get or create singleton SpecialistSubscribers instance."""
    global _specialist_subscribers
    if _specialist_subscribers is None:
        _specialist_subscribers = SpecialistSubscribers()
    return _specialist_subscribers


def on_medication_request(message: pubsub_v1.subscriber.message.Message) -> None:
    """Standalone callback for medication requests."""
    get_specialist_subscribers().on_medication_request(message)


def on_symptom_request(message: pubsub_v1.subscriber.message.Message) -> None:
    """Standalone callback for symptom requests."""
    get_specialist_subscribers().on_symptom_request(message)


def on_drug_interaction_request(message: pubsub_v1.subscriber.message.Message) -> None:
    """Standalone callback for drug interaction requests."""
    get_specialist_subscribers().on_drug_interaction_request(message)


# Subscriber runner for testing
def main() -> None:
    """Run all specialist subscribers for testing."""
    import concurrent.futures
    import signal
    import sys

    # Ensure emulator is being used
    if "PUBSUB_EMULATOR_HOST" not in os.environ:
        print("WARNING: PUBSUB_EMULATOR_HOST not set. Using live Pub/Sub.")
        print("Set export PUBSUB_EMULATOR_HOST=localhost:8085 to use emulator")

    project_id = "transplant-pubsub-emulator"
    subscriber = pubsub_v1.SubscriberClient()

    # Subscription paths
    medication_sub = subscriber.subscription_path(project_id, "medication-requests-sub")
    symptom_sub = subscriber.subscription_path(project_id, "symptom-requests-sub")
    interaction_sub = subscriber.subscription_path(project_id, "interaction-requests-sub")

    print("Starting specialist subscribers...")
    print(f"  - Medication requests: {medication_sub}")
    print(f"  - Symptom requests: {symptom_sub}")
    print(f"  - Interaction requests: {interaction_sub}")

    # Start streaming pull for each subscription
    futures = []
    futures.append(subscriber.subscribe(medication_sub, callback=on_medication_request))
    futures.append(subscriber.subscribe(symptom_sub, callback=on_symptom_request))
    futures.append(subscriber.subscribe(interaction_sub, callback=on_drug_interaction_request))

    print("\nSubscribers running. Press Ctrl+C to stop.")

    # Handle graceful shutdown
    def signal_handler(_sig: int, _frame: Any) -> None:
        print("\nShutting down subscribers...")
        for future in futures:
            future.cancel()
        get_specialist_subscribers().close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Keep running
    import contextlib

    with (
        concurrent.futures.ThreadPoolExecutor() as executor,
        contextlib.suppress(KeyboardInterrupt),
    ):
        executor.map(lambda f: f.result(), futures)


if __name__ == "__main__":
    main()
