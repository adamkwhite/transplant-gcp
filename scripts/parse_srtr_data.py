#!/usr/bin/env python3
"""
SRTR Data Parser - Extract transplant outcomes from SRTR Excel files

This script parses the SRTR 2023 Annual Data Report Excel files and extracts
clinically relevant transplant outcomes data for use in the medication adherence system.

Usage:
    python scripts/parse_srtr_data.py [--organ kidney] [--output json|firestore]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


class SRTRDataParser:
    """Parse SRTR transplant outcomes data from Excel files."""

    def __init__(self, data_dir: str = "data/srtr/raw"):
        """
        Initialize parser.

        Args:
            data_dir: Directory containing SRTR Excel files
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path("data/srtr/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Define sheets to extract
        self.kidney_sheets = {
            "graft_survival_age": "KI-F61-tx-adult-GF-LD-5yr-age",
            "graft_survival_race": "KI-F62-tx-adult-GF-LD-5yr-race",
            "graft_survival_sex": "KI-F63-tx-adult-GF-LD-5yr-sex",
            "graft_survival_diagnosis": "KI-F64-tx-adult-GF-LD-5yr-diag",
            "acute_rejection_age": "KI-F67-tx-adult-inc-AR-age",
            "acute_rejection_induction": "KI-F68-tx-adult-inc-AR-ind",
            "egfr_12m_deceased": "KI-F65-tx-adult-egfr-12M-dd",
            "egfr_12m_living": "KI-F66-tx-adult-egfr-12M-ld",
        }

    def parse_kidney_data(self) -> dict[str, Any]:
        """
        Parse kidney transplant outcomes data.

        Returns:
            Dictionary with structured kidney outcomes data
        """
        print("📊 Parsing kidney transplant data...")

        kidney_file = self.data_dir / "Kidney_Figures_Supporting_Information.xlsx"
        if not kidney_file.exists():
            raise FileNotFoundError(f"Kidney data file not found: {kidney_file}")

        results = {}

        # Parse graft survival by age
        print("  → Graft survival by age...")
        results["graft_survival_by_age"] = self._parse_graft_survival_age(kidney_file)

        # Parse acute rejection rates
        print("  → Acute rejection rates...")
        results["acute_rejection_by_age"] = self._parse_acute_rejection_age(kidney_file)

        # Parse graft survival by demographics
        print("  → Graft survival by demographics...")
        results["graft_survival_by_race"] = self._parse_graft_survival_demo(
            kidney_file, self.kidney_sheets["graft_survival_race"]
        )
        results["graft_survival_by_sex"] = self._parse_graft_survival_demo(
            kidney_file, self.kidney_sheets["graft_survival_sex"]
        )

        # Parse kidney function (eGFR)
        print("  → Kidney function (eGFR) at 12 months...")
        results["egfr_12m"] = self._parse_egfr_data(kidney_file)

        print(f"✅ Parsed {len(results)} datasets")
        return results

    def _parse_graft_survival_age(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse graft survival data by age group."""
        sheet_name = self.kidney_sheets["graft_survival_age"]
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Clean up dataframe - skip unnamed columns
        df = df.iloc[:, 8:]  # Skip first 8 unnamed columns
        df = df.dropna(how="all")  # Drop empty rows

        # Extract data
        records = []
        for _, row in df.iterrows():
            years_post = row.iloc[0]
            if pd.isna(years_post):
                continue

            for col in df.columns[1:]:  # Age group columns
                survival_rate = row[col]
                if pd.isna(survival_rate):
                    continue

                records.append(
                    {
                        "metric": "graft_survival",
                        "organ": "kidney",
                        "years_post_transplant": float(years_post),
                        "age_group": col,
                        "survival_rate": float(survival_rate),
                        "source": "SRTR 2023",
                        "donor_type": "living_donor",
                    }
                )

        return records

    def _parse_acute_rejection_age(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse acute rejection incidence by age group."""
        sheet_name = self.kidney_sheets["acute_rejection_age"]
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Clean up dataframe
        df = df.iloc[:, 8:]  # Skip unnamed columns
        df = df.dropna(how="all")

        records = []
        for _, row in df.iterrows():
            year = row.iloc[0]
            if pd.isna(year):
                continue

            for col in df.columns[1:]:  # Age group columns
                rejection_rate = row[col]
                if pd.isna(rejection_rate):
                    continue

                records.append(
                    {
                        "metric": "acute_rejection_rate",
                        "organ": "kidney",
                        "year": int(year),
                        "age_group": col,
                        "rejection_rate": float(rejection_rate),
                        "source": "SRTR 2023",
                    }
                )

        return records

    def _parse_graft_survival_demo(self, file_path: Path, sheet_name: str) -> list[dict[str, Any]]:
        """Parse graft survival by demographic category."""
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = df.iloc[:, 8:]  # Skip unnamed columns
        df = df.dropna(how="all")

        # Determine demographic type from sheet name
        if "race" in sheet_name:
            demo_type = "race"
        elif "sex" in sheet_name:
            demo_type = "sex"
        elif "diag" in sheet_name:
            demo_type = "diagnosis"
        else:
            demo_type = "other"

        records = []
        for _, row in df.iterrows():
            years_post = row.iloc[0]
            if pd.isna(years_post):
                continue

            for col in df.columns[1:]:
                survival_rate = row[col]
                if pd.isna(survival_rate):
                    continue

                records.append(
                    {
                        "metric": "graft_survival",
                        "organ": "kidney",
                        "years_post_transplant": float(years_post),
                        "demographic_type": demo_type,
                        "demographic_value": col,
                        "survival_rate": float(survival_rate),
                        "source": "SRTR 2023",
                    }
                )

        return records

    def _parse_egfr_data(self, file_path: Path) -> list[dict[str, Any]]:
        """Parse kidney function (eGFR) data at 12 months."""
        records = []

        # Parse deceased donor eGFR
        sheet_dd = self.kidney_sheets["egfr_12m_deceased"]
        df_dd = pd.read_excel(file_path, sheet_name=sheet_dd)
        df_dd = df_dd.iloc[:, 8:].dropna(how="all")

        for _, row in df_dd.iterrows():
            year = row.iloc[0]
            if pd.isna(year):
                continue

            # Assuming columns are eGFR ranges or categories
            for col in df_dd.columns[1:]:
                value = row[col]
                if pd.isna(value):
                    continue

                records.append(
                    {
                        "metric": "egfr_12m",
                        "organ": "kidney",
                        "year": int(year) if not pd.isna(year) else None,
                        "donor_type": "deceased",
                        "category": col,
                        "value": float(value),
                        "source": "SRTR 2023",
                    }
                )

        return records

    def save_json(self, data: dict[str, Any], organ: str) -> None:
        """
        Save parsed data to JSON file.

        Args:
            data: Parsed data dictionary
            organ: Organ type (e.g., "kidney")
        """
        output_file = self.output_dir / f"{organ}_outcomes.json"
        print(f"\n💾 Saving to {output_file}...")

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✅ Saved {output_file}")

        # Also save flattened version for easy querying
        flat_file = self.output_dir / f"{organ}_outcomes_flat.json"
        flattened = []
        for dataset_name, records in data.items():
            if isinstance(records, list):
                for record in records:
                    record["dataset"] = dataset_name
                    flattened.append(record)

        with open(flat_file, "w") as f:
            json.dump(flattened, f, indent=2)

        print(f"✅ Saved flattened version: {flat_file}")

    def generate_summary_stats(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate summary statistics from parsed data."""
        summary = {
            "total_records": 0,
            "datasets": {},
            "latest_acute_rejection_rates": {},
            "average_graft_survival_1yr": {},
        }

        # Count records per dataset
        for dataset_name, records in data.items():
            if isinstance(records, list):
                summary["total_records"] += len(records)
                summary["datasets"][dataset_name] = len(records)

        # Extract latest acute rejection rates (2022)
        if "acute_rejection_by_age" in data:
            latest_year = 2022
            for record in data["acute_rejection_by_age"]:
                if record["year"] == latest_year:
                    age_group = record["age_group"]
                    summary["latest_acute_rejection_rates"][age_group] = record["rejection_rate"]

        # Calculate average 1-year graft survival by age
        if "graft_survival_by_age" in data:
            one_year_data = [
                r for r in data["graft_survival_by_age"] if 0.9 <= r["years_post_transplant"] <= 1.1
            ]
            for record in one_year_data:
                age_group = record["age_group"]
                if age_group not in summary["average_graft_survival_1yr"]:
                    summary["average_graft_survival_1yr"][age_group] = []
                summary["average_graft_survival_1yr"][age_group].append(record["survival_rate"])

            # Average the values
            for age_group in summary["average_graft_survival_1yr"]:
                values = summary["average_graft_survival_1yr"][age_group]
                summary["average_graft_survival_1yr"][age_group] = sum(values) / len(values)

        return summary


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Parse SRTR transplant outcomes data")
    parser.add_argument(
        "--organ",
        choices=["kidney", "liver", "heart", "lung", "pancreas", "intestine", "all"],
        default="kidney",
        help="Organ to parse data for",
    )
    parser.add_argument(
        "--output",
        choices=["json", "firestore", "both"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    print("🏥 SRTR Data Parser")
    print("=" * 60)

    srtr_parser = SRTRDataParser()

    try:
        # Parse kidney data
        if args.organ in ["kidney", "all"]:
            kidney_data = srtr_parser.parse_kidney_data()

            # Generate summary stats
            summary = srtr_parser.generate_summary_stats(kidney_data)
            print("\n📈 Summary Statistics:")
            print(f"  Total records: {summary['total_records']}")
            print(f"  Datasets: {len(summary['datasets'])}")

            print("\n  Latest Acute Rejection Rates (2022):")
            for age_group, rate in summary["latest_acute_rejection_rates"].items():
                print(f"    {age_group}: {rate:.2f}%")

            if args.output in ["json", "both"]:
                srtr_parser.save_json(kidney_data, "kidney")

                # Save summary
                summary_file = srtr_parser.output_dir / "kidney_summary.json"
                with open(summary_file, "w") as f:
                    json.dump(summary, f, indent=2)
                print(f"✅ Saved summary: {summary_file}")

            if args.output in ["firestore", "both"]:
                print("\n🔥 Firestore integration not yet implemented")
                print("   (Will be added in next iteration)")

        print("\n✅ Parsing complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
