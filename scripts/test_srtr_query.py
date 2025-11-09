#!/usr/bin/env python3
"""Test script to demonstrate SRTR data querying."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data.srtr_outcomes import get_srtr_data


def main():
    """Demonstrate SRTR data queries."""
    print("🔬 SRTR Data Query Test")
    print("=" * 60)

    srtr = get_srtr_data()

    # Test 1: Get acute rejection rates
    print("\n1️⃣  Acute Rejection Rates (2022):")
    all_rates = srtr.get_acute_rejection_rate()
    for age_group, rate in all_rates.items():
        print(f"   {age_group}: {rate:.2f}%")

    # Test 2: Get graft survival for specific patient
    print("\n2️⃣  Graft Survival Rates:")
    age_group = "35-49"
    for months in [6, 12, 24, 36]:
        survival = srtr.get_graft_survival_rate(months, age_group)
        print(f"   {age_group} at {months} months: {survival:.2f}%")

    # Test 3: Get population context
    print("\n3️⃣  Population Context for 45-year-old, 6 months post-transplant:")
    context = srtr.get_population_context("35-49", 6)
    for key, value in context.items():
        print(f"   {key}: {value}")

    # Test 4: Format for AI prompt
    print("\n4️⃣  Formatted for AI Prompt:")
    prompt_text = srtr.format_for_prompt("35-49", 6)
    print(prompt_text)

    # Test 5: Risk multiplier calculation
    print("\n5️⃣  Risk Multiplier Examples:")
    scenarios = [
        ("medium", 2, "35-49"),
        ("medium", 8, "35-49"),
        ("medium", 15, "18-34 years"),
    ]

    for risk, hours_late, age_group in scenarios:
        multiplier, explanation = srtr.get_risk_multiplier(risk, hours_late, age_group)
        print(f"\n   Scenario: {hours_late}h late, age {age_group}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   {explanation}")

    print("\n✅ All tests complete!")


if __name__ == "__main__":
    main()
