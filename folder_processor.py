"""Process one Braille source folder using metadata embedded in its XML."""

from __future__ import annotations

from pathlib import Path
import shutil

from braille_models import FolderResult, ProcessingLimits
from brl_conversion import convert_brl_file_to_brf_file, extract_volume_suffix
from naming_rules import make_output_brf_name, make_output_folder_name, make_output_xml_name, sanitize_path_name
from reporting import write_error_report
from validators import (
    determine_file_lois_id_and_consistency,
    determine_folder_identifier,
    list_brl_files,
    list_xml_files,
    validate_source_folder,
)
from xml_metadata import parse_xml_book_record


def infer_lois_id(source_folder: Path, xml_path: Path | None, brl_files: list[Path]) -> str | None:
    """Return the normalized Lois ID found in XML and BRL filenames."""

    lois_id, _ = determine_file_lois_id_and_consistency(
        source_folder,
        xml_files=[xml_path] if xml_path is not None else [],
        brl_files=brl_files,
    )
    return lois_id


def _error_result(
    source_folder: Path,
    output_root: Path,
    errors: list[str],
    *,
    lois_id: str = "",
    book_number: str = "",
    title: str = "",
) -> FolderResult:
    fallback_name = sanitize_path_name(f"{source_folder.name}_error")
    output_folder = output_root / fallback_name
    output_folder.mkdir(parents=True, exist_ok=True)
    write_error_report(output_folder, errors)
    return FolderResult(
        source_folder=source_folder.name,
        output_folder=fallback_name,
        status="error",
        lois_id=lois_id,
        book_number=book_number,
        title=title,
        errors=errors,
    )


def process_source_folder(
    source_folder: Path,
    output_root: Path,
    conversion_table: dict[int, int],
    limits: ProcessingLimits | None = None,
) -> FolderResult:
    """Convert one source folder using its folder number and XML metadata.

    The source folder name supplies the Belgian book number. The explicit XML
    fields ``lois_id`` and ``title`` supply the remaining metadata. The XML
    Lois ID must equal the normalized ID in all XML/BRL filenames. XML bytes
    are copied unchanged; only the output filename changes.

    Args:
        source_folder: Folder containing exactly one XML and one or more BRL files.
        output_root: Destination root for the generated output folder.
        conversion_table: Byte mapping used for BRL-to-BRF conversion.
        limits: Optional folder and BRL-count processing limits.

    Returns:
        Per-folder result. Validation failures still create an ``*_error`` folder.
    """

    validation_errors = validate_source_folder(source_folder, limits=limits)
    if validation_errors:
        return _error_result(source_folder, output_root, validation_errors)

    xml_path = list_xml_files(source_folder)[0]
    brl_files = list_brl_files(source_folder)

    file_lois_id, lois_errors = determine_file_lois_id_and_consistency(
        source_folder,
        xml_files=[xml_path],
        brl_files=brl_files,
    )
    if lois_errors:
        return _error_result(source_folder, output_root, lois_errors)

    book_number, folder_errors = determine_folder_identifier(source_folder)
    if folder_errors or not book_number:
        errors = folder_errors or [
            f"Geen Belgisch boeknummer gevonden in bronfoldernaam '{source_folder.name}'."
        ]
        return _error_result(source_folder, output_root, errors, lois_id=file_lois_id or "")

    try:
        book = parse_xml_book_record(xml_path, book_number)
    except ValueError as exc:
        return _error_result(
            source_folder,
            output_root,
            [str(exc)],
            lois_id=file_lois_id or "",
            book_number=book_number,
        )

    if book.lois_id != file_lois_id:
        errors = [
            "Lois ID in XML-metadata komt niet overeen met XML/BRL-bestandsnamen.",
            f"Lois ID uit XML-metadata: {book.lois_id}",
            f"Lois ID uit bestandsnamen: {file_lois_id or 'onbekend'}",
        ]
        return _error_result(
            source_folder,
            output_root,
            errors,
            lois_id=file_lois_id or "",
            book_number=book.book_number,
            title=book.title,
        )

    output_folder_name = make_output_folder_name(book.book_number, book.title_slug)
    output_folder = output_root / output_folder_name
    output_folder.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(xml_path, output_folder / make_output_xml_name(book.book_number, book.title_slug))

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

    if errors:
        write_error_report(output_folder, errors)

    return FolderResult(
        source_folder=source_folder.name,
        output_folder=output_folder_name,
        status="success" if not errors else "error",
        lois_id=book.lois_id,
        book_number=book.book_number,
        title=book.title,
        converted_count=converted_count,
        errors=errors,
    )
