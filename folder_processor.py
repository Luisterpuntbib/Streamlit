"""Per-folder processing for BRL to BRF conversion.

This module validates one source folder, resolves the matching Excel record,
renames/copies XML unchanged, converts BRL files, and writes folder reports.
"""

from __future__ import annotations

from pathlib import Path
import shutil

from braille_models import BookRecord, FolderResult, ProcessingLimits
from brl_conversion import convert_brl_file_to_brf_file, extract_volume_suffix
from excel_mapping import ExcelIndex, normalize_lois_id
from naming_rules import make_output_brf_name, make_output_folder_name, make_output_xml_name, sanitize_path_name
from reporting import build_excel_no_match_report, write_error_report
from validators import (
    determine_file_lois_id_and_consistency,
    determine_folder_identifier,
    list_brl_files,
    list_xml_files,
    validate_source_folder,
)


def infer_lois_id(source_folder: Path, xml_path: Path | None, brl_files: list[Path]) -> str | None:
    """Infer the normalized Lois ID for one source folder.

    Args:
        source_folder: Folder being processed.
        xml_path: Optional XML file path for this folder.
        brl_files: BRL files for this folder.

    Returns:
        Normalized Lois ID or ``None`` when no usable value is found.
    """

    lois_id, _ = determine_file_lois_id_and_consistency(
        source_folder,
        xml_files=[xml_path] if xml_path is not None else [],
        brl_files=brl_files,
    )
    return lois_id


def resolve_book_record(lois_id: str | None, excel_index: ExcelIndex):
    """Resolve the Excel record by normalized Lois ID.

    Args:
        lois_id: Input Lois ID candidate.
        excel_index: Excel lookup index.

    Returns:
        Matching ``BookRecord`` or ``None`` if no exact match exists.
    """

    if not lois_id:
        return None
    normalized = normalize_lois_id(lois_id)
    if not normalized:
        return None
    return excel_index.by_lois_id.get(normalized)


def resolve_input_book_record(
    folder_identifier: str | None,
    file_lois_id: str | None,
    excel_index: ExcelIndex,
) -> tuple[BookRecord | None, list[str]]:
    """Resolve old and new delivery identifiers to one Excel record.

    Legacy folders use the Lois ID from Excel column C in their folder name.
    New folders use the Belgian book number from column E. In both formats,
    XML and BRL filenames must contain the Lois ID from column C.
    """

    normalized_folder = normalize_lois_id(folder_identifier)
    normalized_file_lois = normalize_lois_id(file_lois_id)

    by_book = excel_index.by_book_number.get(normalized_folder) if normalized_folder else None
    by_lois = excel_index.by_lois_id.get(normalized_folder) if normalized_folder else None

    if by_book is not None and by_lois is not None and by_book != by_lois:
        return None, [
            f"Foldernummer {normalized_folder} is dubbelzinnig: het matcht zowel Excel kolom C "
            "als kolom E op verschillende rijen."
        ]

    book = by_book or by_lois
    if book is None and not normalized_folder:
        book = excel_index.by_lois_id.get(normalized_file_lois) if normalized_file_lois else None

    if book is None:
        if normalized_folder and normalized_folder != normalized_file_lois:
            return None, [
                "Geen Excel-match voor het nummer uit de bronfolder.",
                f"Gevonden foldernummer: {normalized_folder}",
                "Verwacht een match met Lois ID (kolom C) of boeknummer (kolom E).",
                f"Gevonden Lois ID in XML/BRL: {normalized_file_lois or 'onbekend'}",
            ]
        return None, build_excel_no_match_report(normalized_file_lois or normalized_folder, excel_index)

    if normalized_file_lois != book.lois_id:
        return book, [
            "Lois ID in XML/BRL komt niet overeen met Excel kolom C.",
            f"Gevonden foldernummer: {normalized_folder or 'onbekend'}",
            f"Gevonden Lois ID in XML/BRL: {normalized_file_lois or 'onbekend'}",
            f"Excel rij {book.excel_row}, kolom C: {book.lois_id}",
            f"Excel rij {book.excel_row}, kolom E: {book.book_number}",
        ]

    return book, []


def process_source_folder(
    source_folder: Path,
    output_root: Path,
    excel_index: ExcelIndex,
    conversion_table: dict[int, int],
    limits: ProcessingLimits | None = None,
) -> FolderResult:
    """Process one source folder into one output folder.

    Flow:
    1. Validate folder structure and Lois ID consistency.
    2. Resolve Excel record by Lois ID (column C).
    3. Copy XML unchanged but renamed.
    4. Convert BRL files to BRF.

    Validation behavior:
    - on any validation or matching error, an ``*_error`` output folder is
      still created with ``error_report.txt``.

    Args:
        source_folder: Input folder containing XML and BRL files.
        output_root: Destination root where one output folder is created.
        excel_index: Parsed Excel lookup index.
        conversion_table: Byte mapping used for BRL->BRF conversion.
        limits: Optional processing limits.

    Returns:
        ``FolderResult`` with status, counts and error details.
    """

    validation_errors = validate_source_folder(source_folder, limits=limits)
    if validation_errors:
        fallback_name = sanitize_path_name(f"{source_folder.name}_error")
        output_folder = output_root / fallback_name
        output_folder.mkdir(parents=True, exist_ok=True)
        write_error_report(output_folder, validation_errors)
        return FolderResult(
            source_folder=source_folder.name,
            output_folder=fallback_name,
            status="error",
            errors=validation_errors,
        )

    xml_path = list_xml_files(source_folder)[0]
    brl_files = list_brl_files(source_folder)

    lois_id, lois_errors = determine_file_lois_id_and_consistency(
        source_folder,
        xml_files=[xml_path],
        brl_files=brl_files,
    )
    if lois_errors:
        fallback_name = sanitize_path_name(f"{source_folder.name}_error")
        output_folder = output_root / fallback_name
        output_folder.mkdir(parents=True, exist_ok=True)
        write_error_report(output_folder, lois_errors)
        return FolderResult(
            source_folder=source_folder.name,
            output_folder=fallback_name,
            status="error",
            errors=lois_errors,
        )

    folder_identifier, folder_errors = determine_folder_identifier(source_folder)
    if folder_errors:
        fallback_name = sanitize_path_name(f"{source_folder.name}_error")
        output_folder = output_root / fallback_name
        output_folder.mkdir(parents=True, exist_ok=True)
        write_error_report(output_folder, folder_errors)
        return FolderResult(
            source_folder=source_folder.name,
            output_folder=fallback_name,
            status="error",
            lois_id=lois_id or "",
            errors=folder_errors,
        )

    book, match_errors = resolve_input_book_record(folder_identifier, lois_id, excel_index)

    if match_errors:
        fallback_name = sanitize_path_name(f"{source_folder.name}_error")
        output_folder = output_root / fallback_name
        output_folder.mkdir(parents=True, exist_ok=True)
        write_error_report(output_folder, match_errors)
        return FolderResult(
            source_folder=source_folder.name,
            output_folder=fallback_name,
            status="error",
            lois_id=lois_id or "",
            book_number=book.book_number if book else "",
            title=book.title if book else "",
            errors=match_errors,
        )

    if book is None:
        raise RuntimeError("Boekrecord ontbreekt zonder gerapporteerde matchfout.")

    output_folder_name = make_output_folder_name(book.book_number, book.title_slug)
    output_folder = output_root / output_folder_name
    output_folder.mkdir(parents=True, exist_ok=True)

    new_xml_name = make_output_xml_name(book.book_number, book.title_slug)
    shutil.copyfile(xml_path, output_folder / new_xml_name)

    converted_count = 0
    errors: list[str] = []

    for brl_file in brl_files:
        try:
            volume = extract_volume_suffix(brl_file.name)
            brf_name = make_output_brf_name(book.book_number, volume, book.title_slug)
            convert_brl_file_to_brf_file(brl_file, output_folder / brf_name, conversion_table)
            converted_count += 1
        except Exception as exc:
            errors.append(f"{brl_file.name}: {exc}")

    status = "success" if not errors else "error"
    if errors:
        write_error_report(output_folder, errors)

    return FolderResult(
        source_folder=source_folder.name,
        output_folder=output_folder_name,
        status=status,
        lois_id=lois_id or "",
        book_number=book.book_number,
        title=book.title,
        converted_count=converted_count,
        errors=errors,
    )
