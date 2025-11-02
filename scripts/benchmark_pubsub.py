#!/usr/bin/env python3
"""
Pub/Sub Multi-Agent Communication Benchmark

Measures end-to-end latency for Pub/Sub-based agent communication.
Compares against in-process implementation if available.
"""

import json
import os
import statistics
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import pubsub_v1

from services.pubsub.coordinator_publisher import CoordinatorPublisher
from services.pubsub.response_aggregator import ResponseAggregator
from services.pubsub.specialist_subscribers import SpecialistSubscribers


class PubSubBenchmark:
    """Benchmark for Pub/Sub multi-agent communication."""

    def __init__(self, num_iterations: int = 10):
        """
        Initialize benchmark.

        Args:
            num_iterations: Number of benchmark iterations to run
        """
        self.num_iterations = num_iterations
        self.results: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "num_iterations": num_iterations,
            "emulator_host": os.environ.get("PUBSUB_EMULATOR_HOST", "not set"),
            "single_agent_latencies": [],
            "multi_agent_latencies": [],
            "processing_times": [],
            "message_overhead": [],
        }

    def setup_subscribers(self) -> tuple[Any, list[Any]]:
        """Start specialist subscribers in background."""
        subscribers = SpecialistSubscribers()
        subscriber_client = pubsub_v1.SubscriberClient()
        project_id = "transplant-pubsub-emulator"

        # Subscription paths
        medication_sub = subscriber_client.subscription_path(project_id, "medication-requests-sub")
        symptom_sub = subscriber_client.subscription_path(project_id, "symptom-requests-sub")
        interaction_sub = subscriber_client.subscription_path(
            project_id, "interaction-requests-sub"
        )

        # Start subscribers
        futures = []
        futures.append(
            subscriber_client.subscribe(medication_sub, subscribers.on_medication_request)
        )
        futures.append(subscriber_client.subscribe(symptom_sub, subscribers.on_symptom_request))
        futures.append(
            subscriber_client.subscribe(interaction_sub, subscribers.on_drug_interaction_request)
        )

        # Let subscribers start
        time.sleep(2)

        return subscribers, futures

    def teardown_subscribers(self, subscribers: Any, futures: list[Any]) -> None:
        """Stop specialist subscribers."""
        for future in futures:
            future.cancel()
        subscribers.close()

    def benchmark_single_agent_request(self, iteration: int) -> dict[str, float]:
        """
        Benchmark single specialist agent request.

        Args:
            iteration: Current iteration number

        Returns:
            Dict with latency metrics
        """
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=15.0)

        # Measure end-to-end latency
        start_time = time.time()

        request_id = publisher.publish_medication_request(
            patient_id=f"benchmark-patient-{iteration}",
            medication_name="tacrolimus",
            scheduled_time="2024-01-01T08:00:00",
            actual_time="2024-01-01T10:00:00",
            patient_context={"transplant_type": "kidney"},
        )

        publish_time = time.time()

        result = aggregator.wait_for_responses(
            request_ids=[request_id],
            expected_count=1,
        )

        total_time = time.time() - start_time

        # Extract metrics
        if result["responses"]:
            agent_processing_time = result["responses"][0]["processing_time"]
            message_overhead = total_time - agent_processing_time
        else:
            agent_processing_time = 0.0
            message_overhead = 0.0

        # Cleanup
        publisher.close()
        aggregator.close()

        return {
            "total_latency": total_time,
            "publish_latency": publish_time - start_time,
            "agent_processing_time": agent_processing_time,
            "message_overhead": message_overhead,
            "complete": result["complete"],
            "timeout": result["timeout"],
        }

    def benchmark_multi_agent_request(self, iteration: int) -> dict[str, float]:
        """
        Benchmark multi-agent request (3 specialists).

        Args:
            iteration: Current iteration number

        Returns:
            Dict with latency metrics
        """
        publisher = CoordinatorPublisher()
        aggregator = ResponseAggregator(timeout_seconds=20.0)

        # Measure end-to-end latency
        start_time = time.time()

        request_ids = publisher.publish_multi_agent_request(
            patient_id=f"benchmark-multi-{iteration}",
            request_types=["medication", "symptom", "interaction"],
            parameters={
                "medication": {
                    "medication_name": "tacrolimus",
                    "scheduled_time": "2024-01-01T08:00:00",
                    "actual_time": "2024-01-01T09:00:00",
                },
                "symptom": {
                    "symptoms": ["fever", "fatigue"],
                    "severity": "moderate",
                    "duration_hours": 12.0,
                },
                "interaction": {
                    "current_medications": ["tacrolimus"],
                    "new_medication": "ibuprofen",
                },
            },
        )

        publish_time = time.time()

        result = aggregator.wait_for_responses(
            request_ids=request_ids,
            expected_count=3,
        )

        total_time = time.time() - start_time

        # Extract metrics
        if result["responses"]:
            avg_agent_time = sum(r["processing_time"] for r in result["responses"]) / len(
                result["responses"]
            )
            max_agent_time = max(r["processing_time"] for r in result["responses"])
            message_overhead = total_time - max_agent_time  # Parallel processing
        else:
            avg_agent_time = 0.0
            max_agent_time = 0.0
            message_overhead = 0.0

        # Cleanup
        publisher.close()
        aggregator.close()

        return {
            "total_latency": total_time,
            "publish_latency": publish_time - start_time,
            "avg_agent_processing_time": avg_agent_time,
            "max_agent_processing_time": max_agent_time,
            "message_overhead": message_overhead,
            "responses_received": len(result["responses"]),
            "complete": result["complete"],
            "timeout": result["timeout"],
        }

    def run_benchmarks(self) -> dict[str, Any]:
        """
        Run all benchmarks.

        Returns:
            Dict with benchmark results
        """
        print("=" * 80)
        print("Pub/Sub Multi-Agent Communication Benchmark")
        print("=" * 80)
        print(f"Iterations: {self.num_iterations}")
        print(f"Emulator: {self.results['emulator_host']}")
        print()

        # Start subscribers
        print("Starting specialist subscribers...")
        subscribers, futures = self.setup_subscribers()
        print("✓ Subscribers ready\n")

        # Benchmark single-agent requests
        print(f"Running {self.num_iterations} single-agent request benchmarks...")
        for i in range(self.num_iterations):
            print(f"  Iteration {i + 1}/{self.num_iterations}...", end=" ", flush=True)
            result = self.benchmark_single_agent_request(i)
            self.results["single_agent_latencies"].append(result)
            print(f"{result['total_latency']:.3f}s")
            time.sleep(0.5)  # Brief pause between iterations

        # Benchmark multi-agent requests
        print(f"\nRunning {self.num_iterations} multi-agent request benchmarks...")
        for i in range(self.num_iterations):
            print(f"  Iteration {i + 1}/{self.num_iterations}...", end=" ", flush=True)
            result = self.benchmark_multi_agent_request(i)
            self.results["multi_agent_latencies"].append(result)
            print(f"{result['total_latency']:.3f}s")
            time.sleep(0.5)

        # Stop subscribers
        print("\nStopping subscribers...")
        self.teardown_subscribers(subscribers, futures)

        # Calculate statistics
        self._calculate_statistics()

        return self.results

    def _calculate_statistics(self) -> None:
        """Calculate summary statistics from benchmark results."""
        # Single-agent statistics
        single_latencies = [r["total_latency"] for r in self.results["single_agent_latencies"]]
        single_processing = [
            r["agent_processing_time"] for r in self.results["single_agent_latencies"]
        ]
        single_overhead = [r["message_overhead"] for r in self.results["single_agent_latencies"]]

        self.results["single_agent_summary"] = {
            "mean_latency": statistics.mean(single_latencies),
            "median_latency": statistics.median(single_latencies),
            "stdev_latency": statistics.stdev(single_latencies)
            if len(single_latencies) > 1
            else 0.0,
            "min_latency": min(single_latencies),
            "max_latency": max(single_latencies),
            "mean_processing_time": statistics.mean(single_processing),
            "mean_message_overhead": statistics.mean(single_overhead),
            "success_rate": sum(1 for r in self.results["single_agent_latencies"] if r["complete"])
            / len(self.results["single_agent_latencies"]),
        }

        # Multi-agent statistics
        multi_latencies = [r["total_latency"] for r in self.results["multi_agent_latencies"]]
        multi_avg_processing = [
            r["avg_agent_processing_time"] for r in self.results["multi_agent_latencies"]
        ]
        multi_max_processing = [
            r["max_agent_processing_time"] for r in self.results["multi_agent_latencies"]
        ]
        multi_overhead = [r["message_overhead"] for r in self.results["multi_agent_latencies"]]

        self.results["multi_agent_summary"] = {
            "mean_latency": statistics.mean(multi_latencies),
            "median_latency": statistics.median(multi_latencies),
            "stdev_latency": statistics.stdev(multi_latencies) if len(multi_latencies) > 1 else 0.0,
            "min_latency": min(multi_latencies),
            "max_latency": max(multi_latencies),
            "mean_avg_processing_time": statistics.mean(multi_avg_processing),
            "mean_max_processing_time": statistics.mean(multi_max_processing),
            "mean_message_overhead": statistics.mean(multi_overhead),
            "success_rate": sum(1 for r in self.results["multi_agent_latencies"] if r["complete"])
            / len(self.results["multi_agent_latencies"]),
        }

    def print_results(self) -> None:
        """Print benchmark results to console."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        # Single-agent results
        single = self.results["single_agent_summary"]
        print("\nSINGLE-AGENT REQUESTS:")
        print(
            f"  Mean latency:      {single['mean_latency']:.3f}s ± {single['stdev_latency']:.3f}s"
        )
        print(f"  Median latency:    {single['median_latency']:.3f}s")
        print(f"  Min/Max latency:   {single['min_latency']:.3f}s / {single['max_latency']:.3f}s")
        print(f"  Processing time:   {single['mean_processing_time']:.3f}s")
        print(f"  Message overhead:  {single['mean_message_overhead']:.3f}s")
        print(f"  Success rate:      {single['success_rate']:.1%}")

        # Multi-agent results
        multi = self.results["multi_agent_summary"]
        print("\nMULTI-AGENT REQUESTS (3 specialists):")
        print(f"  Mean latency:      {multi['mean_latency']:.3f}s ± {multi['stdev_latency']:.3f}s")
        print(f"  Median latency:    {multi['median_latency']:.3f}s")
        print(f"  Min/Max latency:   {multi['min_latency']:.3f}s / {multi['max_latency']:.3f}s")
        print(f"  Avg processing:    {multi['mean_avg_processing_time']:.3f}s")
        print(f"  Max processing:    {multi['mean_max_processing_time']:.3f}s")
        print(f"  Message overhead:  {multi['mean_message_overhead']:.3f}s")
        print(f"  Success rate:      {multi['success_rate']:.1%}")

        # Comparison
        print("\nPARALLELISM BENEFIT:")
        sequential_estimate = single["mean_latency"] * 3
        actual_multi = multi["mean_latency"]
        speedup = sequential_estimate / actual_multi
        print(f"  Sequential (est):  {sequential_estimate:.3f}s (3 × single-agent)")
        print(f"  Parallel (actual): {actual_multi:.3f}s")
        print(f"  Speedup:           {speedup:.2f}x")

    def save_results(self, output_path: str = "benchmarks/pubsub_results.json") -> None:
        """
        Save benchmark results to JSON file.

        Args:
            output_path: Path to save results
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n✓ Results saved to: {output_file}")


def main() -> None:
    """Run the Pub/Sub benchmark."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Pub/Sub multi-agent communication")
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=10,
        help="Number of benchmark iterations (default: 10)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="benchmarks/pubsub_results.json",
        help="Output file path (default: benchmarks/pubsub_results.json)",
    )
    args = parser.parse_args()

    # Check emulator
    if "PUBSUB_EMULATOR_HOST" not in os.environ:
        print("WARNING: PUBSUB_EMULATOR_HOST not set")
        print("Make sure emulator is running: bash scripts/setup_pubsub_emulator.sh")
        return

    # Run benchmark
    benchmark = PubSubBenchmark(num_iterations=args.iterations)
    benchmark.run_benchmarks()
    benchmark.print_results()
    benchmark.save_results(args.output)


if __name__ == "__main__":
    main()
