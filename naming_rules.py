"""Naming helpers for output folders and files.

This module centralizes slug and filename construction rules used by the
Braille conversion pipeline.
"""

from __future__ import annotations

import re

INVALID_FILENAME_CHARS = r'<>:"/\\|?*'


def make_title_slug(title: str) -> str:
    """Convert a title to the configured slug format.

    Rules:
    - trim leading/trailing whitespace
    - collapse internal whitespace to single spaces
    - replace spaces with underscores

    Args:
        title: Raw title text from Excel.

    Returns:
        Slug value used in output folder/file names.
    """

    trimmed = (title or "").strip()
    collapsed = re.sub(r"\s+", " ", trimmed)
    return collapsed.replace(" ", "_")


def sanitize_path_name(name: str) -> str:
    """Sanitize a folder or filename fragment for filesystem safety.

    Args:
        name: Raw candidate name.

    Returns:
        Name with forbidden characters replaced and whitespace normalized.
        Falls back to ``"onbekend"`` when the result is empty.
    """

    cleaned = "".join("_" if ch in INVALID_FILENAME_CHARS else ch for ch in name)
    cleaned = cleaned.strip().strip(".")
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned or "onbekend"


def make_output_folder_name(book_number: str, title_slug: str) -> str:
    """Build the output folder name: ``{book_number}_{title_slug}``."""

    return sanitize_path_name(f"{book_number}_{title_slug}")


def make_output_xml_name(book_number: str, title_slug: str) -> str:
    """Build the renamed XML filename: ``{book_number}_meta_{title_slug}.xml``."""

    return sanitize_path_name(f"{book_number}_meta_{title_slug}.xml")


def make_output_brf_name(book_number: str, volume: str, title_slug: str) -> str:
    """Build the BRF filename: ``{book_number}_{volume}_{title_slug}.brf``."""

    return sanitize_path_name(f"{book_number}_{volume}_{title_slug}.brf")
