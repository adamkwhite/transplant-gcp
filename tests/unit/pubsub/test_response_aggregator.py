"""Unit tests for ResponseAggregator."""

from unittest.mock import MagicMock, patch

from services.pubsub.response_aggregator import ResponseAggregator


class TestResponseAggregatorInit:
    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_init_creates_subscriber(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "projects/p/subscriptions/s"

        agg = ResponseAggregator(project_id="test-project", timeout_seconds=5.0)

        assert agg.project_id == "test-project"
        assert agg.timeout_seconds == 5.0
        assert agg.pending_requests == {}

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_close(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "projects/p/subscriptions/s"

        agg = ResponseAggregator()
        agg.close()

        mock_subscriber.close.assert_called_once()


class TestSynthesizeResponses:
    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_synthesize_no_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        result = agg._synthesize_responses([], complete=False, timeout=True)

        assert result["status"] == "error"
        assert "No responses" in result["message"]

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_synthesize_complete_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        responses = [
            {
                "agent_type": "MedicationAdvisor",
                "agent_response": {
                    "recommendation": "Take now",
                    "risk_level": "low",
                },
                "processing_time": 1.5,
            },
        ]

        result = agg._synthesize_responses(responses, complete=True, timeout=False)

        assert result["status"] == "complete"
        assert result["complete"] is True
        assert result["timeout"] is False
        assert "MedicationAdvisor" in result["agents_consulted"]
        assert result["total_responses"] == 1
        assert result["avg_processing_time"] == 1.5

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_synthesize_partial_timeout_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        responses = [
            {
                "agent_type": "SymptomMonitor",
                "agent_response": {
                    "urgency": "urgent",
                    "actions": ["Contact coordinator", "Monitor closely"],
                },
                "processing_time": 2.0,
            },
        ]

        result = agg._synthesize_responses(responses, complete=False, timeout=True)

        assert result["status"] == "timeout_partial"
        assert "WARNING" in result["recommendation"]

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_synthesize_drug_interaction_response(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        responses = [
            {
                "agent_type": "DrugInteractionChecker",
                "agent_response": {
                    "has_interaction": True,
                    "severity": "severe",
                    "recommendation": "Avoid combination",
                },
                "processing_time": 0.8,
            },
        ]

        result = agg._synthesize_responses(responses, complete=True, timeout=False)

        assert "DrugInteractionChecker" in result["agents_consulted"]
        assert (
            "severe" in result["recommendation"].lower() or "Severity" in result["recommendation"]
        )

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_synthesize_multi_agent_responses(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        responses = [
            {
                "agent_type": "MedicationAdvisor",
                "agent_response": {"recommendation": "Take now", "risk_level": "medium"},
                "processing_time": 1.0,
            },
            {
                "agent_type": "SymptomMonitor",
                "agent_response": {"urgency": "same_day", "actions": ["Monitor"]},
                "processing_time": 1.5,
            },
            {
                "agent_type": "DrugInteractionChecker",
                "agent_response": {
                    "has_interaction": False,
                    "severity": "none",
                    "recommendation": "No issues",
                },
                "processing_time": 0.5,
            },
        ]

        result = agg._synthesize_responses(responses, complete=True, timeout=False)

        assert len(result["agents_consulted"]) == 3
        assert result["total_responses"] == 3
        assert result["avg_processing_time"] == 1.0


class TestDeterminePriority:
    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_emergency_from_symptom_monitor(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"SymptomMonitor": {"urgency": "emergency"}}
        assert agg._determine_priority(recs) == "emergency"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_urgent_from_symptom_monitor(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"SymptomMonitor": {"urgency": "urgent"}}
        assert agg._determine_priority(recs) == "urgent"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_urgent_from_medication_critical_risk(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"MedicationAdvisor": {"risk_level": "critical"}}
        assert agg._determine_priority(recs) == "urgent"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_urgent_from_medication_high_risk(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"MedicationAdvisor": {"risk_level": "high"}}
        assert agg._determine_priority(recs) == "urgent"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_urgent_from_severe_interaction(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"DrugInteractionChecker": {"severity": "severe"}}
        assert agg._determine_priority(recs) == "urgent"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_urgent_from_contraindicated_interaction(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"DrugInteractionChecker": {"severity": "contraindicated"}}
        assert agg._determine_priority(recs) == "urgent"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_routine_from_low_risk(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        recs = {"MedicationAdvisor": {"risk_level": "low"}}
        assert agg._determine_priority(recs) == "routine"

    @patch("services.pubsub.response_aggregator.pubsub_v1")
    def test_information_from_empty_recommendations(self, mock_pubsub):
        mock_subscriber = MagicMock()
        mock_pubsub.SubscriberClient.return_value = mock_subscriber
        mock_subscriber.subscription_path.return_value = "path"

        agg = ResponseAggregator()
        assert agg._determine_priority({}) == "information"
