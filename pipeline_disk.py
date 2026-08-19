"""Disk-based ZIP pipeline for multi-folder Braille conversion.

This pipeline unpacks one input ZIP, processes top-level source folders
sequentially, and creates one output ZIP containing all output folders.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from braille_models import PipelineResult, ProcessingLimits
from brl_conversion import parse_cnv_table_bytes
from excel_mapping import build_excel_index, parse_excel_mapping_file
from folder_processor import process_source_folder
from validators import (
    determine_file_lois_id_and_consistency,
    determine_folder_identifier,
    list_brl_files,
    list_xml_files,
)


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            member_path = destination / member.filename
            resolved = member_path.resolve()
            if not str(resolved).startswith(str(destination.resolve())):
                raise ValueError(f"Onveilig pad in zip: {member.filename}")
        archive.extractall(destination)


def _discover_top_level_source_folders(input_root: Path) -> list[Path]:
    return sorted(path for path in input_root.iterdir() if path.is_dir())


def _ensure_unique_folder_name(name: str, used_names: set[str]) -> str:
    if name not in used_names:
        used_names.add(name)
        return name

    suffix = 2
    while True:
        candidate = f"{name}_{suffix}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate
        suffix += 1


def _zip_output_root(output_root: Path, output_zip_path: Path) -> None:
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_root.rglob("*")):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(output_root))


def inspect_input_zip(input_zip_path: Path) -> list[dict[str, object]]:
    """Inspect input ZIP contents before processing.

    Args:
        input_zip_path: Path to the uploaded input ZIP.

    Returns:
        Per-source-folder records with keys:
        - ``source_folder``
        - ``lois_id`` (derived/normalized)
        - ``errors`` (consistency or structure messages)

    Raises:
        FileNotFoundError: If the ZIP does not exist.
        ValueError: If ZIP extraction detects unsafe paths.
    """

    if not input_zip_path.is_file():
        raise FileNotFoundError(f"Input zip niet gevonden: {input_zip_path}")

    inspections: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="braille_inspect_") as temp_dir:
        input_root = Path(temp_dir) / "input"
        input_root.mkdir(parents=True, exist_ok=True)
        _safe_extract_zip(input_zip_path, input_root)

        for source_folder in _discover_top_level_source_folders(input_root):
            xml_files = list_xml_files(source_folder)
            brl_files = list_brl_files(source_folder)
            folder_identifier, folder_errors = determine_folder_identifier(source_folder)
            lois_id, errors = determine_file_lois_id_and_consistency(
                source_folder,
                xml_files=xml_files,
                brl_files=brl_files,
            )
            inspections.append(
                {
                    "source_folder": source_folder.name,
                    "folder_identifier": folder_identifier,
                    "lois_id": lois_id,
                    "errors": folder_errors + errors,
                }
            )

    return inspections


def run_pipeline_disk(
    input_zip_path: Path,
    excel_path: Path,
    cnv_path: Path,
    output_zip_path: Path,
    limits: ProcessingLimits | None = None,
) -> PipelineResult:
    """Run the full disk-based conversion pipeline.

    Important validation rules:
    - input ZIP size must not exceed ``max_zip_size_bytes``
    - top-level source folder count must not exceed ``max_source_folders``
    - each source folder is processed through ``process_source_folder`` and
      always yields one output folder (success or error report folder)

    Args:
        input_zip_path: ZIP with top-level source folders.
        excel_path: Excel mapping file.
        cnv_path: Fixed conversion table file.
        output_zip_path: Destination ZIP path to write pipeline output.
        limits: Optional processing limits.

    Returns:
        ``PipelineResult`` with per-folder results and output ZIP path.

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If global pipeline validations fail.
        RuntimeError: If output folder count does not match source folder count.
    """

    limits = limits or ProcessingLimits()

    if not input_zip_path.is_file():
        raise FileNotFoundError(f"Input zip niet gevonden: {input_zip_path}")
    if not excel_path.is_file():
        raise FileNotFoundError(f"Excel-bestand niet gevonden: {excel_path}")
    if not cnv_path.is_file():
        raise FileNotFoundError(f"CNV-bestand niet gevonden: {cnv_path}")

    zip_size = input_zip_path.stat().st_size
    if zip_size > limits.max_zip_size_bytes:
        raise ValueError(
            f"Input zip overschrijdt maximum grootte: {zip_size} > {limits.max_zip_size_bytes} bytes."
        )

    records = parse_excel_mapping_file(excel_path)
    excel_index = build_excel_index(records)
    conversion_table = parse_cnv_table_bytes(cnv_path.read_bytes())

    with tempfile.TemporaryDirectory(prefix="braille_pipeline_") as temp_dir:
        temp_root = Path(temp_dir)
        input_root = temp_root / "input"
        staging_root = temp_root / "staging"
        final_output_root = temp_root / "output"

        input_root.mkdir(parents=True, exist_ok=True)
        staging_root.mkdir(parents=True, exist_ok=True)
        final_output_root.mkdir(parents=True, exist_ok=True)

        _safe_extract_zip(input_zip_path, input_root)
        source_folders = _discover_top_level_source_folders(input_root)

        if not source_folders:
            raise ValueError("Input zip bevat geen top-level bronfolders.")
        if len(source_folders) > limits.max_source_folders:
            raise ValueError(
                f"Aantal bronfolders overschrijdt limiet: {len(source_folders)} > {limits.max_source_folders}."
            )

        results = []
        used_output_names: set[str] = set()

        for source_folder in source_folders:
            per_source_stage = staging_root / source_folder.name
            per_source_stage.mkdir(parents=True, exist_ok=True)

            result = process_source_folder(
                source_folder=source_folder,
                output_root=per_source_stage,
                excel_index=excel_index,
                conversion_table=conversion_table,
                limits=limits,
            )

            staged_output_folder = per_source_stage / result.output_folder
            if not staged_output_folder.exists():
                staged_output_folder.mkdir(parents=True, exist_ok=True)
                (staged_output_folder / "error_report.txt").write_text(
                    "Outputfolder ontbrak na verwerking; automatische foutfolder aangemaakt.\n",
                    encoding="utf-8",
                )
                if result.status == "success":
                    result.status = "error"
                    result.errors.append("Outputfolder ontbrak na verwerking.")

            final_name = _ensure_unique_folder_name(result.output_folder, used_output_names)
            final_destination = final_output_root / final_name
            shutil.move(str(staged_output_folder), str(final_destination))
            result.output_folder = final_name
            results.append(result)

        if len(results) != len(source_folders):
            raise RuntimeError("Aantal outputfolders komt niet overeen met aantal bronfolders.")

        _zip_output_root(final_output_root, output_zip_path)

    return PipelineResult(
        output_zip_path=output_zip_path,
        folder_results=results,
        total_source_folders=len(results),
    )
