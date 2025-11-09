#!/usr/bin/env python3
"""
Load SRTR outcomes data into Firestore

This script loads the parsed SRTR data from JSON files into Firestore
for runtime querying by the ADK agents.

Usage:
    python scripts/load_srtr_to_firestore.py [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

from google.cloud import firestore


def load_to_firestore(data_file: Path, collection_name: str, dry_run: bool = False):
    """
    Load JSON data into Firestore collection.

    Args:
        data_file: Path to JSON file with data
        collection_name: Firestore collection name
        dry_run: If True, don't actually write to Firestore
    """
    print(f"📂 Loading {data_file.name} into '{collection_name}'...")

    # Load JSON data
    with open(data_file) as f:
        records = json.load(f)

    if not isinstance(records, list):
        print(f"❌ Error: Expected list of records, got {type(records)}")
        return

    print(f"  Found {len(records)} records")

    if dry_run:
        print("  [DRY RUN] Would write to Firestore (skipping)")
        # Show first 3 records
        print("\n  Sample records (first 3):")
        for i, record in enumerate(records[:3], 1):
            print(f"    {i}. {record}")
        return

    # Initialize Firestore
    db = firestore.Client()
    collection_ref = db.collection(collection_name)

    # Batch write
    batch = db.batch()
    batch_count = 0
    total_written = 0

    for record in records:
        # Generate document ID from record data
        doc_id = generate_doc_id(record)
        doc_ref = collection_ref.document(doc_id)

        batch.set(doc_ref, record)
        batch_count += 1

        # Firestore batch limit is 500
        if batch_count >= 500:
            batch.commit()
            total_written += batch_count
            print(f"  ✓ Written {total_written}/{len(records)} records...")
            batch = db.batch()
            batch_count = 0

    # Commit remaining records
    if batch_count > 0:
        batch.commit()
        total_written += batch_count

    print(f"  ✅ Wrote {total_written} records to Firestore")


def generate_doc_id(record: dict) -> str:
    """
    Generate a unique document ID from record fields.

    Args:
        record: Data record

    Returns:
        Unique document ID
    """
    metric = record.get("metric", "unknown")
    organ = record.get("organ", "unknown")

    # Build ID from available fields
    id_parts = [organ, metric]

    if "age_group" in record:
        id_parts.append(record["age_group"].replace(" ", "_"))

    if "year" in record:
        id_parts.append(str(record["year"]))
    elif "years_post_transplant" in record:
        years = record["years_post_transplant"]
        id_parts.append(f"{years:.2f}yrs")

    if "demographic_type" in record:
        id_parts.append(record["demographic_type"])
        id_parts.append(record.get("demographic_value", "").replace(" ", "_"))

    return "_".join(id_parts)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Load SRTR data to Firestore")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be loaded without writing",
    )
    parser.add_argument(
        "--collection",
        default="srtr_outcomes",
        help="Firestore collection name",
    )

    args = parser.parse_args()

    print("🔥 SRTR Firestore Loader")
    print("=" * 60)

    data_dir = Path("data/srtr/processed")
    flat_file = data_dir / "kidney_outcomes_flat.json"

    if not flat_file.exists():
        print(f"❌ Error: Data file not found: {flat_file}")
        print("   Run: python scripts/parse_srtr_data.py first")
        sys.exit(1)

    try:
        load_to_firestore(flat_file, args.collection, dry_run=args.dry_run)

        if not args.dry_run:
            print("\n✅ Data loaded successfully!")
            print(f"   Collection: {args.collection}")
            print("   Access from agents using Firestore client")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
