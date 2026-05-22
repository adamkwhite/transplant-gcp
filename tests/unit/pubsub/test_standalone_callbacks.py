"""Tests for specialist_subscribers standalone functions and _publish_error_response."""

import json
from unittest.mock import MagicMock, patch

from services.pubsub.specialist_subscribers import (
    on_drug_interaction_request,
    on_medication_request,
    on_symptom_request,
)


class TestPublishErrorResponse:
    def test_publish_error_response(self):
        with (
            patch("services.pubsub.specialist_subscribers.pubsub_v1") as mock_pubsub,
            patch("services.pubsub.specialist_subscribers.MedicationAdvisorAgent"),
            patch("services.pubsub.specialist_subscribers.SymptomMonitorAgent"),
            patch("services.pubsub.specialist_subscribers.DrugInteractionCheckerAgent"),
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
        ):
            mock_publisher = MagicMock()
            mock_pubsub.PublisherClient.return_value = mock_publisher
            mock_publisher.topic_path.return_value = "path"
            mock_future = MagicMock()
            mock_future.result.return_value = "id"
            mock_publisher.publish.return_value = mock_future

            from services.pubsub.specialist_subscribers import SpecialistSubscribers

            subs = SpecialistSubscribers()
            subs._publish_error_response(
                {"request_id": "err-1", "patient_id": "P1"}, "Something broke"
            )

            call_args = mock_publisher.publish.call_args
            data = json.loads(call_args[0][1].decode("utf-8"))
            assert data["agent_type"] == "Error"
            assert data["status"] == "error"
            assert data["agent_response"]["error"] == "Something broke"


class TestPublishResponseException:
    def test_publish_response_reraises_on_future_failure(self):
        with (
            patch("services.pubsub.specialist_subscribers.pubsub_v1") as mock_pubsub,
            patch("services.pubsub.specialist_subscribers.MedicationAdvisorAgent"),
            patch("services.pubsub.specialist_subscribers.SymptomMonitorAgent"),
            patch("services.pubsub.specialist_subscribers.DrugInteractionCheckerAgent"),
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
        ):
            mock_publisher = MagicMock()
            mock_pubsub.PublisherClient.return_value = mock_publisher
            mock_publisher.topic_path.return_value = "path"
            mock_future = MagicMock()
            mock_future.result.side_effect = RuntimeError("Publish failed")
            mock_publisher.publish.return_value = mock_future

            from services.pubsub.specialist_subscribers import SpecialistSubscribers

            subs = SpecialistSubscribers()
            import pytest

            with pytest.raises(RuntimeError, match="Publish failed"):
                subs._publish_response({"request_id": "r1", "agent_type": "Test", "data": "x"})


class TestGetSpecialistSubscribersSingleton:
    def test_creates_singleton_when_none(self):
        with (
            patch("services.pubsub.specialist_subscribers.pubsub_v1") as mock_pubsub,
            patch("services.pubsub.specialist_subscribers.MedicationAdvisorAgent"),
            patch("services.pubsub.specialist_subscribers.SymptomMonitorAgent"),
            patch("services.pubsub.specialist_subscribers.DrugInteractionCheckerAgent"),
            patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
        ):
            mock_publisher = MagicMock()
            mock_pubsub.PublisherClient.return_value = mock_publisher
            mock_publisher.topic_path.return_value = "path"

            import services.pubsub.specialist_subscribers as mod

            mod._specialist_subscribers = None
            result = mod.get_specialist_subscribers()
            assert result is not None
            assert isinstance(result, mod.SpecialistSubscribers)
            mod._specialist_subscribers = None


class TestStandaloneCallbacks:
    @patch("services.pubsub.specialist_subscribers._specialist_subscribers")
    @patch("services.pubsub.specialist_subscribers.get_specialist_subscribers")
    def test_on_medication_request_delegates(self, mock_get, mock_singleton):
        mock_subs = MagicMock()
        mock_get.return_value = mock_subs
        msg = MagicMock()

        on_medication_request(msg)

        mock_subs.on_medication_request.assert_called_once_with(msg)

    @patch("services.pubsub.specialist_subscribers._specialist_subscribers")
    @patch("services.pubsub.specialist_subscribers.get_specialist_subscribers")
    def test_on_symptom_request_delegates(self, mock_get, mock_singleton):
        mock_subs = MagicMock()
        mock_get.return_value = mock_subs
        msg = MagicMock()

        on_symptom_request(msg)

        mock_subs.on_symptom_request.assert_called_once_with(msg)

    @patch("services.pubsub.specialist_subscribers._specialist_subscribers")
    @patch("services.pubsub.specialist_subscribers.get_specialist_subscribers")
    def test_on_drug_interaction_request_delegates(self, mock_get, mock_singleton):
        mock_subs = MagicMock()
        mock_get.return_value = mock_subs
        msg = MagicMock()

        on_drug_interaction_request(msg)

        mock_subs.on_drug_interaction_request.assert_called_once_with(msg)
