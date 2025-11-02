"""
Integration Tests for Pub/Sub Error Handling

Tests error scenarios, edge cases, and failure modes in the Pub/Sub communication system.
"""

import json
import os
import time
from typing import Any
from unittest.mock import MagicMock, patch

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
class TestPubSubErrorHandling:
    """Integration tests for error handling in Pub/Sub communication."""

    def test_malformed_message_handling(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test handling of malformed messages in medication subscriber."""
        # Create publisher and send malformed message directly
        publisher_client = pubsub_v1.PublisherClient()
        topic_path = publisher_client.topic_path(
            "transplant-pubsub-emulator", "medication-requests"
        )

        # Send invalid JSON
        invalid_message = b"not valid json"
        future = publisher_client.publish(topic_path, invalid_message)
        future.result(timeout=5.0)

        # Give subscriber time to process and nack
        time.sleep(1)

        # Should not crash - message will be nacked and retried
        # We can't easily verify the nack without more infrastructure,
        # but we verify the system remains responsive
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        request_id = publisher.publish_medication_request(
            patient_id="test-patient-malformed",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T09:00:00",
        )

        result = aggregator.wait_for_responses(request_ids=[request_id], expected_count=1)

        # Should still process valid messages
        assert result["complete"]
        assert len(result["responses"]) == 1

        publisher.close()
        aggregator.close()

    def test_missing_required_fields(self, ensure_emulator: None, subscriber_thread: None) -> None:
        """Test handling of messages with missing required fields."""
        publisher_client = pubsub_v1.PublisherClient()
        topic_path = publisher_client.topic_path("transplant-pubsub-emulator", "symptom-requests")

        # Send message missing required fields
        incomplete_message = json.dumps(
            {
                "request_id": "test-incomplete",
                # Missing patient_id, parameters, etc.
            }
        ).encode("utf-8")

        future = publisher_client.publish(topic_path, incomplete_message)
        future.result(timeout=5.0)

        time.sleep(1)

        # Verify system still works after error
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        request_id = publisher.publish_symptom_request(
            patient_id="test-patient-incomplete",
            symptoms=["fever"],
            severity="mild",
            duration_hours=1.0,
        )

        result = aggregator.wait_for_responses(request_ids=[request_id], expected_count=1)
        assert result["complete"]

        publisher.close()
        aggregator.close()

    def test_empty_response_synthesis(self, ensure_emulator: None) -> None:
        """Test synthesis with no responses (timeout with no partial responses)."""
        aggregator = ResponseAggregator(timeout_seconds=1.0)

        # Wait for responses that will never come (using non-existent request IDs)
        result = aggregator.wait_for_responses(
            request_ids=["fake-request-1", "fake-request-2"], expected_count=2
        )

        # Should timeout with no responses
        assert not result["complete"]
        assert result["timeout"]
        assert len(result["responses"]) == 0

        # Synthesis should handle empty responses gracefully
        synthesis = result["synthesis"]
        assert synthesis["status"] == "error"
        assert "No responses received" in synthesis["message"]
        assert "contact your transplant team" in synthesis["recommendation"]

        aggregator.close()

    def test_response_callback_invocation(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test that response callbacks are invoked correctly."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Track callback invocations
        callback_responses = []

        def response_callback(response: dict[str, Any]) -> None:
            """Capture responses in callback."""
            callback_responses.append(response)

        # Publish request
        request_id = publisher.publish_medication_request(
            patient_id="test-patient-callback",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T09:00:00",
        )

        # Wait with callback
        result = aggregator.wait_for_responses(
            request_ids=[request_id], expected_count=1, callback=response_callback
        )

        # Verify callback was invoked
        assert len(callback_responses) == 1
        assert callback_responses[0]["request_id"] == request_id
        assert callback_responses[0]["agent_type"] == "MedicationAdvisor"

        # Verify result also contains the response
        assert result["complete"]
        assert len(result["responses"]) == 1

        publisher.close()
        aggregator.close()

    def test_publish_response_failure_handling(self, ensure_emulator: None) -> None:
        """Test handling of publish failures in response aggregator."""
        subscribers = SpecialistSubscribers()

        # Mock the publisher to simulate failure
        with patch.object(subscribers.publisher, "publish") as mock_publish:
            # Make publish raise an exception
            mock_future = MagicMock()
            mock_future.result.side_effect = Exception("Simulated publish failure")
            mock_publish.return_value = mock_future

            # Attempt to publish response should raise
            response_data = {
                "request_id": "test-123",
                "agent_type": "Test",
                "status": "success",
            }

            with pytest.raises(Exception) as exc_info:
                subscribers._publish_response(response_data)

            assert "Simulated publish failure" in str(exc_info.value)

        subscribers.close()

    def test_priority_determination_edge_cases(self, ensure_emulator: None) -> None:
        """Test priority determination with various agent response combinations."""
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Test empty recommendations -> information priority
        priority = aggregator._determine_priority({})
        assert priority == "information"

        # Test only medication with low risk -> routine
        priority = aggregator._determine_priority({"MedicationAdvisor": {"risk_level": "low"}})
        assert priority == "routine"

        # Test high risk medication -> urgent
        priority = aggregator._determine_priority({"MedicationAdvisor": {"risk_level": "high"}})
        assert priority == "urgent"

        # Test critical risk medication -> urgent
        priority = aggregator._determine_priority({"MedicationAdvisor": {"risk_level": "critical"}})
        assert priority == "urgent"

        # Test emergency symptom urgency -> emergency
        priority = aggregator._determine_priority({"SymptomMonitor": {"urgency": "emergency"}})
        assert priority == "emergency"

        # Test urgent symptom urgency -> urgent
        priority = aggregator._determine_priority({"SymptomMonitor": {"urgency": "urgent"}})
        assert priority == "urgent"

        # Test severe interaction -> urgent
        priority = aggregator._determine_priority(
            {"DrugInteractionChecker": {"severity": "severe"}}
        )
        assert priority == "urgent"

        # Test contraindicated interaction -> urgent
        priority = aggregator._determine_priority(
            {"DrugInteractionChecker": {"severity": "contraindicated"}}
        )
        assert priority == "urgent"

        # Test symptom urgency overrides medication risk
        priority = aggregator._determine_priority(
            {
                "MedicationAdvisor": {"risk_level": "low"},
                "SymptomMonitor": {"urgency": "emergency"},
            }
        )
        assert priority == "emergency"

        aggregator.close()

    def test_drug_interaction_with_supplements(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test drug interaction check with supplements instead of medications."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish interaction request with supplement
        request_id = publisher.publish_interaction_request(
            patient_id="test-patient-supplement",
            current_medications=["tacrolimus"],
            new_supplement="St. John's Wort",
            patient_context={"transplant_type": "kidney"},
        )

        result = aggregator.wait_for_responses(request_ids=[request_id], expected_count=1)

        # Verify response
        assert result["complete"]
        assert len(result["responses"]) == 1
        assert result["responses"][0]["agent_type"] == "DrugInteractionChecker"

        publisher.close()
        aggregator.close()

    def test_drug_interaction_with_food(
        self, ensure_emulator: None, subscriber_thread: None
    ) -> None:
        """Test drug interaction check with food items."""
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Publish interaction request with food
        request_id = publisher.publish_interaction_request(
            patient_id="test-patient-food",
            current_medications=["tacrolimus"],
            new_food="grapefruit",
            patient_context={"transplant_type": "kidney"},
        )

        result = aggregator.wait_for_responses(request_ids=[request_id], expected_count=1)

        # Verify response
        assert result["complete"]
        assert len(result["responses"]) == 1
        assert result["responses"][0]["agent_type"] == "DrugInteractionChecker"

        publisher.close()
        aggregator.close()

    def test_standalone_callback_functions(self, ensure_emulator: None) -> None:
        """Test standalone callback wrapper functions for subscribers."""
        from services.pubsub import specialist_subscribers

        # Create a mock message
        mock_message = MagicMock()
        mock_message.data = json.dumps(
            {
                "request_id": "test-callback-123",
                "patient_id": "test-patient",
                "request_type": "medication_advice",
                "parameters": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "2024-01-01T08:00:00",
                    "actual_time": "2024-01-01T09:00:00",
                },
                "patient_context": {},
            }
        ).encode("utf-8")
        mock_message.ack = MagicMock()

        # Test medication request callback
        specialist_subscribers.on_medication_request(mock_message)
        mock_message.ack.assert_called_once()

        # Reset mock
        mock_message.ack.reset_mock()
        mock_message.data = json.dumps(
            {
                "request_id": "test-callback-456",
                "patient_id": "test-patient",
                "request_type": "symptom_analysis",
                "parameters": {
                    "symptoms": ["fever"],
                    "severity": "mild",
                    "duration_hours": 1.0,
                },
                "patient_context": {},
            }
        ).encode("utf-8")

        # Test symptom request callback
        specialist_subscribers.on_symptom_request(mock_message)
        mock_message.ack.assert_called_once()

        # Reset mock
        mock_message.ack.reset_mock()
        mock_message.data = json.dumps(
            {
                "request_id": "test-callback-789",
                "patient_id": "test-patient",
                "request_type": "interaction_check",
                "parameters": {
                    "current_medications": ["tacrolimus"],
                    "new_medication": "ibuprofen",
                },
                "patient_context": {},
            }
        ).encode("utf-8")

        # Test drug interaction request callback
        specialist_subscribers.on_drug_interaction_request(mock_message)
        mock_message.ack.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
