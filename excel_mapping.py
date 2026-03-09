"""Excel parsing and indexing utilities for Braille conversion.

This module reads the mapping workbook and validates required columns:
- column B: title
- column C: Lois ID
- column E: target book number
Row 1 is skipped as a header/title row.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from braille_models import BookRecord
from naming_rules import make_title_slug


@dataclass(frozen=True)
class ExcelIndex:
    """Lookup container for Excel records.

    Attributes:
        by_lois_id: Records keyed by normalized Lois ID (column C).
        by_book_number: Records keyed by target book number (column E).
    """

    by_lois_id: dict[str, BookRecord]
    by_book_number: dict[str, BookRecord]


def normalize_lois_id(value: str | None) -> str:
    """Normalize a Lois ID value for stable matching.

    Rules:
    - trim whitespace
    - lowercase
    - remove a leading 't' prefix when present
    - keep only numeric characters

    Args:
        value: Raw Lois ID value from Excel or filenames.

    Returns:
        Normalized numeric Lois ID string, or an empty string when invalid.
    """

    raw = "" if value is None else str(value)
    normalized = raw.strip().lower()
    if normalized.startswith("t"):
        normalized = normalized[1:]
    digits = re.sub(r"\D", "", normalized)
    return digits


def parse_excel_mapping_file(excel_path: Path, sheet_name: str | int | None = None) -> list[BookRecord]:
    """Read and validate mapping rows from the Excel file.

    Validation rules:
    - row 1 is ignored
    - column B (title), C (Lois ID), and E (book number) are required
    - normalized Lois ID and book number must be unique
    - slugified title must not be empty

    Args:
        excel_path: Path to the Excel workbook.
        sheet_name: Optional sheet selector; defaults to first sheet.

    Returns:
        List of validated ``BookRecord`` instances.

    Raises:
        ValueError: If the workbook/sheet has invalid or missing mapping data.
    """

    selected_sheet: str | int = 0 if sheet_name is None else sheet_name
    df = pd.read_excel(excel_path, header=None, sheet_name=selected_sheet)

    if isinstance(df, dict):
        if not df:
            raise ValueError("Excel bevat geen leesbare sheets.")
        df = next(iter(df.values()))

    records: list[BookRecord] = []
    seen_book_numbers: set[str] = set()
    seen_lois_ids: set[str] = set()

    for idx, row in df.iterrows():
        excel_row = idx + 1
        if excel_row == 1:
            continue

        title_raw = row.iloc[1] if len(row) > 1 else None      # Kolom B
        lois_id_raw = row.iloc[2] if len(row) > 2 else None    # Kolom C
        book_number_raw = row.iloc[4] if len(row) > 4 else None  # Kolom E

        title = "" if pd.isna(title_raw) else str(title_raw).strip()
        lois_id_input = "" if pd.isna(lois_id_raw) else str(lois_id_raw).strip()
        lois_id = normalize_lois_id(lois_id_input)
        book_number = "" if pd.isna(book_number_raw) else str(book_number_raw).strip()

        if not title and not lois_id_input and not book_number:
            continue
        if not title:
            raise ValueError(f"Excel rij {excel_row}: kolom B (titel) is leeg.")
        if not lois_id:
            raise ValueError(f"Excel rij {excel_row}: kolom C (Lois ID) is leeg of ongeldig.")
        if not book_number:
            raise ValueError(f"Excel rij {excel_row}: kolom E (boeknummer) is leeg.")

        if lois_id in seen_lois_ids:
            raise ValueError(f"Excel rij {excel_row}: duplicaat Lois ID '{lois_id}'.")
        if book_number in seen_book_numbers:
            raise ValueError(f"Excel rij {excel_row}: duplicaat boeknummer '{book_number}'.")

        slug = make_title_slug(title)
        if not slug:
            raise ValueError(f"Excel rij {excel_row}: titel_slug is leeg na normalisatie.")

        records.append(
            BookRecord(
                excel_row=excel_row,
                title=title,
                title_slug=slug,
                book_number=book_number,
                lois_id=lois_id,
            )
        )
        seen_lois_ids.add(lois_id)
        seen_book_numbers.add(book_number)

    if not records:
        raise ValueError("Excel bevat geen bruikbare boekgegevens vanaf rij 2.")

    return records


def build_excel_index(records: list[BookRecord]) -> ExcelIndex:
    """Build fast lookups from parsed Excel records.

    Args:
        records: Validated ``BookRecord`` list.

    Returns:
        ``ExcelIndex`` with lookup tables by Lois ID and by book number.
    """

    by_lois_id = {record.lois_id: record for record in records}
    by_book_number = {record.book_number: record for record in records}
    return ExcelIndex(by_lois_id=by_lois_id, by_book_number=by_book_number)
