"""
Coordinator Publisher for Pub/Sub Communication

Publishes request messages from coordinator to specialist agent topics.
"""

import json
import os
import time
import uuid
from typing import Any

from google.cloud import pubsub_v1


class CoordinatorPublisher:
    """
    Publisher for coordinator agent to send requests to specialist agents.

    The coordinator publishes messages to topic-specific queues:
    - medication-requests: For MedicationAdvisorAgent
    - symptom-requests: For SymptomMonitorAgent
    - interaction-requests: For DrugInteractionAgent
    """

    def __init__(self, project_id: str = "transplant-pubsub-emulator"):
        """
        Initialize the coordinator publisher.

        Args:
            project_id: GCP project ID (use emulator default for local dev)
        """
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()

        # Topic paths
        self.medication_topic = self.publisher.topic_path(project_id, "medication-requests")
        self.symptom_topic = self.publisher.topic_path(project_id, "symptom-requests")
        self.interaction_topic = self.publisher.topic_path(project_id, "interaction-requests")

    def publish_medication_request(
        self,
        patient_id: str,
        medication_name: str,
        scheduled_time: str,
        actual_time: str,
        patient_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Publish medication advisor request.

        Args:
            patient_id: Patient identifier
            medication_name: Name of medication (e.g., "tacrolimus")
            scheduled_time: When dose should have been taken (ISO format)
            actual_time: When dose was/will be taken (ISO format)
            patient_context: Additional patient medical context

        Returns:
            request_id: Unique request identifier for correlation
        """
        request_id = str(uuid.uuid4())

        message_data = {
            "request_id": request_id,
            "patient_id": patient_id,
            "request_type": "medication_advice",
            "parameters": {
                "medication_name": medication_name,
                "scheduled_time": scheduled_time,
                "actual_time": actual_time,
            },
            "patient_context": patient_context or {},
            "timestamp": time.time(),
        }

        self._publish_message(self.medication_topic, message_data)
        return request_id

    def publish_symptom_request(
        self,
        patient_id: str,
        symptoms: list[str],
        severity: str,
        duration_hours: float,
        patient_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Publish symptom monitor request.

        Args:
            patient_id: Patient identifier
            symptoms: List of symptoms (e.g., ["fever", "nausea"])
            severity: Severity level ("mild", "moderate", "severe")
            duration_hours: How long symptoms have persisted
            patient_context: Additional patient medical context

        Returns:
            request_id: Unique request identifier for correlation
        """
        request_id = str(uuid.uuid4())

        message_data = {
            "request_id": request_id,
            "patient_id": patient_id,
            "request_type": "symptom_check",
            "parameters": {
                "symptoms": symptoms,
                "severity": severity,
                "duration_hours": duration_hours,
            },
            "patient_context": patient_context or {},
            "timestamp": time.time(),
        }

        self._publish_message(self.symptom_topic, message_data)
        return request_id

    def publish_interaction_request(
        self,
        patient_id: str,
        current_medications: list[str],
        new_medication: str | None = None,
        new_food: str | None = None,
        new_supplement: str | None = None,
        patient_context: dict[str, Any] | None = None,
    ) -> str:
        """
        Publish drug interaction check request.

        Args:
            patient_id: Patient identifier
            current_medications: List of current medications
            new_medication: New medication to check (optional)
            new_food: Food item to check (optional)
            new_supplement: Supplement to check (optional)
            patient_context: Additional patient medical context

        Returns:
            request_id: Unique request identifier for correlation
        """
        request_id = str(uuid.uuid4())

        message_data = {
            "request_id": request_id,
            "patient_id": patient_id,
            "request_type": "interaction_check",
            "parameters": {
                "current_medications": current_medications,
                "new_medication": new_medication,
                "new_food": new_food,
                "new_supplement": new_supplement,
            },
            "patient_context": patient_context or {},
            "timestamp": time.time(),
        }

        self._publish_message(self.interaction_topic, message_data)
        return request_id

    def publish_multi_agent_request(
        self,
        patient_id: str,
        request_types: list[str],
        parameters: dict[str, Any],
        patient_context: dict[str, Any] | None = None,
    ) -> list[str]:
        """
        Publish requests to multiple specialist agents.

        Args:
            patient_id: Patient identifier
            request_types: List of request types (e.g., ["medication", "symptom"])
            parameters: Parameters dict with keys for each request type
            patient_context: Additional patient medical context

        Returns:
            List of request_ids for tracking responses
        """
        request_ids = []

        if "medication" in request_types:
            med_params = parameters.get("medication", {})
            request_id = self.publish_medication_request(
                patient_id=patient_id,
                medication_name=med_params.get("medication_name", ""),
                scheduled_time=med_params.get("scheduled_time", ""),
                actual_time=med_params.get("actual_time", ""),
                patient_context=patient_context,
            )
            request_ids.append(request_id)

        if "symptom" in request_types:
            symp_params = parameters.get("symptom", {})
            request_id = self.publish_symptom_request(
                patient_id=patient_id,
                symptoms=symp_params.get("symptoms", []),
                severity=symp_params.get("severity", "moderate"),
                duration_hours=symp_params.get("duration_hours", 0),
                patient_context=patient_context,
            )
            request_ids.append(request_id)

        if "interaction" in request_types:
            int_params = parameters.get("interaction", {})
            request_id = self.publish_interaction_request(
                patient_id=patient_id,
                current_medications=int_params.get("current_medications", []),
                new_medication=int_params.get("new_medication"),
                new_food=int_params.get("new_food"),
                new_supplement=int_params.get("new_supplement"),
                patient_context=patient_context,
            )
            request_ids.append(request_id)

        return request_ids

    def _publish_message(self, topic_path: str, message_data: dict[str, Any]) -> None:
        """
        Publish a message to a Pub/Sub topic.

        Args:
            topic_path: Full topic path
            message_data: Message data to publish
        """
        # Serialize message to JSON
        message_bytes = json.dumps(message_data).encode("utf-8")

        # Publish message
        future = self.publisher.publish(
            topic_path,
            message_bytes,
            request_id=message_data["request_id"],  # Add as attribute for filtering
            request_type=message_data["request_type"],
        )

        # Wait for publish to complete (with timeout)
        try:
            message_id = future.result(timeout=5.0)
            print(f"Published message {message_id} to {topic_path.split('/')[-1]}")
        except Exception as e:
            print(f"Failed to publish message: {e}")
            raise

    def close(self) -> None:
        """Close the publisher client."""
        # Flush any pending messages
        self.publisher.stop()


# Convenience function for quick testing
def main() -> None:
    """Test the coordinator publisher with the emulator."""
    # Ensure emulator is being used
    if "PUBSUB_EMULATOR_HOST" not in os.environ:
        print("WARNING: PUBSUB_EMULATOR_HOST not set. Using live Pub/Sub.")
        print("Set export PUBSUB_EMULATOR_HOST=localhost:8085 to use emulator")

    publisher = CoordinatorPublisher()

    # Test medication request
    print("\nPublishing test medication request...")
    request_id = publisher.publish_medication_request(
        patient_id="patient-123",
        medication_name="tacrolimus",
        scheduled_time="2024-01-01T08:00:00",
        actual_time="2024-01-01T10:30:00",
        patient_context={"transplant_type": "kidney", "days_post_transplant": 45},
    )
    print(f"Medication request published with ID: {request_id}")

    # Test symptom request
    print("\nPublishing test symptom request...")
    request_id = publisher.publish_symptom_request(
        patient_id="patient-123",
        symptoms=["fever", "fatigue"],
        severity="moderate",
        duration_hours=12.5,
        patient_context={"transplant_type": "kidney"},
    )
    print(f"Symptom request published with ID: {request_id}")

    # Test interaction request
    print("\nPublishing test interaction request...")
    request_id = publisher.publish_interaction_request(
        patient_id="patient-123",
        current_medications=["tacrolimus", "mycophenolate"],
        new_medication="ibuprofen",
        patient_context={"transplant_type": "kidney"},
    )
    print(f"Interaction request published with ID: {request_id}")

    publisher.close()
    print("\nAll test messages published successfully!")


if __name__ == "__main__":
    main()
