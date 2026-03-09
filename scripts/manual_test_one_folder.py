"""Manual one-folder test runner for Braille conversion.

Usage:
  python scripts/manual_test_one_folder.py \
    --source-folder C:\\path\\to\\source_folder \
    --excel-file C:\\path\\to\\mapping.xlsx \
    --cnv-file C:\\path\\to\\table.cnv \
    --output-root C:\\path\\to\\output_root

What this script does:
- validates one source folder (exact 1 XML, at least 1 BRL, BRL names end with _NNN.brl)
- reads Excel mapping (row 1 skipped, title in column B, Lois ID in column C, target book number in column E)
- reads CNV table as byte-mapping dict[int, int]
- processes the folder and writes output files to the output root
- prints a clear summary of discovered input and generated output

Notes:
- XML content is never modified; only the XML filename is changed in output.
- Matching priority for Lois ID: folder name -> XML filename -> BRL filename.
- Lois IDs are normalized before matching (trim/lowercase/remove leading t/T/keep digits).
- This script is intentionally local/manual and does not touch Streamlit UI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brl_conversion import parse_cnv_table_bytes
from excel_mapping import build_excel_index, parse_excel_mapping_file
from folder_processor import infer_lois_id, process_source_folder, resolve_book_record
from validators import list_brl_files, list_xml_files, validate_source_folder


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for one-folder manual processing."""

    parser = argparse.ArgumentParser(description="Manual test for one Braille source folder.")
    parser.add_argument("--source-folder", required=True, type=Path, help="Path to one source folder")
    parser.add_argument("--excel-file", required=True, type=Path, help="Path to Excel mapping file")
    parser.add_argument("--cnv-file", required=True, type=Path, help="Path to .cnv conversion table")
    parser.add_argument("--output-root", required=True, type=Path, help="Output root directory")
    return parser.parse_args()


def main() -> int:
    """Run the manual one-folder conversion flow and print a summary.

    Returns:
        Process exit code (0 on success, non-zero on validation/processing errors).
    """

    args = parse_args()

    source_folder = args.source_folder
    excel_file = args.excel_file
    cnv_file = args.cnv_file
    output_root = args.output_root

    if not source_folder.is_dir():
        print(f"ERROR: source folder bestaat niet: {source_folder}")
        return 1
    if not excel_file.is_file():
        print(f"ERROR: excel-bestand bestaat niet: {excel_file}")
        return 1
    if not cnv_file.is_file():
        print(f"ERROR: cnv-bestand bestaat niet: {cnv_file}")
        return 1

    output_root.mkdir(parents=True, exist_ok=True)

    xml_files = list_xml_files(source_folder)
    brl_files = list_brl_files(source_folder)

    print("=== Input detectie ===")
    if xml_files:
        print(f"Gevonden XML-bestand: {xml_files[0]}")
    else:
        print("Gevonden XML-bestand: GEEN")

    print("Gevonden .brl bestanden:")
    if brl_files:
        for path in brl_files:
            print(f"- {path}")
    else:
        print("- GEEN")

    validation_errors = validate_source_folder(source_folder)
    if validation_errors:
        print("\n=== Validatiefouten ===")
        for err in validation_errors:
            print(f"- {err}")
        return 2

    records = parse_excel_mapping_file(excel_file)
    excel_index = build_excel_index(records)
    conversion_table = parse_cnv_table_bytes(cnv_file.read_bytes())

    lois_id = infer_lois_id(source_folder, xml_files[0] if xml_files else None, brl_files)
    book = resolve_book_record(lois_id, excel_index)

    print("\n=== Koppeling ===")
    print(f"Afgeleide Lois ID: {lois_id or 'GEEN'}")
    if book is None:
        print("Gekoppeld boeknummer en titel: GEEN MATCH IN EXCEL")
    else:
        print(f"Gekoppeld boeknummer en titel: {book.book_number} | {book.title}")

    result = process_source_folder(
        source_folder=source_folder,
        output_root=output_root,
        excel_index=excel_index,
        conversion_table=conversion_table,
    )

    output_folder = output_root / result.output_folder

    print("\n=== Output ===")
    print(f"Outputfolder: {output_folder}")
    print(f"Status: {result.status}")
    if result.errors:
        print("Fouten:")
        for err in result.errors:
            print(f"- {err}")

    print("Gegenereerde bestanden:")
    if output_folder.exists():
        generated_files = sorted(path for path in output_folder.iterdir() if path.is_file())
        if generated_files:
            for path in generated_files:
                print(f"- {path.name}")
        else:
            print("- GEEN")
    else:
        print("- GEEN (outputfolder ontbreekt)")

    return 0 if result.status == "success" else 3


if __name__ == "__main__":
    sys.exit(main())
