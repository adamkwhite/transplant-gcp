#!/usr/bin/env python3
"""
SRTR Data Parser v2 - Multi-Organ Support

Parses SRTR 2023 Annual Data Report Excel files for all organ types.
Uses pattern matching to handle organ-specific naming conventions.

Usage:
    python scripts/parse_srtr_data_v2.py --organ kidney
    python scripts/parse_srtr_data_v2.py --organ lung
    python scripts/parse_srtr_data_v2.py --organ all
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Organ prefix mapping
ORGAN_PREFIXES = {
    "kidney": "KI",
    "liver": "LI",
    "heart": "HR",
    "lung": "LU",
    "pancreas": "PA",
    "intestine": "IN",
}


class SRTRDataParserV2:
    """Universal SRTR data parser for all organ types."""

    def __init__(self, data_dir: str = "data/srtr/raw"):
        """Initialize parser."""
        self.data_dir = Path(data_dir)
        self.output_dir = Path("data/srtr/processed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_organ_data(self, organ: str) -> dict[str, Any]:
        """
        Parse transplant outcomes for any organ.

        Args:
            organ: Organ type (kidney, liver, heart, lung, pancreas, intestine)

        Returns:
            Dictionary with structured outcomes data
        """
        organ_lower = organ.lower()
        if organ_lower not in ORGAN_PREFIXES:
            raise ValueError(f"Unknown organ: {organ}")

        prefix = ORGAN_PREFIXES[organ_lower]
        organ_title = organ.capitalize()

        print(f"📊 Parsing {organ_title} transplant data...")

        # Find Excel file
        file_path = self.data_dir / f"{organ_title}_Figures_Supporting_Information.xlsx"
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        results = {}

        # Parse acute rejection rates
        print("  → Acute rejection rates...")
        results["acute_rejection_by_age"] = self._parse_pattern(
            file_path, prefix, "inc-AR-age", "acute_rejection_rate", organ_lower
        )

        # Parse patient survival
        print("  → Patient survival rates...")
        results["patient_survival_5yr"] = self._parse_pattern(
            file_path, prefix, "pat-surv-DD-5y", "patient_survival", organ_lower
        )

        # Organ-specific function metrics
        if organ_lower == "kidney":
            print("  → Kidney function (eGFR)...")
            results["function_12m"] = self._parse_pattern(
                file_path, prefix, "egfr-12M", "egfr", organ_lower
            )
        elif organ_lower == "lung":
            print("  → Lung function (FEV1)...")
            # LU doesn't have standard FEV sheets in same format, skip for now

        print(f"  ✅ Parsed {sum(len(v) for v in results.values() if isinstance(v, list))} records")

        return results

    def _parse_pattern(
        self,
        file_path: Path,
        prefix: str,
        pattern: str,
        metric_name: str,
        organ: str,
    ) -> list[dict[str, Any]]:
        """
        Generic pattern-based sheet parser.

        Args:
            file_path: Excel file path
            prefix: Organ prefix (e.g., "KI", "LU")
            pattern: Pattern to match in sheet name (e.g., "inc-AR-age")
            metric_name: Metric name for output
            organ: Organ type

        Returns:
            List of parsed records
        """
        xl_file = pd.ExcelFile(file_path)

        # Find matching sheets
        matching_sheets = [
            sheet for sheet in xl_file.sheet_names if sheet.startswith(prefix) and pattern in sheet
        ]

        if not matching_sheets:
            print(f"    ⚠️  No sheets found matching pattern: {prefix}-*{pattern}*")
            return []

        all_records = []

        for sheet_name in matching_sheets:
            try:
                all_records.extend(self._parse_sheet(file_path, sheet_name, metric_name, organ))
            except Exception as e:
                print(f"    ⚠️  Error parsing {sheet_name}: {e}")
                continue

        return all_records

    def _parse_sheet(
        self,
        file_path: Path,
        sheet_name: str,
        metric_name: str,
        organ: str,
    ) -> list[dict[str, Any]]:
        """Parse a single matched sheet into records."""
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Clean up - skip unnamed columns
        df = df.iloc[:, 8:]  # Skip first 8 columns (formatting)
        df = df.dropna(how="all")

        # Determine what the first column represents. Loop-invariant, so it is
        # resolved once here rather than re-evaluated per cell as it was.
        first_col_name = df.columns[0]
        is_year_column = "year" in first_col_name.lower() or (
            "year" in sheet_name.lower() or "inc-AR" in sheet_name
        )

        records: list[dict[str, Any]] = []
        for _, row in df.iterrows():
            time_or_year = row.iloc[0]
            if pd.isna(time_or_year):
                continue
            records.extend(
                self._records_from_row(
                    row=row,
                    columns=df.columns[1:],
                    time_or_year=time_or_year,
                    is_year_column=is_year_column,
                    metric_name=metric_name,
                    organ=organ,
                    sheet_name=sheet_name,
                )
            )
        return records

    @staticmethod
    def _records_from_row(
        *,
        row: Any,
        columns: Any,
        time_or_year: Any,
        is_year_column: bool,
        metric_name: str,
        organ: str,
        sheet_name: str,
    ) -> list[dict[str, Any]]:
        """One record per non-null demographic/age column in a row."""
        records: list[dict[str, Any]] = []
        for col in columns:
            value = row[col]
            if pd.isna(value):
                continue

            record: dict[str, Any] = {
                "metric": metric_name,
                "organ": organ,
                "source": "SRTR 2023",
                "sheet": sheet_name,
            }

            if is_year_column:
                record["year"] = int(time_or_year)
            else:
                record["time_value"] = float(time_or_year)

            record["demographic"] = col
            record["value"] = float(value)
            records.append(record)
        return records

    def save_json(self, data: dict[str, Any], organ: str) -> None:
        """Save parsed data to JSON."""
        output_file = self.output_dir / f"{organ.lower()}_outcomes.json"
        print(f"\n💾 Saving to {output_file}...")

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        # Flattened version
        flat_file = self.output_dir / f"{organ.lower()}_outcomes_flat.json"
        flattened = []

        for dataset_name, records in data.items():
            if isinstance(records, list):
                for record in records:
                    record["dataset"] = dataset_name
                    flattened.append(record)

        with open(flat_file, "w") as f:
            json.dump(flattened, f, indent=2)

        # Generate summary
        summary = self._generate_summary(data, organ)
        summary_file = self.output_dir / f"{organ.lower()}_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        print(f"✅ Saved: {output_file}")
        print(f"✅ Saved: {flat_file}")
        print(f"✅ Saved: {summary_file}")

    def _generate_summary(self, data: dict[str, Any], organ: str) -> dict[str, Any]:
        """Generate summary statistics."""
        summary = {
            "organ": organ,
            "total_records": sum(len(v) for v in data.values() if isinstance(v, list)),
            "datasets": {k: len(v) for k, v in data.items() if isinstance(v, list)},
            "latest_acute_rejection_rates": {},
        }

        # Extract latest rejection rates
        if "acute_rejection_by_age" in data and data["acute_rejection_by_age"]:
            # Find most recent year
            years = [r.get("year") for r in data["acute_rejection_by_age"] if "year" in r]
            if years:
                latest_year = max(years)
                for record in data["acute_rejection_by_age"]:
                    if record.get("year") == latest_year:
                        demo = record.get("demographic", "unknown")
                        summary["latest_acute_rejection_rates"][demo] = record["value"]

        return summary


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Parse SRTR transplant outcomes (all organs)")
    parser.add_argument(
        "--organ",
        choices=list(ORGAN_PREFIXES.keys()) + ["all"],
        default="kidney",
        help="Organ to parse",
    )

    args = parser.parse_args()

    print("🏥 SRTR Data Parser v2 - Multi-Organ Support")
    print("=" * 60)

    srtr_parser = SRTRDataParserV2()

    organs_to_parse = list(ORGAN_PREFIXES.keys()) if args.organ == "all" else [args.organ]

    try:
        for organ in organs_to_parse:
            data = srtr_parser.parse_organ_data(organ)
            srtr_parser.save_json(data, organ)

            # Show summary
            summary_file = srtr_parser.output_dir / f"{organ}_summary.json"
            with open(summary_file) as f:
                summary = json.load(f)

            print(f"\n📈 {organ.capitalize()} Summary:")
            print(f"  Total records: {summary['total_records']}")
            if summary.get("latest_acute_rejection_rates"):
                print("  Latest Rejection Rates:")
                for demo, rate in list(summary["latest_acute_rejection_rates"].items())[:4]:
                    print(f"    {demo}: {rate:.2f}%")

            print()

        print("\n✅ All organs parsed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
