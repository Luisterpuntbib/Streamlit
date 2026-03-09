"""Manual ZIP pipeline test runner.

Usage:
  python scripts/manual_test_zip_pipeline.py \
    --input-zip C:\\path\\to\\input.zip \
    --excel-file C:\\path\\to\\ECB.xlsx \
    --cnv-file C:\\path\\to\\brl2brf.cnv \
    --output-zip C:\\path\\to\\output.zip

What this script does:
- inspects the input ZIP and lists top-level source folders
- shows the derived Lois ID per source folder
- runs the disk-based ZIP pipeline
- prints per-folder result (success/error + output folder + errors)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline_disk import inspect_input_zip, run_pipeline_disk


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for ZIP pipeline manual testing."""

    parser = argparse.ArgumentParser(description="Manual ZIP pipeline test runner.")
    parser.add_argument("--input-zip", required=True, type=Path, help="Path to input ZIP with source folders")
    parser.add_argument("--excel-file", required=True, type=Path, help="Path to Excel mapping file")
    parser.add_argument("--cnv-file", required=True, type=Path, help="Path to CNV conversion table")
    parser.add_argument("--output-zip", required=True, type=Path, help="Path to output ZIP")
    return parser.parse_args()


def main() -> int:
    """Run ZIP inspection + pipeline execution and print per-folder results.

    Returns:
        Process exit code (0 on successful run, non-zero when no source folders are found).
    """

    args = parse_args()

    print("=== Input inspectie ===")
    inspections = inspect_input_zip(args.input_zip)
    if not inspections:
        print("Geen top-level bronfolders gevonden.")
        return 1

    print(f"Gevonden bronfolders: {len(inspections)}")
    for item in inspections:
        source_folder = item["source_folder"]
        lois_id = item["lois_id"]
        errors = item["errors"]
        print(f"- {source_folder}: Lois ID={lois_id or 'onbekend'}")
        if errors:
            for err in errors:
                print(f"  ! {err}")

    print("\n=== Pipeline uitvoering ===")
    result = run_pipeline_disk(
        input_zip_path=args.input_zip,
        excel_path=args.excel_file,
        cnv_path=args.cnv_file,
        output_zip_path=args.output_zip,
    )

    print(f"Output ZIP: {result.output_zip_path}")
    print(f"Verwerkte bronfolders: {result.total_source_folders}")

    print("\n=== Resultaat per folder ===")
    for item in result.folder_results:
        print(
            f"- bronfolder={item.source_folder} | status={item.status} | "
            f"outputfolder={item.output_folder} | converted={item.converted_count}"
        )
        if item.errors:
            for err in item.errors:
                print(f"  ! {err}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
