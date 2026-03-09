from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ProcessingLimits:
    max_zip_size_bytes: int = 500 * 1024 * 1024
    max_source_folders: int = 100
    max_brl_per_folder: int = 200


@dataclass(frozen=True)
class BookRecord:
    excel_row: int
    title: str
    title_slug: str
    book_number: str
    lois_id: str


@dataclass
class FolderResult:
    source_folder: str
    output_folder: str
    status: str
    converted_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    output_zip_path: Path
    folder_results: list[FolderResult]
    total_source_folders: int
