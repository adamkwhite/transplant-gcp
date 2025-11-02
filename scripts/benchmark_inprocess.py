#!/usr/bin/env python3
"""
Benchmark Script for In-Process Multi-Agent Communication

Measures latency and performance of the coordinator routing requests
to specialist agents.

Usage:
    python scripts/benchmark_inprocess.py

Outputs results to: benchmarks/inprocess_results.json
"""

import json
import os
import statistics
import time
from pathlib import Path

from services.agents.coordinator_agent import TransplantCoordinatorAgent
from services.agents.drug_interaction_agent import DrugInteractionCheckerAgent
from services.agents.medication_advisor_agent import MedicationAdvisorAgent
from services.agents.symptom_monitor_agent import SymptomMonitorAgent

# Sample test requests covering different scenarios
SAMPLE_REQUESTS = [
    {
        "id": 1,
        "request": "I missed my tacrolimus dose at 8am, it's now 2pm",
        "expected_agents": ["MedicationAdvisor"],
        "category": "single_agent_medication",
    },
    {
        "id": 2,
        "request": "I have a fever of 101°F and decreased urine output",
        "expected_agents": ["SymptomMonitor"],
        "category": "single_agent_symptom",
    },
    {
        "id": 3,
        "request": "Can I take ibuprofen with my tacrolimus?",
        "expected_agents": ["DrugInteractionChecker"],
        "category": "single_agent_interaction",
    },
    {
        "id": 4,
        "request": "I missed my morning dose and now I have a fever",
        "expected_agents": ["MedicationAdvisor", "SymptomMonitor"],
        "category": "multi_agent_2",
    },
    {
        "id": 5,
        "request": "I forgot my tacrolimus at 8am and want to take ibuprofen for a headache",
        "expected_agents": ["MedicationAdvisor", "DrugInteractionChecker"],
        "category": "multi_agent_2",
    },
    {
        "id": 6,
        "request": "I missed my dose, have fever and decreased urine, and want to take aspirin",
        "expected_agents": ["MedicationAdvisor", "SymptomMonitor", "DrugInteractionChecker"],
        "category": "multi_agent_3",
    },
    {
        "id": 7,
        "request": "Should I take my mycophenolate now or skip it?",
        "expected_agents": ["MedicationAdvisor"],
        "category": "single_agent_medication",
    },
    {
        "id": 8,
        "request": "I'm experiencing nausea and fatigue today",
        "expected_agents": ["SymptomMonitor"],
        "category": "single_agent_symptom",
    },
    {
        "id": 9,
        "request": "Can I eat grapefruit with my immunosuppressants?",
        "expected_agents": ["DrugInteractionChecker"],
        "category": "single_agent_interaction",
    },
    {
        "id": 10,
        "request": "I missed prednisone this morning and feeling weak",
        "expected_agents": ["MedicationAdvisor", "SymptomMonitor"],
        "category": "multi_agent_2",
    },
]


def setup_coordinator():
    """Initialize coordinator with specialist agents."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    # Create specialist agents
    medication_advisor = MedicationAdvisorAgent(api_key=api_key)
    symptom_monitor = SymptomMonitorAgent(api_key=api_key)
    drug_interaction_checker = DrugInteractionCheckerAgent(api_key=api_key)

    # Create coordinator
    coordinator = TransplantCoordinatorAgent(
        api_key=api_key,
        medication_advisor=medication_advisor,
        symptom_monitor=symptom_monitor,
        drug_interaction_checker=drug_interaction_checker,
    )

    return coordinator


def benchmark_request(coordinator, request_data, parallel=True):
    """Benchmark a single request."""
    request = request_data["request"]

    # Measure total latency
    start_time = time.time()

    try:
        result = coordinator.route_request(request, parallel=parallel)
        end_time = time.time()

        latency = end_time - start_time

        return {
            "request_id": request_data["id"],
            "category": request_data["category"],
            "request": request,
            "latency_seconds": latency,
            "agents_consulted": result["agents_consulted"],
            "request_type": result["request_type"],
            "confidence": result["confidence"],
            "success": True,
            "error": None,
        }

    except Exception as e:
        end_time = time.time()
        latency = end_time - start_time

        return {
            "request_id": request_data["id"],
            "category": request_data["category"],
            "request": request,
            "latency_seconds": latency,
            "agents_consulted": [],
            "request_type": "error",
            "confidence": 0.0,
            "success": False,
            "error": str(e),
        }


def run_benchmarks():
    """Run all benchmarks and collect results."""
    print("🚀 Starting In-Process Multi-Agent Communication Benchmarks")
    print(f"Testing {len(SAMPLE_REQUESTS)} sample requests...\n")

    coordinator = setup_coordinator()

    results = []
    latencies = []

    # Test each request
    for i, request_data in enumerate(SAMPLE_REQUESTS, 1):
        print(f"[{i}/{len(SAMPLE_REQUESTS)}] Testing: {request_data['request'][:60]}...")

        # Run benchmark
        result = benchmark_request(coordinator, request_data, parallel=True)

        results.append(result)

        if result["success"]:
            latencies.append(result["latency_seconds"])
            print(
                f"  ✓ Latency: {result['latency_seconds']:.2f}s | "
                f"Agents: {', '.join(result['agents_consulted'])}"
            )
        else:
            print(f"  ✗ Error: {result['error']}")

        print()

    # Calculate statistics
    if latencies:
        stats = {
            "mean_latency": statistics.mean(latencies),
            "median_latency": statistics.median(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "p50_latency": statistics.median(latencies),
            "p95_latency": statistics.quantiles(latencies, n=20)[18]
            if len(latencies) > 1
            else latencies[0],
            "total_requests": len(SAMPLE_REQUESTS),
            "successful_requests": len([r for r in results if r["success"]]),
            "failed_requests": len([r for r in results if not r["success"]]),
        }
    else:
        stats = {
            "mean_latency": 0,
            "median_latency": 0,
            "min_latency": 0,
            "max_latency": 0,
            "p50_latency": 0,
            "p95_latency": 0,
            "total_requests": len(SAMPLE_REQUESTS),
            "successful_requests": 0,
            "failed_requests": len(SAMPLE_REQUESTS),
        }

    # Category breakdown
    category_stats = {}
    for category in {r["category"] for r in results}:
        category_results = [r for r in results if r["category"] == category]
        category_latencies = [r["latency_seconds"] for r in category_results if r["success"]]

        if category_latencies:
            category_stats[category] = {
                "count": len(category_results),
                "mean_latency": statistics.mean(category_latencies),
                "success_rate": len([r for r in category_results if r["success"]])
                / len(category_results),
            }

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": stats,
        "category_breakdown": category_stats,
        "detailed_results": results,
    }


def save_results(results, output_path="benchmarks/inprocess_results.json"):
    """Save benchmark results to JSON file."""
    # Create directory if needed
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✓ Results saved to: {output_file}")


def print_summary(results):
    """Print benchmark summary."""
    stats = results["summary"]

    print("\n" + "=" * 60)
    print("📊 BENCHMARK RESULTS SUMMARY")
    print("=" * 60)

    print(f"\nTotal Requests: {stats['total_requests']}")
    print(f"Successful: {stats['successful_requests']} | Failed: {stats['failed_requests']}")
    print(f"Success Rate: {stats['successful_requests'] / stats['total_requests'] * 100:.1f}%")

    print("\n⏱️  LATENCY STATISTICS:")
    print(f"  Mean:   {stats['mean_latency']:.2f}s")
    print(f"  Median: {stats['median_latency']:.2f}s")
    print(f"  Min:    {stats['min_latency']:.2f}s")
    print(f"  Max:    {stats['max_latency']:.2f}s")
    print(f"  P50:    {stats['p50_latency']:.2f}s")
    print(f"  P95:    {stats['p95_latency']:.2f}s")

    print("\n📂 CATEGORY BREAKDOWN:")
    for category, cat_stats in results["category_breakdown"].items():
        print(f"  {category}:")
        print(f"    Count:        {cat_stats['count']}")
        print(f"    Mean Latency: {cat_stats['mean_latency']:.2f}s")
        print(f"    Success Rate: {cat_stats['success_rate'] * 100:.1f}%")

    # Success criteria check
    print("\n✅ SUCCESS CRITERIA:")
    p50_target = 5.0
    p50_actual = stats["p50_latency"]
    p50_pass = p50_actual < p50_target

    print(
        f"  P50 latency < {p50_target}s: {'✓ PASS' if p50_pass else '✗ FAIL'} ({p50_actual:.2f}s)"
    )

    print("\n" + "=" * 60)


def main():
    """Main benchmark execution."""
    try:
        results = run_benchmarks()
        save_results(results)
        print_summary(results)

        # Exit code based on success criteria
        if results["summary"]["p50_latency"] < 5.0:
            print("\n✓ All success criteria met!")
            return 0
        else:
            print("\n⚠ Some success criteria not met")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠ Benchmark interrupted by user")
        return 130
    except Exception as e:
        print(f"\n✗ Benchmark failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
