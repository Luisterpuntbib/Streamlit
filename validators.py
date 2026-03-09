"""Validation helpers for one source folder.

This module validates file presence, BRL naming rules and Lois ID consistency
across multiple sources.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from braille_models import ProcessingLimits
from brl_conversion import extract_volume_suffix
from excel_mapping import normalize_lois_id

LOIS_ID_PATTERN = re.compile(r"(?i)t?\d{5,}")
INPUT_SOURCES = ("folder_name", "xml_filename", "brl_filenames")
ALL_SOURCES = ("folder_name", "xml_filename", "brl_filenames", "xml_content")


def list_xml_files(source_folder: Path) -> list[Path]:
    """List XML files directly inside a source folder."""

    return sorted(path for path in source_folder.iterdir() if path.is_file() and path.suffix.lower() == ".xml")


def list_brl_files(source_folder: Path) -> list[Path]:
    """List BRL files directly inside a source folder."""

    return sorted(path for path in source_folder.iterdir() if path.is_file() and path.suffix.lower() == ".brl")


def validate_brl_filename(brl_path: Path) -> str:
    """Validate BRL filename format and return extracted volume number."""

    return extract_volume_suffix(brl_path.name)


def _extract_lois_ids_from_text(value: str) -> list[str]:
    ids: list[str] = []
    for match in LOIS_ID_PATTERN.findall(value or ""):
        normalized = normalize_lois_id(match)
        if normalized:
            ids.append(normalized)
    return ids


def _extract_lois_ids_from_xml_content(xml_path: Path) -> list[str]:
    try:
        root = ET.parse(xml_path).getroot()
    except Exception:
        return []

    ids: list[str] = []
    for element in root.iter():
        ids.extend(_extract_lois_ids_from_text(element.tag.split("}")[-1]))
        ids.extend(_extract_lois_ids_from_text(element.text or ""))
        for attr_name, attr_value in element.attrib.items():
            ids.extend(_extract_lois_ids_from_text(attr_name))
            ids.extend(_extract_lois_ids_from_text(attr_value or ""))

    return ids


def collect_lois_id_sources(
    source_folder: Path,
    xml_files: list[Path] | None = None,
    brl_files: list[Path] | None = None,
) -> dict[str, list[str]]:
    """Collect candidate Lois IDs from folder and file names (and XML content).

    Args:
        source_folder: Folder being validated.
        xml_files: Optional pre-discovered XML files to reuse.
        brl_files: Optional pre-discovered BRL files to reuse.

    Returns:
        Dict with Lois ID candidates per source channel.
    """

    xml_files = list_xml_files(source_folder) if xml_files is None else xml_files
    brl_files = list_brl_files(source_folder) if brl_files is None else brl_files

    by_source: dict[str, list[str]] = {
        "folder_name": _extract_lois_ids_from_text(source_folder.name),
        "xml_filename": [],
        "brl_filenames": [],
        "xml_content": [],
    }

    if len(xml_files) == 1:
        by_source["xml_filename"] = _extract_lois_ids_from_text(xml_files[0].stem)
        by_source["xml_content"] = _extract_lois_ids_from_xml_content(xml_files[0])

    for brl_file in brl_files:
        by_source["brl_filenames"].extend(_extract_lois_ids_from_text(brl_file.stem))

    return by_source


def determine_lois_id_and_consistency(
    source_folder: Path,
    xml_files: list[Path] | None = None,
    brl_files: list[Path] | None = None,
) -> tuple[str | None, list[str]]:
    """Determine one Lois ID and report inconsistencies.

    Truth source priority is based on input sources:
    folder name -> XML filename -> BRL filenames.
    XML content is only used as an extra consistency check.

    Args:
        source_folder: Folder being evaluated.
        xml_files: Optional pre-discovered XML files.
        brl_files: Optional pre-discovered BRL files.

    Returns:
        Tuple of ``(resolved_lois_id, errors)``. ``resolved_lois_id`` can be
        ``None`` when no usable input Lois ID is found.
    """

    by_source = collect_lois_id_sources(source_folder, xml_files=xml_files, brl_files=brl_files)
    errors: list[str] = []

    source_uniques: dict[str, set[str]] = {key: {value for value in values if value} for key, values in by_source.items()}

    for source_name, unique_values in source_uniques.items():
        if len(unique_values) > 1:
            errors.append(
                f"Inconsistente Lois ID binnen bron '{source_name}' in folder '{source_folder.name}': "
                f"{', '.join(sorted(unique_values))}."
            )

    reference_id: str | None = None
    for source_name in INPUT_SOURCES:
        values = sorted(source_uniques[source_name])
        if values:
            reference_id = values[0]
            break

    if not reference_id:
        errors.append(
            f"Geen bruikbare Lois ID gevonden in folder '{source_folder.name}' "
            "(foldernaam, XML-bestandsnaam of BRL-bestandsnamen)."
        )
        return None, errors

    for source_name in ALL_SOURCES:
        values = sorted(source_uniques[source_name])
        if values and values[0] != reference_id:
            errors.append(
                "Inconsistente Lois ID tussen inputbronnen in folder "
                f"'{source_folder.name}': referentie={reference_id}; {source_name}={values[0]}."
            )

    return reference_id, errors


def validate_source_folder(source_folder: Path, limits: ProcessingLimits | None = None) -> list[str]:
    """Validate one source folder before conversion.

    Validation rules:
    - exactly one XML file
    - at least one BRL file
    - each BRL filename must match ``*_NNN.brl``
    - optional BRL count limit from ``ProcessingLimits``
    - Lois ID consistency across source channels

    Args:
        source_folder: Folder to validate.
        limits: Optional processing limits.

    Returns:
        List of validation error messages. Empty list means valid.
    """

    errors: list[str] = []
    xml_files = list_xml_files(source_folder)
    brl_files = list_brl_files(source_folder)

    if len(xml_files) != 1:
        errors.append(f"Bronfolder '{source_folder.name}' moet exact 1 XML-bestand bevatten, gevonden: {len(xml_files)}.")

    if len(brl_files) < 1:
        errors.append(f"Bronfolder '{source_folder.name}' moet minstens 1 .brl-bestand bevatten.")

    if limits is not None and len(brl_files) > limits.max_brl_per_folder:
        errors.append(
            f"Bronfolder '{source_folder.name}' overschrijdt maximum .brl-bestanden: "
            f"{len(brl_files)} > {limits.max_brl_per_folder}."
        )

    for brl_file in brl_files:
        try:
            validate_brl_filename(brl_file)
        except ValueError as exc:
            errors.append(str(exc))

    _, lois_errors = determine_lois_id_and_consistency(source_folder, xml_files=xml_files, brl_files=brl_files)
    errors.extend(lois_errors)

    return errors
