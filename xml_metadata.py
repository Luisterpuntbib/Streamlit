"""Read explicit Braille book metadata from a source XML file."""

from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

from braille_models import BookRecord
from excel_mapping import normalize_lois_id
from naming_rules import make_title_slug


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def parse_xml_book_record(xml_path: Path, book_number: str) -> BookRecord:
    """Build a book record from explicit ``lois_id`` and ``title`` XML fields.

    Args:
        xml_path: Source XML containing one explicit Lois ID and title.
        book_number: Belgian book number derived from the source folder name.

    Returns:
        Validated metadata used for output naming and consistency checks.

    Raises:
        ValueError: If XML is invalid or required metadata is missing/ambiguous.
    """

    try:
        root = ET.parse(xml_path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError(f"XML-bestand '{xml_path.name}' kan niet worden gelezen: {exc}") from exc

    values: dict[str, list[str]] = {"lois_id": [], "title": []}
    for element in root.iter():
        name = _local_name(element.tag)
        text = (element.text or "").strip()
        if name in values and text:
            values[name].append(text)

    for field_name, field_values in values.items():
        if not field_values:
            raise ValueError(f"XML-bestand '{xml_path.name}' bevat geen expliciet <{field_name}>-veld.")
        if len(set(field_values)) > 1:
            raise ValueError(
                f"XML-bestand '{xml_path.name}' bevat meerdere verschillende <{field_name}>-waarden."
            )

    raw_lois_id = values["lois_id"][0]
    if re.fullmatch(r"(?i)t?\d+", raw_lois_id) is None:
        raise ValueError(f"XML-bestand '{xml_path.name}' bevat een ongeldige Lois ID.")

    lois_id = normalize_lois_id(raw_lois_id)
    title = values["title"][0]
    title_slug = make_title_slug(title)
    if not lois_id:
        raise ValueError(f"XML-bestand '{xml_path.name}' bevat een ongeldige Lois ID.")
    if not title_slug:
        raise ValueError(f"XML-bestand '{xml_path.name}' bevat een lege titel.")

    return BookRecord(
        excel_row=0,
        title=title,
        title_slug=title_slug,
        book_number=book_number,
        lois_id=lois_id,
    )
