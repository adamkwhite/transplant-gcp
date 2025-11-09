#!/usr/bin/env python3
"""Test script to demonstrate multi-organ SRTR data querying."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.data.srtr_outcomes import get_srtr_data


def test_organ_data(organ: str):
    """Test querying data for a specific organ."""
    print(f"\n{'=' * 60}")
    print(f"🫁 {organ.upper()} TRANSPLANT DATA")
    print(f"{'=' * 60}")

    srtr = get_srtr_data(organ)

    # Test 1: Get acute rejection rates
    print("\n1️⃣  Acute Rejection Rates (2022):")
    all_rates = srtr.get_acute_rejection_rate()
    if all_rates:
        for age_group, rate in list(all_rates.items())[:4]:  # Show first 4
            print(f"   {age_group}: {rate:.2f}%")
    else:
        print("   No rejection rate data available")

    # Test 2: Get patient survival for specific demographic
    print("\n2️⃣  Patient Survival Rates (Age 35-49):")
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
        (2, "35-49"),
        (8, "35-49"),
        (15, "18-34 years"),
    ]

    for hours_late, age_grp in scenarios:
        multiplier, explanation = srtr.get_risk_multiplier(hours_late, age_grp)
        print(f"\n   Scenario: {hours_late}h late, age {age_grp}")
        print(f"   Multiplier: {multiplier}x")
        print(f"   {explanation}")


def main():
    """Demonstrate SRTR data queries for all organs."""
    print("🏥 SRTR Multi-Organ Data Query Test")
    print("=" * 60)

    # Test all organs
    organs = ["lung", "kidney", "liver", "heart"]  # Lung first since it's most relevant

    for organ in organs:
        try:
            test_organ_data(organ)
        except Exception as e:
            print(f"\n❌ Error testing {organ}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ Multi-organ testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
