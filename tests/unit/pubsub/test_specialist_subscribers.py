"""Unit tests for SpecialistSubscribers."""

import json
from unittest.mock import MagicMock, patch

import pytest

from services.pubsub.specialist_subscribers import SpecialistSubscribers


def _make_message(data: dict) -> MagicMock:
    """Create a mock Pub/Sub message."""
    msg = MagicMock()
    msg.data = json.dumps(data).encode("utf-8")
    return msg


@pytest.fixture
def subscribers():
    with (
        patch("services.pubsub.specialist_subscribers.pubsub_v1") as mock_pubsub,
        patch("services.pubsub.specialist_subscribers.MedicationAdvisorAgent") as mock_med,
        patch("services.pubsub.specialist_subscribers.SymptomMonitorAgent") as mock_sym,
        patch("services.pubsub.specialist_subscribers.DrugInteractionCheckerAgent") as mock_drug,
        patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}),
    ):
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.return_value = "projects/p/topics/t"
        mock_future = MagicMock()
        mock_future.result.return_value = "msg-id"
        mock_publisher.publish.return_value = mock_future

        subs = SpecialistSubscribers()
        yield subs


class TestSpecialistSubscribersInit:
    def test_init_requires_api_key(self):
        with (
            patch("services.pubsub.specialist_subscribers.pubsub_v1"),
            patch("services.pubsub.specialist_subscribers.MedicationAdvisorAgent"),
            patch("services.pubsub.specialist_subscribers.SymptomMonitorAgent"),
            patch("services.pubsub.specialist_subscribers.DrugInteractionCheckerAgent"),
            patch.dict("os.environ", {}, clear=True),
            patch("services.pubsub.specialist_subscribers.os.environ.get", return_value=None),
            pytest.raises(ValueError, match="GEMINI_API_KEY"),
        ):
            SpecialistSubscribers()


class TestOnMedicationRequest:
    def test_processes_medication_request(self, subscribers):
        subscribers.medication_advisor.analyze_missed_dose.return_value = {
            "recommendation": "Take now",
            "risk_level": "low",
        }

        message = _make_message(
            {
                "request_id": "req-001",
                "patient_id": "P1",
                "request_type": "medication_advice",
                "parameters": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "08:00",
                    "actual_time": "12:00",
                },
                "patient_context": {"transplant_type": "kidney"},
            }
        )

        subscribers.on_medication_request(message)

        message.ack.assert_called_once()
        subscribers.medication_advisor.analyze_missed_dose.assert_called_once()

    def test_publishes_response(self, subscribers):
        subscribers.medication_advisor.analyze_missed_dose.return_value = {
            "recommendation": "Take now",
        }

        message = _make_message(
            {
                "request_id": "req-002",
                "patient_id": "P2",
                "parameters": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "08:00",
                    "actual_time": "12:00",
                },
            }
        )

        subscribers.on_medication_request(message)

        # Verify response was published
        publisher = subscribers.publisher
        publisher.publish.assert_called_once()
        call_args = publisher.publish.call_args
        response_data = json.loads(call_args[0][1].decode("utf-8"))
        assert response_data["agent_type"] == "MedicationAdvisor"
        assert response_data["status"] == "success"

    def test_handles_error_gracefully(self, subscribers):
        subscribers.medication_advisor.analyze_missed_dose.side_effect = Exception("Agent error")

        message = _make_message(
            {
                "request_id": "req-err",
                "patient_id": "P1",
                "parameters": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "08:00",
                    "actual_time": "12:00",
                },
            }
        )

        subscribers.on_medication_request(message)

        message.nack.assert_called_once()


class TestOnSymptomRequest:
    def test_processes_symptom_request(self, subscribers):
        subscribers.symptom_monitor.analyze_symptoms.return_value = {
            "rejection_risk": "moderate",
            "urgency": "same_day",
        }

        message = _make_message(
            {
                "request_id": "req-sym-001",
                "patient_id": "P3",
                "request_type": "symptom_check",
                "parameters": {
                    "symptoms": ["fever", "fatigue"],
                    "severity": "moderate",
                },
                "patient_context": {"transplant_type": "kidney"},
            }
        )

        subscribers.on_symptom_request(message)

        message.ack.assert_called_once()
        subscribers.symptom_monitor.analyze_symptoms.assert_called_once()

    def test_handles_error_gracefully(self, subscribers):
        subscribers.symptom_monitor.analyze_symptoms.side_effect = Exception("Agent error")

        message = _make_message(
            {
                "request_id": "req-sym-err",
                "patient_id": "P3",
                "parameters": {"symptoms": ["fever"]},
            }
        )

        subscribers.on_symptom_request(message)

        message.nack.assert_called_once()


class TestOnDrugInteractionRequest:
    def test_processes_interaction_request(self, subscribers):
        subscribers.drug_interaction_checker.check_interaction.return_value = {
            "has_interaction": True,
            "severity": "severe",
        }

        message = _make_message(
            {
                "request_id": "req-int-001",
                "patient_id": "P4",
                "request_type": "interaction_check",
                "parameters": {
                    "current_medications": ["tacrolimus"],
                    "new_medication": "ibuprofen",
                },
            }
        )

        subscribers.on_drug_interaction_request(message)

        message.ack.assert_called_once()
        subscribers.drug_interaction_checker.check_interaction.assert_called_once()

    def test_processes_food_interaction(self, subscribers):
        subscribers.drug_interaction_checker.check_interaction.return_value = {
            "has_interaction": True,
        }

        message = _make_message(
            {
                "request_id": "req-int-002",
                "patient_id": "P5",
                "parameters": {
                    "current_medications": ["tacrolimus"],
                    "new_food": "grapefruit",
                },
            }
        )

        subscribers.on_drug_interaction_request(message)

        call_args = subscribers.drug_interaction_checker.check_interaction.call_args
        assert call_args[1]["foods"] == ["grapefruit"]

    def test_processes_supplement_interaction(self, subscribers):
        subscribers.drug_interaction_checker.check_interaction.return_value = {
            "has_interaction": True,
        }

        message = _make_message(
            {
                "request_id": "req-int-003",
                "patient_id": "P6",
                "parameters": {
                    "current_medications": ["tacrolimus"],
                    "new_supplement": "St. John's Wort",
                },
            }
        )

        subscribers.on_drug_interaction_request(message)

        call_args = subscribers.drug_interaction_checker.check_interaction.call_args
        assert call_args[1]["supplements"] == ["St. John's Wort"]

    def test_handles_error_gracefully(self, subscribers):
        subscribers.drug_interaction_checker.check_interaction.side_effect = Exception("error")

        message = _make_message(
            {
                "request_id": "req-int-err",
                "patient_id": "P4",
                "parameters": {"current_medications": ["tacrolimus"]},
            }
        )

        subscribers.on_drug_interaction_request(message)

        message.nack.assert_called_once()


class TestClose:
    def test_close_stops_publisher(self, subscribers):
        subscribers.close()
        subscribers.publisher.stop.assert_called_once()
