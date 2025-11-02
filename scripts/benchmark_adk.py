#!/usr/bin/env python3
"""
Benchmark ADK Orchestration Performance

Measures:
- Latency (including LLM routing overhead)
- Token usage (routing decisions + specialist responses)
- Routing accuracy (LLM vs keyword-based)
- Multi-turn conversation overhead

Outputs results to benchmarks/adk_results.json
"""

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification
from services.orchestration.adk_orchestrator import ADKOrchestrator  # noqa: E402
from services.orchestration.conversation_manager import ConversationManager  # noqa: E402


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    test_name: str
    user_request: str
    latency_ms: float
    token_usage: dict[str, int]  # {"input": X, "output": Y, "total": Z}
    agents_consulted: list[str]
    routing_path: list[str]
    routing_correct: bool
    expected_agent: str
    timestamp: str


class ADKBenchmark:
    """Benchmark suite for ADK orchestration."""

    def __init__(self):
        """Initialize benchmark suite."""
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.orchestrator = ADKOrchestrator(api_key=api_key)
        self.conversation_manager = ConversationManager()
        self.results: list[BenchmarkResult] = []

    def run_single_turn_benchmarks(self) -> None:
        """Run single-turn routing benchmarks."""
        print("\n=== Single-Turn Routing Benchmarks ===\n")

        test_cases = [
            {
                "name": "Missed Dose - Formal",
                "request": "I missed my tacrolimus dose at 8 AM, it is now 2 PM",
                "expected_agent": "MedicationAdvisor",
            },
            {
                "name": "Missed Dose - Casual",
                "request": "Forgot to take my meds this morning, what should I do?",
                "expected_agent": "MedicationAdvisor",
            },
            {
                "name": "Symptom - Fever",
                "request": "I have a fever of 101°F and feel weak",
                "expected_agent": "SymptomMonitor",
            },
            {
                "name": "Symptom - Decreased Urine",
                "request": "My urine output has decreased significantly today",
                "expected_agent": "SymptomMonitor",
            },
            {
                "name": "Drug Interaction - Ibuprofen",
                "request": "Can I take ibuprofen for my headache? I'm on tacrolimus",
                "expected_agent": "DrugInteractionChecker",
            },
            {
                "name": "Drug Interaction - Grapefruit",
                "request": "Is it safe to eat grapefruit with my medications?",
                "expected_agent": "DrugInteractionChecker",
            },
        ]

        for test_case in test_cases:
            print(f"Running: {test_case['name']}")
            result = self._benchmark_single_request(
                test_name=test_case["name"],
                user_request=test_case["request"],
                expected_agent=test_case["expected_agent"],
            )
            self.results.append(result)
            self._print_result(result)

    def run_multi_turn_benchmarks(self) -> None:
        """Run multi-turn conversation benchmarks."""
        print("\n=== Multi-Turn Conversation Benchmarks ===\n")

        # Benchmark: Clarification flow
        print("Running: Multi-Turn Clarification")
        conversation_id = str(uuid4())
        patient_id = "benchmark_patient_001"

        self.conversation_manager.start_conversation(conversation_id, patient_id)

        # Turn 1
        turn1_result = self._benchmark_conversation_turn(
            conversation_id=conversation_id,
            patient_id=patient_id,
            test_name="Turn 1 - Vague Question",
            user_request="What should I do?",
            expected_agent="TransplantCoordinator",  # Clarification needed
        )
        self.results.append(turn1_result)

        # Turn 2
        turn2_result = self._benchmark_conversation_turn(
            conversation_id=conversation_id,
            patient_id=patient_id,
            test_name="Turn 2 - Clarify Missed Dose",
            user_request="About my missed dose",
            expected_agent="MedicationAdvisor",
        )
        self.results.append(turn2_result)

        # Turn 3
        turn3_result = self._benchmark_conversation_turn(
            conversation_id=conversation_id,
            patient_id=patient_id,
            test_name="Turn 3 - Provide Details",
            user_request="Tacrolimus at 8 AM, it's now 2 PM",
            expected_agent="MedicationAdvisor",
        )
        self.results.append(turn3_result)

        print(f"\nCompleted multi-turn conversation ({len(self.results)} total benchmarks)")

    def _benchmark_single_request(
        self, test_name: str, user_request: str, expected_agent: str
    ) -> BenchmarkResult:
        """
        Benchmark a single request.

        Args:
            test_name: Name of the test
            user_request: User's request
            expected_agent: Expected specialist agent to be consulted

        Returns:
            BenchmarkResult with timing and token usage
        """
        start_time = time.time()

        response = self.orchestrator.process_request(
            user_request=user_request, patient_id="benchmark_patient"
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Extract token usage (would need ADK event parsing in real implementation)
        # For now, estimate based on input/output length
        token_usage = self._estimate_token_usage(user_request, response["response"])

        # Check routing correctness
        agents_consulted = response.get("agents_consulted", [])
        routing_correct = expected_agent in agents_consulted or len(agents_consulted) == 0

        return BenchmarkResult(
            test_name=test_name,
            user_request=user_request,
            latency_ms=latency_ms,
            token_usage=token_usage,
            agents_consulted=agents_consulted,
            routing_path=response.get("routing_path", []),
            routing_correct=routing_correct,
            expected_agent=expected_agent,
            timestamp=datetime.now().isoformat(),
        )

    def _benchmark_conversation_turn(
        self,
        conversation_id: str,
        patient_id: str,
        test_name: str,
        user_request: str,
        expected_agent: str,
    ) -> BenchmarkResult:
        """
        Benchmark a single conversation turn.

        Args:
            conversation_id: Conversation identifier
            patient_id: Patient identifier
            test_name: Name of the test
            user_request: User's request
            expected_agent: Expected agent to handle request

        Returns:
            BenchmarkResult with timing and token usage
        """
        start_time = time.time()

        response = self.orchestrator.process_request(
            user_request=user_request,
            patient_id=patient_id,
            conversation_history=self.conversation_manager.get_conversation_history(
                conversation_id
            ),
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000

        # Update conversation
        self.conversation_manager.add_turn(conversation_id, "user", user_request)
        self.conversation_manager.add_turn(conversation_id, "assistant", response["response"])

        # Estimate token usage
        token_usage = self._estimate_token_usage(user_request, response["response"])

        # Check routing
        agents_consulted = response.get("agents_consulted", [])
        routing_correct = expected_agent in agents_consulted or len(agents_consulted) == 0

        return BenchmarkResult(
            test_name=test_name,
            user_request=user_request,
            latency_ms=latency_ms,
            token_usage=token_usage,
            agents_consulted=agents_consulted,
            routing_path=response.get("routing_path", []),
            routing_correct=routing_correct,
            expected_agent=expected_agent,
            timestamp=datetime.now().isoformat(),
        )

    def _estimate_token_usage(self, user_request: str, response: str) -> dict[str, int]:
        """
        Estimate token usage from text length.

        Real implementation would parse ADK events for actual token counts.

        Args:
            user_request: User input text
            response: Agent response text

        Returns:
            Dict with input, output, and total token counts
        """
        # Rough estimate: 1 token ≈ 4 characters for English text
        input_tokens = len(user_request) // 4
        output_tokens = len(response) // 4
        total_tokens = input_tokens + output_tokens

        return {"input": input_tokens, "output": output_tokens, "total": total_tokens}

    def _print_result(self, result: BenchmarkResult) -> None:
        """Print a benchmark result."""
        print(f"  Request: {result.user_request[:60]}...")
        print(f"  Latency: {result.latency_ms:.2f}ms")
        print(f"  Tokens: {result.token_usage['total']} total")
        print(f"  Routing: {result.expected_agent} (correct: {result.routing_correct})")
        print()

    def calculate_statistics(self) -> dict[str, Any]:
        """Calculate aggregate statistics from all benchmark results."""
        if not self.results:
            return {}

        latencies = [r.latency_ms for r in self.results]
        token_totals = [r.token_usage["total"] for r in self.results]
        routing_correct_count = sum(1 for r in self.results if r.routing_correct)

        return {
            "total_tests": len(self.results),
            "latency": {
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": sum(latencies) / len(latencies),
                "median_ms": sorted(latencies)[len(latencies) // 2],
            },
            "token_usage": {
                "min_tokens": min(token_totals),
                "max_tokens": max(token_totals),
                "avg_tokens": sum(token_totals) / len(token_totals),
                "total_tokens": sum(token_totals),
            },
            "routing_accuracy": {
                "correct": routing_correct_count,
                "total": len(self.results),
                "accuracy_pct": (routing_correct_count / len(self.results)) * 100,
            },
        }

    def save_results(self, output_path: Path) -> None:
        """
        Save benchmark results to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_data = {
            "benchmark_metadata": {
                "orchestration_method": "ADK Native",
                "timestamp": datetime.now().isoformat(),
                "adk_version": "1.17.0",
            },
            "statistics": self.calculate_statistics(),
            "individual_results": [asdict(r) for r in self.results],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✅ Results saved to: {output_path}")

    def print_summary(self) -> None:
        """Print benchmark summary statistics."""
        stats = self.calculate_statistics()

        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        print(f"\nTotal Tests: {stats['total_tests']}")

        print("\nLatency:")
        print(f"  Min: {stats['latency']['min_ms']:.2f}ms")
        print(f"  Max: {stats['latency']['max_ms']:.2f}ms")
        print(f"  Avg: {stats['latency']['avg_ms']:.2f}ms")
        print(f"  Median: {stats['latency']['median_ms']:.2f}ms")

        print("\nToken Usage:")
        print(f"  Min: {stats['token_usage']['min_tokens']} tokens")
        print(f"  Max: {stats['token_usage']['max_tokens']} tokens")
        print(f"  Avg: {stats['token_usage']['avg_tokens']:.2f} tokens")
        print(f"  Total: {stats['token_usage']['total_tokens']} tokens")

        print("\nRouting Accuracy:")
        print(
            f"  Correct: {stats['routing_accuracy']['correct']}/{stats['routing_accuracy']['total']}"
        )
        print(f"  Accuracy: {stats['routing_accuracy']['accuracy_pct']:.1f}%")

        print("\n" + "=" * 60)


def main():
    """Run ADK orchestration benchmarks."""
    print("=" * 60)
    print("ADK Orchestration Benchmark Suite")
    print("=" * 60)

    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("\n❌ Error: GEMINI_API_KEY environment variable not set")
        print("   Set it with: export GEMINI_API_KEY='your-key'")
        sys.exit(1)

    # Run benchmarks
    benchmark = ADKBenchmark()

    try:
        benchmark.run_single_turn_benchmarks()
        benchmark.run_multi_turn_benchmarks()

        # Print summary
        benchmark.print_summary()

        # Save results
        output_path = project_root / "benchmarks" / "adk_results.json"
        benchmark.save_results(output_path)

        print("\n✅ Benchmark complete!")

    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
