"""Unit tests for CoordinatorPublisher."""

import json
from unittest.mock import MagicMock, patch

from services.pubsub.coordinator_publisher import CoordinatorPublisher


class TestCoordinatorPublisher:
    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_init_creates_publisher_and_topics(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"

        pub = CoordinatorPublisher(project_id="test-project")

        assert pub.project_id == "test-project"
        assert pub.medication_topic == "projects/test-project/topics/medication-requests"
        assert pub.symptom_topic == "projects/test-project/topics/symptom-requests"
        assert pub.interaction_topic == "projects/test-project/topics/interaction-requests"

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_medication_request(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-123"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_id = pub.publish_medication_request(
            patient_id="P1",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T10:00:00",
            patient_context={"transplant_type": "kidney"},
        )

        assert request_id is not None
        mock_publisher.publish.assert_called_once()
        call_args = mock_publisher.publish.call_args
        data = json.loads(call_args[0][1].decode("utf-8"))
        assert data["patient_id"] == "P1"
        assert data["request_type"] == "medication_advice"
        assert data["parameters"]["medication_name"] == "tacrolimus"

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_symptom_request(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-456"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_id = pub.publish_symptom_request(
            patient_id="P2",
            symptoms=["fever", "fatigue"],
            severity="moderate",
            duration_hours=12.0,
        )

        assert request_id is not None
        call_args = mock_publisher.publish.call_args
        data = json.loads(call_args[0][1].decode("utf-8"))
        assert data["request_type"] == "symptom_check"
        assert data["parameters"]["symptoms"] == ["fever", "fatigue"]
        assert data["parameters"]["severity"] == "moderate"
        assert data["parameters"]["duration_hours"] == 12.0

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_interaction_request(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-789"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_id = pub.publish_interaction_request(
            patient_id="P3",
            current_medications=["tacrolimus", "mycophenolate"],
            new_medication="ibuprofen",
        )

        assert request_id is not None
        call_args = mock_publisher.publish.call_args
        data = json.loads(call_args[0][1].decode("utf-8"))
        assert data["request_type"] == "interaction_check"
        assert data["parameters"]["current_medications"] == ["tacrolimus", "mycophenolate"]
        assert data["parameters"]["new_medication"] == "ibuprofen"

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_interaction_request_with_food_and_supplement(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-abc"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_id = pub.publish_interaction_request(
            patient_id="P4",
            current_medications=["tacrolimus"],
            new_food="grapefruit",
            new_supplement="vitamin D",
        )

        assert request_id is not None
        call_args = mock_publisher.publish.call_args
        data = json.loads(call_args[0][1].decode("utf-8"))
        assert data["parameters"]["new_food"] == "grapefruit"
        assert data["parameters"]["new_supplement"] == "vitamin D"

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_multi_agent_request(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-multi"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_ids = pub.publish_multi_agent_request(
            patient_id="P5",
            request_types=["medication", "symptom", "interaction"],
            parameters={
                "medication": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "08:00",
                    "actual_time": "12:00",
                },
                "symptom": {
                    "symptoms": ["fever"],
                    "severity": "moderate",
                    "duration_hours": 6,
                },
                "interaction": {
                    "current_medications": ["tacrolimus"],
                    "new_medication": "ibuprofen",
                },
            },
        )

        assert len(request_ids) == 3
        assert mock_publisher.publish.call_count == 3

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_multi_agent_request_partial(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-partial"
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()
        request_ids = pub.publish_multi_agent_request(
            patient_id="P6",
            request_types=["medication"],
            parameters={
                "medication": {
                    "medication_name": "prednisone",
                    "scheduled_time": "09:00",
                    "actual_time": "15:00",
                },
            },
        )

        assert len(request_ids) == 1

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_publish_message_failure_raises(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Publish failed")
        mock_publisher.publish.return_value = mock_future

        pub = CoordinatorPublisher()

        import pytest

        with pytest.raises(Exception, match="Publish failed"):
            pub.publish_medication_request(
                patient_id="P1",
                medication_name="tacrolimus",
                scheduled_time="08:00",
                actual_time="10:00",
            )

    @patch("services.pubsub.coordinator_publisher.pubsub_v1")
    def test_close(self, mock_pubsub):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.side_effect = lambda p, t: f"projects/{p}/topics/{t}"

        pub = CoordinatorPublisher()
        pub.close()

        mock_publisher.stop.assert_called_once()
