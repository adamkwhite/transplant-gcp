"""
Response Aggregator for Pub/Sub Communication

Coordinates responses from multiple specialist agents and synthesizes final answers.
Implements timeout handling for partial response scenarios.
"""

import json
import os
import threading
import time
from typing import Any

from google.cloud import pubsub_v1  # type: ignore[attr-defined]


class ResponseAggregator:
    """
    Aggregates responses from specialist agents and synthesizes final recommendations.

    The aggregator:
    1. Subscribes to coordinator-responses topic
    2. Tracks responses by request_id
    3. Waits for all expected responses or timeout (10 seconds)
    4. Synthesizes final answer from available responses
    """

    def __init__(
        self,
        project_id: str = "transplant-pubsub-emulator",
        timeout_seconds: float = 10.0,
    ):
        """
        Initialize the response aggregator.

        Args:
            project_id: GCP project ID (use emulator default for local dev)
            timeout_seconds: Max time to wait for all responses (default: 10.0)
        """
        self.project_id = project_id
        self.timeout_seconds = timeout_seconds

        # Create subscriber client
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, "coordinator-responses-sub"
        )

        # Response tracking
        self.pending_requests: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()

    def wait_for_responses(
        self,
        request_ids: list[str],
        expected_count: int,
        callback: Any = None,
    ) -> dict[str, Any]:
        """
        Wait for responses from specialist agents.

        Args:
            request_ids: List of request IDs to track
            expected_count: Number of responses expected
            callback: Optional callback to invoke with each response

        Returns:
            Dict with:
                - responses: List of agent responses received
                - complete: Whether all expected responses received
                - timeout: Whether timeout occurred
                - synthesis: Final synthesized recommendation
        """
        # Initialize tracking for these requests
        with self.lock:
            for request_id in request_ids:
                self.pending_requests[request_id] = {
                    "request_id": request_id,
                    "received": False,
                    "response": None,
                    "timestamp": None,
                }

        # Start subscriber thread
        responses_received = []
        stop_event = threading.Event()

        def message_callback(message: pubsub_v1.subscriber.message.Message) -> None:
            """Process incoming response messages."""
            try:
                response_data = json.loads(message.data.decode("utf-8"))
                request_id = response_data["request_id"]

                # Check if this is a request we're tracking
                with self.lock:
                    if request_id in self.pending_requests:
                        self.pending_requests[request_id]["received"] = True
                        self.pending_requests[request_id]["response"] = response_data
                        self.pending_requests[request_id]["timestamp"] = time.time()
                        responses_received.append(response_data)

                        # Invoke callback if provided
                        if callback:
                            callback(response_data)

                        # Check if we have all responses
                        if len(responses_received) >= expected_count:
                            stop_event.set()

                message.ack()

            except Exception as e:
                print(f"Error processing response: {e}")
                message.nack()

        # Subscribe to responses
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path, callback=message_callback
        )

        print(f"Waiting for {expected_count} responses (timeout: {self.timeout_seconds}s)...")

        # Wait for responses or timeout
        start_time = time.time()
        timed_out = not stop_event.wait(timeout=self.timeout_seconds)
        elapsed_time = time.time() - start_time

        # Cancel subscription
        import contextlib

        streaming_pull_future.cancel()
        with contextlib.suppress(Exception):
            streaming_pull_future.result(timeout=1.0)

        # Gather results
        complete = len(responses_received) >= expected_count
        timeout = timed_out and not complete

        print(
            f"Received {len(responses_received)}/{expected_count} responses in {elapsed_time:.2f}s"
        )
        if timeout:
            print("WARNING: Timeout occurred - synthesizing with partial responses")

        # Synthesize final response
        synthesis = self._synthesize_responses(responses_received, complete, timeout)

        return {
            "responses": responses_received,
            "complete": complete,
            "timeout": timeout,
            "elapsed_time": elapsed_time,
            "synthesis": synthesis,
        }

    def _synthesize_responses(
        self,
        responses: list[dict[str, Any]],
        complete: bool,
        timeout: bool,
    ) -> dict[str, Any]:
        """
        Synthesize final recommendation from specialist responses.

        Args:
            responses: List of specialist agent responses
            complete: Whether all expected responses received
            timeout: Whether timeout occurred

        Returns:
            Synthesized recommendation combining all specialist advice
        """
        if not responses:
            return {
                "status": "error",
                "message": "No responses received from specialist agents",
                "recommendation": "Unable to provide guidance - please contact your transplant team",
            }

        # Determine overall status
        status = "complete" if complete else "partial"
        if timeout:
            status = "timeout_partial"

        # Extract agent responses
        agent_recommendations = {}
        agent_types = []
        processing_times = []

        for response in responses:
            agent_type = response.get("agent_type", "Unknown")
            agent_types.append(agent_type)
            agent_recommendations[agent_type] = response.get("agent_response", {})
            processing_times.append(response.get("processing_time", 0.0))

        # Synthesize comprehensive recommendation
        synthesis = {
            "status": status,
            "agents_consulted": agent_types,
            "complete": complete,
            "timeout": timeout,
            "agent_recommendations": agent_recommendations,
            "avg_processing_time": sum(processing_times) / len(processing_times)
            if processing_times
            else 0.0,
            "total_responses": len(responses),
        }

        # Build synthesized recommendation text
        recommendation_parts = []

        # Add timeout warning if applicable
        if timeout:
            recommendation_parts.append(
                "⚠️ WARNING: Not all specialist agents responded within the timeout period. "
                "This recommendation is based on partial information."
            )

        # Add each agent's recommendation
        for agent_type, agent_response in agent_recommendations.items():
            if agent_type == "MedicationAdvisor":
                rec = agent_response.get("recommendation", "No recommendation available")
                risk = agent_response.get("risk_level", "unknown")
                recommendation_parts.append(f"\n**Medication Advisor** (Risk: {risk}):\n{rec}")

            elif agent_type == "SymptomMonitor":
                urgency = agent_response.get("urgency", "unknown")
                actions = agent_response.get("actions", [])
                recommendation_parts.append(
                    f"\n**Symptom Monitor** (Urgency: {urgency}):\n"
                    + "\n".join(f"- {action}" for action in actions)
                )

            elif agent_type == "DrugInteractionChecker":
                has_interaction = agent_response.get("has_interaction", False)
                severity = agent_response.get("severity", "unknown")
                recommendation = agent_response.get("recommendation", "")
                recommendation_parts.append(
                    f"\n**Drug Interaction Checker** (Severity: {severity}):\n"
                    f"Interaction detected: {has_interaction}\n{recommendation}"
                )

        synthesis["recommendation"] = "\n".join(recommendation_parts)

        # Determine highest priority action
        synthesis["priority"] = self._determine_priority(agent_recommendations)

        return synthesis

    def _determine_priority(self, agent_recommendations: dict[str, Any]) -> str:
        """
        Determine highest priority action based on agent responses.

        Args:
            agent_recommendations: Dict of agent responses

        Returns:
            Priority level: "emergency", "urgent", "routine", or "information"
        """
        # Check symptom monitor urgency
        symptom_response = agent_recommendations.get("SymptomMonitor", {})
        urgency: str = symptom_response.get("urgency", "")  # type: ignore[assignment]
        if urgency in ["emergency", "urgent"]:
            return str(urgency)

        # Check medication risk level
        medication_response = agent_recommendations.get("MedicationAdvisor", {})
        risk_level: str = medication_response.get("risk_level", "")  # type: ignore[assignment]
        if risk_level in ["critical", "high"]:
            return "urgent"

        # Check interaction severity
        interaction_response = agent_recommendations.get("DrugInteractionChecker", {})
        severity: str = interaction_response.get("severity", "")  # type: ignore[assignment]
        if severity in ["severe", "contraindicated"]:
            return "urgent"

        # Default to routine
        return "routine" if agent_recommendations else "information"

    def close(self) -> None:
        """Close the subscriber client."""
        self.subscriber.close()


# Convenience function for testing
def main() -> None:
    """Test the response aggregator with the emulator."""

    # Ensure emulator is being used
    if "PUBSUB_EMULATOR_HOST" not in os.environ:
        print("WARNING: PUBSUB_EMULATOR_HOST not set. Using live Pub/Sub.")
        print("Set export PUBSUB_EMULATOR_HOST=localhost:8085 to use emulator")

    # Import publisher to send test requests
    from services.pubsub.coordinator_publisher import CoordinatorPublisher

    # Create publisher and aggregator
    publisher = CoordinatorPublisher()
    aggregator = ResponseAggregator(timeout_seconds=15.0)

    print("Starting response aggregator test...")
    print("Make sure specialist subscribers are running!")
    print("Run: python services/pubsub/specialist_subscribers.py\n")

    # Publish test requests
    print("Publishing test requests...")
    request_ids = []

    # Medication request
    med_id = publisher.publish_medication_request(
        patient_id="test-patient-123",
        medication_name="tacrolimus",
        scheduled_time="2024-01-01T08:00:00",
        actual_time="2024-01-01T12:00:00",
        patient_context={"transplant_type": "kidney", "days_post_transplant": 30},
    )
    request_ids.append(med_id)

    # Symptom request
    symp_id = publisher.publish_symptom_request(
        patient_id="test-patient-123",
        symptoms=["fever", "decreased urine output"],
        severity="moderate",
        duration_hours=24.0,
        patient_context={"transplant_type": "kidney"},
    )
    request_ids.append(symp_id)

    # Interaction request
    int_id = publisher.publish_interaction_request(
        patient_id="test-patient-123",
        current_medications=["tacrolimus", "mycophenolate"],
        new_medication="ibuprofen",
        patient_context={"transplant_type": "kidney"},
    )
    request_ids.append(int_id)

    print(f"Published {len(request_ids)} requests: {request_ids}\n")

    # Wait for responses
    def response_callback(response: dict[str, Any]) -> None:
        """Print each response as it arrives."""
        print(
            f"✓ Received response from {response['agent_type']} ({response['processing_time']:.2f}s)"
        )

    result = aggregator.wait_for_responses(
        request_ids=request_ids,
        expected_count=3,
        callback=response_callback,
    )

    # Print results
    print("\n" + "=" * 80)
    print("AGGREGATION RESULTS")
    print("=" * 80)
    print(f"Status: {result['synthesis']['status']}")
    print(f"Complete: {result['complete']}")
    print(f"Timeout: {result['timeout']}")
    print(f"Elapsed time: {result['elapsed_time']:.2f}s")
    print(f"Priority: {result['synthesis']['priority']}")
    print(f"\nResponses received: {len(result['responses'])}/{3}")
    print(f"Agents consulted: {result['synthesis']['agents_consulted']}")
    print(f"\n{result['synthesis']['recommendation']}")

    # Cleanup
    publisher.close()
    aggregator.close()


if __name__ == "__main__":
    main()
