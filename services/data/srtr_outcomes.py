"""
SRTR Outcomes Data Query Module

Provides easy access to real transplant outcomes data from SRTR for use by ADK agents.
Data is loaded from JSON files (fast, no Firestore queries needed).
Supports all 6 organ types: kidney, liver, heart, lung, pancreas, intestine.
"""

import json
from pathlib import Path
from typing import Any


class SRTROutcomesData:
    """Query SRTR transplant outcomes data for any organ."""

    SUPPORTED_ORGANS = ["kidney", "liver", "heart", "lung", "pancreas", "intestine"]

    def __init__(self, organ: str = "kidney", data_dir: str = "data/srtr/processed"):
        """
        Initialize SRTR data accessor.

        Args:
            organ: Organ type (kidney, liver, heart, lung, pancreas, intestine)
            data_dir: Directory containing processed JSON files
        """
        if organ.lower() not in self.SUPPORTED_ORGANS:
            raise ValueError(f"Unsupported organ: {organ}. Must be one of {self.SUPPORTED_ORGANS}")

        self.organ = organ.lower()
        self.data_dir = Path(data_dir)
        self._data: list[dict[str, Any]] | None = None
        self._summary: dict[str, Any] | None = None
        self._load_data()

    def _load_data(self):
        """Load data from JSON files for specified organ."""
        flat_file = self.data_dir / f"{self.organ}_outcomes_flat.json"
        summary_file = self.data_dir / f"{self.organ}_summary.json"

        if flat_file.exists():
            with open(flat_file) as f:
                self._data = json.load(f)

        if summary_file.exists():
            with open(summary_file) as f:
                self._summary = json.load(f)

    def get_acute_rejection_rate(self, age_group: str | None = None) -> float | dict[str, float]:
        """
        Get acute rejection rate (latest year: 2022).

        Args:
            age_group: Age group ("18-34 years", "35-49", "50-64", "65+")
                      If None, returns all age groups

        Returns:
            Rejection rate percentage, or dict of all rates
        """
        if not self._summary:
            return 0.0

        rates: dict[str, float] = self._summary.get("latest_acute_rejection_rates", {})

        if age_group:
            return float(rates.get(age_group, 0.0))

        return rates

    def get_graft_survival_rate(
        self, months_post_transplant: int, age_group: str | None = None
    ) -> float:
        """
        Get graft survival rate at specified time post-transplant.

        Args:
            months_post_transplant: Months after transplant (e.g., 6, 12, 24)
            age_group: Age group to filter by

        Returns:
            Survival rate percentage
        """
        if not self._data:
            return 99.0  # Conservative default

        years = months_post_transplant / 12.0

        # Find matching records
        matches = [
            r
            for r in self._data
            if r.get("metric") == "graft_survival"
            and abs(r.get("years_post_transplant", 0) - years) < 0.1
        ]

        if age_group:
            matches = [r for r in matches if r.get("age_group") == age_group]

        if not matches:
            # Return 1-year average if no exact match
            if age_group and self._summary:
                avg_survival: dict[str, float] = self._summary.get("average_graft_survival_1yr", {})
                return float(avg_survival.get(age_group, 98.0))
            return 98.0

        # Average the matching records
        survival_rates: list[float] = [float(r["survival_rate"]) for r in matches]
        return float(sum(survival_rates) / len(survival_rates))

    def get_population_context(self, age_group: str, months_post_transplant: int) -> dict[str, Any]:
        """
        Get comprehensive population context for risk assessment.

        Args:
            age_group: Patient age group
            months_post_transplant: Months since transplant

        Returns:
            Dictionary with population statistics
        """
        return {
            "age_group": age_group,
            "months_post_transplant": months_post_transplant,
            "baseline_rejection_rate": self.get_acute_rejection_rate(age_group),
            "expected_graft_survival": self.get_graft_survival_rate(
                months_post_transplant, age_group
            ),
            "data_source": "SRTR 2023 Annual Data Report",
            "population_size": (self._summary.get("total_records", 0) if self._summary else 0),
        }

    def format_for_prompt(self, age_group: str, months_post_transplant: int) -> str:
        """
        Format population data for inclusion in AI prompt.

        Args:
            age_group: Patient age group
            months_post_transplant: Months since transplant

        Returns:
            Formatted string for prompt context
        """
        context = self.get_population_context(age_group, months_post_transplant)

        return f"""Population Statistics (SRTR 2023 - {self.organ.capitalize()} Transplant):
- Organ: {self.organ.capitalize()}
- Age Group: {context["age_group"]}
- Time Post-Transplant: {context["months_post_transplant"]} months
- Baseline Acute Rejection Rate: {context["baseline_rejection_rate"]:.2f}%
- Expected Graft Survival: {context["expected_graft_survival"]:.2f}%
- Data Source: {context["data_source"]}"""

    def get_risk_multiplier(self, hours_late: float, age_group: str) -> tuple[float, str]:
        """
        Calculate risk multiplier based on population data and missed dose severity.

        Args:
            hours_late: Hours medication is late
            age_group: Patient age group

        Returns:
            Tuple of (risk_multiplier, explanation)
        """
        # Get baseline rejection rate for age group
        baseline_rejection = self.get_acute_rejection_rate(age_group)

        # Risk factors
        if hours_late > 12:
            multiplier = 1.5
            explanation = f"Dose >12h late significantly increases risk. Your age group ({age_group}) has baseline rejection rate of {baseline_rejection:.2f}%."
        elif hours_late > 6:
            multiplier = 1.2
            explanation = f"Dose 6-12h late moderately increases risk. Baseline rejection rate for {age_group}: {baseline_rejection:.2f}%."
        elif hours_late > 2:
            multiplier = 1.1
            explanation = f"Slight risk increase. Stay vigilant. Baseline rejection rate: {baseline_rejection:.2f}%."
        else:
            multiplier = 1.0
            explanation = (
                f"Minimal risk impact. Baseline rejection rate: {baseline_rejection:.2f}%."
            )

        return multiplier, explanation


# Global instances for easy import (one per organ)
_srtr_data_cache: dict[str, SRTROutcomesData] = {}


def get_srtr_data(organ: str = "kidney") -> SRTROutcomesData:
    """
    Get cached instance of SRTR data for specified organ.

    Args:
        organ: Organ type (kidney, liver, heart, lung, pancreas, intestine)

    Returns:
        SRTROutcomesData instance for the specified organ
    """
    organ_lower = organ.lower()
    if organ_lower not in _srtr_data_cache:
        _srtr_data_cache[organ_lower] = SRTROutcomesData(organ=organ_lower)
    return _srtr_data_cache[organ_lower]
