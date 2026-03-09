"""Reporting helpers for conversion errors.

This module builds user-facing error lines and persists them into per-folder
report files.
"""

from __future__ import annotations

from difflib import get_close_matches
from pathlib import Path

from excel_mapping import ExcelIndex, normalize_lois_id


def write_error_report(output_folder: Path, lines: list[str]) -> None:
    """Write an ``error_report.txt`` file in an output folder.

    Args:
        output_folder: Destination output folder.
        lines: Error/report lines to write in order.
    """

    report_path = output_folder / "error_report.txt"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_excel_no_match_report(lois_id: str | None, excel_index: ExcelIndex) -> list[str]:
    """Build report lines for missing Excel Lois ID matches.

    Includes the normalized input Lois ID and, when possible, a close-match
    suggestion to highlight likely typos.

    Args:
        lois_id: Input Lois ID derived from source folder/files.
        excel_index: Parsed Excel lookup index.

    Returns:
        List of report lines for ``error_report.txt`` and UI display.
    """

    normalized = normalize_lois_id(lois_id)
    lines = [
        "Geen Excel-match op Lois ID (kolom C).",
        f"Gevonden Lois ID uit input: {normalized or 'onbekend'}",
    ]

    if normalized:
        suggestion = get_close_matches(normalized, list(excel_index.by_lois_id.keys()), n=1, cutoff=0.75)
        if suggestion:
            lines.append("Lois ID in Excel lijkt fout (mogelijke typefout).")
            lines.append(f"Dichtstbijzijnde Lois ID in Excel: {suggestion[0]}")

    return lines
