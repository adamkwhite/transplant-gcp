"""
Integration Tests for Pub/Sub Multi-Agent Communication

Tests the full end-to-end message flow from coordinator → specialists → aggregator.
Requires Pub/Sub emulator to be running.
"""

import os
import time
from typing import Any

import pytest
from google.cloud import pubsub_v1

from services.pubsub.coordinator_publisher import CoordinatorPublisher
from services.pubsub.response_aggregator import ResponseAggregator
from services.pubsub.specialist_subscribers import SpecialistSubscribers


@pytest.fixture(scope="module")
def ensure_emulator() -> None:
    """Ensure Pub/Sub emulator is configured."""
    if "PUBSUB_EMULATOR_HOST" not in os.environ:
        pytest.skip("PUBSUB_EMULATOR_HOST not set - emulator not running")


@pytest.fixture(scope="module")
def subscriber_thread(ensure_emulator: None) -> Any:  # noqa: ARG001
    """Start specialist subscribers in background thread."""
    subscribers = SpecialistSubscribers()

    # Create subscriber client
    subscriber_client = pubsub_v1.SubscriberClient()
    project_id = "transplant-pubsub-emulator"

    # Subscription paths
    medication_sub = subscriber_client.subscription_path(project_id, "medication-requests-sub")
    symptom_sub = subscriber_client.subscription_path(project_id, "symptom-requests-sub")
    interaction_sub = subscriber_client.subscription_path(project_id, "interaction-requests-sub")

    # Start subscribers
    futures = []
    futures.append(
        subscriber_client.subscribe(medication_sub, callback=subscribers.on_medication_request)
    )
    futures.append(
        subscriber_client.subscribe(symptom_sub, callback=subscribers.on_symptom_request)
    )
    futures.append(
        subscriber_client.subscribe(
            interaction_sub, callback=subscribers.on_drug_interaction_request
        )
    )

    # Let subscribers start
    time.sleep(2)

    yield

    # Cleanup
    for future in futures:
        future.cancel()
    subscribers.close()


@pytest.mark.integration
class TestPubSubCommunication:
    """Integration tests for Pub/Sub multi-agent communication."""

    def test_end_to_end_medication_request(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test medication request flows through the system correctly."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish medication request
        request_id = publisher.publish_medication_request(
            patient_id="test-patient-001",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T12:00:00",
            patient_context={"transplant_type": "kidney", "days_post_transplant": 30},
        )

        # Wait for response
        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        # Verify response
        assert result["complete"], "Should receive complete response"
        assert not result["timeout"], "Should not timeout"
        assert len(result["responses"]) == 1, "Should receive exactly one response"

        response = result["responses"][0]
        assert response["request_id"] == request_id
        assert response["agent_type"] == "MedicationAdvisor"
        assert response["status"] == "success"
        assert "agent_response" in response
        assert "processing_time" in response

        # Verify synthesis
        synthesis = result["synthesis"]
        assert synthesis["status"] == "complete"
        assert "MedicationAdvisor" in synthesis["agents_consulted"]
        assert synthesis["priority"] in ["routine", "urgent", "emergency", "information"]

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_end_to_end_symptom_request(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test symptom request flows through the system correctly."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish symptom request
        request_id = publisher.publish_symptom_request(
            patient_id="test-patient-002",
            symptoms=["fever", "decreased urine output"],
            severity="moderate",
            duration_hours=24.0,
            patient_context={"transplant_type": "kidney"},
        )

        # Wait for response
        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        # Verify response
        assert result["complete"], "Should receive complete response"
        assert not result["timeout"], "Should not timeout"
        assert len(result["responses"]) == 1

        response = result["responses"][0]
        assert response["request_id"] == request_id
        assert response["agent_type"] == "SymptomMonitor"
        assert response["status"] == "success"

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_end_to_end_interaction_request(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test interaction request flows through the system correctly."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish interaction request
        request_id = publisher.publish_interaction_request(
            patient_id="test-patient-003",
            current_medications=["tacrolimus", "mycophenolate"],
            new_medication="ibuprofen",
            patient_context={"transplant_type": "kidney"},
        )

        # Wait for response
        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        # Verify response
        assert result["complete"], "Should receive complete response"
        assert not result["timeout"], "Should not timeout"
        assert len(result["responses"]) == 1

        response = result["responses"][0]
        assert response["request_id"] == request_id
        assert response["agent_type"] == "DrugInteractionChecker"
        assert response["status"] == "success"

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_multi_agent_request(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Test multiple agents responding to related requests."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=20.0)

        # Publish multiple requests
        request_ids = publisher.publish_multi_agent_request(
            patient_id="test-patient-004",
            request_types=["medication", "symptom", "interaction"],
            parameters={
                "medication": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "2024-01-01T08:00:00",
                    "actual_time": "2024-01-01T10:00:00",
                },
                "symptom": {
                    "symptoms": ["fatigue", "nausea"],
                    "severity": "mild",
                    "duration_hours": 6.0,
                },
                "interaction": {
                    "current_medications": ["tacrolimus"],
                    "new_food": "grapefruit juice",
                },
            },
            patient_context={"transplant_type": "kidney"},
        )

        # Wait for all responses
        result = aggregator.wait_for_responses(
            request_ids=request_ids,
            expected_count=3,
        )

        # Verify all responses
        assert result["complete"], "Should receive all responses"
        assert not result["timeout"], "Should not timeout"
        assert len(result["responses"]) == 3, "Should receive 3 responses"

        # Verify all agent types present
        agent_types = {r["agent_type"] for r in result["responses"]}
        assert agent_types == {
            "MedicationAdvisor",
            "SymptomMonitor",
            "DrugInteractionChecker",
        }

        # Verify synthesis includes all agents
        synthesis = result["synthesis"]
        assert len(synthesis["agents_consulted"]) == 3
        assert synthesis["total_responses"] == 3

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_timeout_handling(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Test timeout handling when not all responses arrive."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=2.0)  # Short timeout

        # Publish request
        request_id = publisher.publish_medication_request(
            patient_id="test-patient-005",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T09:00:00",
        )

        # Wait for MORE responses than we'll get (to trigger timeout)
        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=5,  # Expect 5 but will only get 1
        )

        # Should timeout but still have partial response
        assert not result["complete"], "Should not be complete"
        assert result["timeout"], "Should timeout"
        assert len(result["responses"]) >= 1, "Should have at least one response"

        # Synthesis should indicate partial/timeout status
        synthesis = result["synthesis"]
        assert synthesis["status"] in ["partial", "timeout_partial"]

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_message_retry_on_nack(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Test message retry behavior when subscriber nacks."""
        # This test verifies Pub/Sub's built-in retry mechanism
        # We'll publish a request and verify it eventually succeeds
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish request
        request_id = publisher.publish_medication_request(
            patient_id="test-patient-006",
            medication_name="mycophenolate",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T08:30:00",
        )

        # Even if there are transient failures, should eventually succeed
        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        # Should eventually get response (Pub/Sub retries nacked messages)
        assert len(result["responses"]) >= 1, "Should receive response after retries"

        # Cleanup
        publisher.close()
        aggregator.close()

    def test_concurrent_requests(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Test handling multiple concurrent requests from different patients."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=20.0)

        # Publish multiple concurrent requests
        all_request_ids = []

        for i in range(3):
            request_ids = publisher.publish_multi_agent_request(
                patient_id=f"test-patient-concurrent-{i}",
                request_types=["medication", "symptom"],
                parameters={
                    "medication": {
                        "medication_name": "tacrolimus",
                        "scheduled_time": "2024-01-01T08:00:00",
                        "actual_time": f"2024-01-01T0{9+i}:00:00",
                    },
                    "symptom": {
                        "symptoms": ["fatigue"],
                        "severity": "mild",
                        "duration_hours": float(i + 1),
                    },
                },
            )
            all_request_ids.extend(request_ids)

        # Wait for all responses
        result = aggregator.wait_for_responses(
            request_ids=all_request_ids,
            expected_count=6,  # 3 patients × 2 requests each
        )

        # Verify all responses received
        assert result["complete"], "Should receive all responses"
        assert len(result["responses"]) == 6

        # Verify responses for different patients
        patient_ids = {r["patient_id"] for r in result["responses"]}
        assert len(patient_ids) == 3, "Should have responses from 3 different patients"

        # Cleanup
        publisher.close()
        aggregator.close()


@pytest.mark.integration
class TestPubSubPerformance:
    """Performance-related integration tests."""

    def test_end_to_end_latency(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Measure end-to-end latency for single request."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Measure time
        start_time = time.time()

        request_id = publisher.publish_medication_request(
            patient_id="test-patient-perf",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T09:00:00",
        )

        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        total_latency = time.time() - start_time

        # Verify reasonable latency (should be < 10 seconds for emulator)
        assert total_latency < 10.0, f"Latency too high: {total_latency:.2f}s"
        assert result["complete"], "Should complete successfully"

        # Log latency for benchmarking
        print(f"\nEnd-to-end latency: {total_latency:.3f}s")
        print(f"Agent processing time: {result['responses'][0]['processing_time']:.3f}s")

        # Cleanup
        publisher.close()
        aggregator.close()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-m", "integration"])
