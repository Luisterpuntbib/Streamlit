"""Helpers for reading Formie CSV exports and building Bpost contact names."""

from __future__ import annotations

import io
from typing import BinaryIO

import pandas as pd


NAME_COLUMN_PAIRS = (
    ("Naam: Voornaam", "Naam: Familienaam"),
    ("Naam: First Name", "Naam: Last Name"),
)


def read_formie_csv(source: BinaryIO) -> pd.DataFrame:
    """Read a Formie CSV using its detected encoding and delimiter.

    UTF-8 (with or without BOM) and Windows-1252 are supported. The delimiter
    is selected from comma and semicolon based on the header row.
    """

    source.seek(0)
    raw_data = source.read()

    try:
        text = raw_data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw_data.decode("cp1252")

    header = text.splitlines()[0] if text else ""
    delimiter = ";" if header.count(";") > header.count(",") else ","
    return pd.read_csv(io.StringIO(text), sep=delimiter)


def build_contact_names(input_data: pd.DataFrame) -> pd.Series:
    """Return trimmed contact names from Dutch or English Formie columns.

    Dutch headers are preferred when both variants exist. Missing first or
    last names are accepted; if no supported pair exists, empty values are
    returned for every input row.
    """

    for first_name_column, last_name_column in NAME_COLUMN_PAIRS:
        if {first_name_column, last_name_column}.issubset(input_data.columns):
            first_names = input_data[first_name_column].fillna("").astype(str).str.strip()
            last_names = input_data[last_name_column].fillna("").astype(str).str.strip()
            return (first_names + " " + last_names).str.strip()

    return pd.Series("", index=input_data.index, dtype="object")
