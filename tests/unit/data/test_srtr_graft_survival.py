"""Tests for SRTROutcomesData.get_graft_survival_rate with matching data."""

import json
import tempfile
from pathlib import Path

from services.data.srtr_outcomes import SRTROutcomesData


class TestGraftSurvivalWithData:
    def test_returns_average_of_matching_records(self):
        data = [
            {
                "metric": "graft_survival",
                "years_post_transplant": 1.0,
                "survival_rate": 95.0,
                "age_group": "35-49",
            },
            {
                "metric": "graft_survival",
                "years_post_transplant": 1.0,
                "survival_rate": 97.0,
                "age_group": "35-49",
            },
        ]
        summary = {"total_records": 2, "latest_acute_rejection_rates": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "kidney_outcomes_flat.json", "w") as f:
                json.dump(data, f)
            with open(Path(tmpdir) / "kidney_summary.json", "w") as f:
                json.dump(summary, f)

            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            rate = srtr.get_graft_survival_rate(12, "35-49")

            assert rate == 96.0

    def test_returns_average_without_age_filter(self):
        data = [
            {
                "metric": "graft_survival",
                "years_post_transplant": 0.5,
                "survival_rate": 98.0,
            },
            {
                "metric": "graft_survival",
                "years_post_transplant": 0.5,
                "survival_rate": 96.0,
            },
        ]
        summary = {"total_records": 2, "latest_acute_rejection_rates": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "kidney_outcomes_flat.json", "w") as f:
                json.dump(data, f)
            with open(Path(tmpdir) / "kidney_summary.json", "w") as f:
                json.dump(summary, f)

            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            rate = srtr.get_graft_survival_rate(6)

            assert rate == 97.0

    def test_falls_back_to_summary_1yr_average(self):
        data = [{"metric": "other_metric", "years_post_transplant": 1.0}]
        summary = {
            "total_records": 1,
            "latest_acute_rejection_rates": {},
            "average_graft_survival_1yr": {"35-49": 94.5},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "kidney_outcomes_flat.json", "w") as f:
                json.dump(data, f)
            with open(Path(tmpdir) / "kidney_summary.json", "w") as f:
                json.dump(summary, f)

            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            rate = srtr.get_graft_survival_rate(6, "35-49")

            assert rate == 94.5

    def test_returns_default_when_no_matches_and_no_age_group(self):
        data = [{"metric": "other_metric", "years_post_transplant": 1.0}]
        summary = {"total_records": 1, "latest_acute_rejection_rates": {}}

        with tempfile.TemporaryDirectory() as tmpdir:
            with open(Path(tmpdir) / "kidney_outcomes_flat.json", "w") as f:
                json.dump(data, f)
            with open(Path(tmpdir) / "kidney_summary.json", "w") as f:
                json.dump(summary, f)

            srtr = SRTROutcomesData(organ="kidney", data_dir=tmpdir)
            rate = srtr.get_graft_survival_rate(6)

            assert rate == 98.0
