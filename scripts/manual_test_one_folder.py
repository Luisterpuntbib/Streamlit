"""Manually process one XML-metadata-based Braille source folder.

Usage:
  python scripts/manual_test_one_folder.py \
    --source-folder C:\\path\\to\\65856 \
    --cnv-file C:\\path\\to\\brl2brf.cnv \
    --output-root C:\\path\\to\\output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from brl_conversion import parse_cnv_table_bytes
from folder_processor import process_source_folder
from validators import list_brl_files, list_xml_files


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for one-folder manual processing."""

    parser = argparse.ArgumentParser(description="Test one Braille source folder without Excel.")
    parser.add_argument("--source-folder", required=True, type=Path)
    parser.add_argument("--cnv-file", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """Process one folder and print detected input, metadata and output."""

    args = parse_args()
    if not args.source_folder.is_dir():
        print(f"ERROR: bronfolder bestaat niet: {args.source_folder}")
        return 1
    if not args.cnv_file.is_file():
        print(f"ERROR: CNV-bestand bestaat niet: {args.cnv_file}")
        return 1

    args.output_root.mkdir(parents=True, exist_ok=True)
    xml_files = list_xml_files(args.source_folder)
    brl_files = list_brl_files(args.source_folder)

    print("=== Input ===")
    print(f"Bronfolder: {args.source_folder}")
    print(f"XML: {xml_files[0].name if len(xml_files) == 1 else f'{len(xml_files)} bestanden'}")
    print("BRL-bestanden:")
    for brl_file in brl_files:
        print(f"- {brl_file.name}")

    table = parse_cnv_table_bytes(args.cnv_file.read_bytes())
    result = process_source_folder(args.source_folder, args.output_root, table)

    print("\n=== Resultaat ===")
    print(f"Status: {result.status}")
    print(f"Belgisch boeknummer: {result.book_number or 'onbekend'}")
    print(f"Lois ID: {result.lois_id or 'onbekend'}")
    print(f"Titel: {result.title or 'onbekend'}")
    print(f"Outputfolder: {result.output_folder}")
    for error in result.errors:
        print(f"FOUT: {error}")

    output_folder = args.output_root / result.output_folder
    print("Gegenereerde bestanden:")
    for path in sorted(output_folder.iterdir()):
        if path.is_file():
            print(f"- {path.name}")
    return 0 if result.status == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
