"""Tests for ResponseAggregator.wait_for_responses — the subscriber loop."""

import json
import threading
from unittest.mock import MagicMock, patch

from services.pubsub.response_aggregator import ResponseAggregator


def _make_response(request_id: str, agent_type: str) -> dict:
    return {
        "request_id": request_id,
        "agent_type": agent_type,
        "agent_response": {"recommendation": "test"},
        "processing_time": 0.5,
    }


class TestWaitForResponses:
    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_receives_all_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        captured_callback = {}

        def fake_subscribe(_path, callback):
            captured_callback["cb"] = callback
            future = MagicMock()

            def deliver():
                for rid, atype in [("r1", "MedicationAdvisor"), ("r2", "SymptomMonitor")]:
                    msg = MagicMock()
                    msg.data = json.dumps(_make_response(rid, atype)).encode("utf-8")
                    callback(msg)

            threading.Timer(0.05, deliver).start()
            return future

        mock_subscriber.subscribe.side_effect = fake_subscribe

        agg = ResponseAggregator(timeout_seconds=2.0)
        result = agg.wait_for_responses(
            request_ids=["r1", "r2"],
            expected_count=2,
        )

        assert result["complete"] is True
        assert result["timeout"] is False
        assert len(result["responses"]) == 2
        assert "synthesis" in result

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_timeout_with_partial_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        def fake_subscribe(_path, callback):
            msg = MagicMock()
            msg.data = json.dumps(_make_response("r1", "MedicationAdvisor")).encode("utf-8")
            threading.Timer(0.05, lambda: callback(msg)).start()
            return MagicMock()

        mock_subscriber.subscribe.side_effect = fake_subscribe

        agg = ResponseAggregator(timeout_seconds=0.3)
        result = agg.wait_for_responses(
            request_ids=["r1", "r2"],
            expected_count=2,
        )

        assert result["complete"] is False
        assert result["timeout"] is True
        assert len(result["responses"]) == 1

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_callback_invoked_per_response(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        def fake_subscribe(_path, callback):
            msg = MagicMock()
            msg.data = json.dumps(_make_response("r1", "MedicationAdvisor")).encode("utf-8")
            threading.Timer(0.05, lambda: callback(msg)).start()
            return MagicMock()

        mock_subscriber.subscribe.side_effect = fake_subscribe

        callback_results = []
        agg = ResponseAggregator(timeout_seconds=0.3)
        agg.wait_for_responses(
            request_ids=["r1"],
            expected_count=1,
            callback=lambda r: callback_results.append(r),
        )

        assert len(callback_results) == 1
        assert callback_results[0]["request_id"] == "r1"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_ignores_untracked_request_ids(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        def fake_subscribe(_path, callback):
            def deliver():
                untracked = MagicMock()
                untracked.data = json.dumps(_make_response("unknown", "X")).encode("utf-8")
                callback(untracked)

                tracked = MagicMock()
                tracked.data = json.dumps(_make_response("r1", "Med")).encode("utf-8")
                callback(tracked)

            threading.Timer(0.05, deliver).start()
            return MagicMock()

        mock_subscriber.subscribe.side_effect = fake_subscribe

        agg = ResponseAggregator(timeout_seconds=0.5)
        result = agg.wait_for_responses(request_ids=["r1"], expected_count=1)

        assert len(result["responses"]) == 1
        assert result["responses"][0]["request_id"] == "r1"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_handles_malformed_message(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        def fake_subscribe(_path, callback):
            def deliver():
                bad = MagicMock()
                bad.data = b"not json"
                callback(bad)

            threading.Timer(0.05, deliver).start()
            return MagicMock()

        mock_subscriber.subscribe.side_effect = fake_subscribe

        agg = ResponseAggregator(timeout_seconds=0.3)
        result = agg.wait_for_responses(request_ids=["r1"], expected_count=1)

        assert result["timeout"] is True
        assert len(result["responses"]) == 0

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_timeout_no_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"
        mock_subscriber.subscribe.return_value = MagicMock()

        agg = ResponseAggregator(timeout_seconds=0.1)
        result = agg.wait_for_responses(request_ids=["r1"], expected_count=1)

        assert result["complete"] is False
        assert result["timeout"] is True
        assert result["synthesis"]["status"] == "error"
