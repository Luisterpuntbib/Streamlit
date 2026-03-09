"""Byte-based BRL to BRF conversion utilities.

The conversion table is treated as ``dict[int, int]``. Conversion is performed
on bytes, not on text strings.
"""

from __future__ import annotations

import re
from pathlib import Path


def _parse_byte_token(token: str) -> int:
    token = token.strip()
    if not token:
        raise ValueError("Lege token in .cnv regel.")

    if token.lower().startswith("0x"):
        value = int(token, 16)
    elif token.isdigit():
        # In .cnv files without 0x-prefix, values are decimal (0..255).
        value = int(token, 10)
    elif re.fullmatch(r"[0-9A-Fa-f]{1,2}", token):
        # Backward-compatible fallback for explicit hex-like tokens.
        value = int(token, 16)
    else:
        raise ValueError(f"Ongeldige byte token: {token}")

    if not 0 <= value <= 255:
        raise ValueError(f"Byte buiten bereik 0..255: {token}")
    return value


def parse_cnv_table_bytes(cnv_bytes: bytes) -> dict[int, int]:
    """Parse a `.cnv` file to a byte mapping.

    Accepted formats include decimal and hex byte tokens per rule line.
    Comment/empty lines are ignored.

    Args:
        cnv_bytes: Raw bytes of the conversion table file.

    Returns:
        Mapping from source byte to target byte.

    Raises:
        ValueError: If no valid mapping exists or if any rule is invalid.
    """

    text = cnv_bytes.decode("utf-8", errors="ignore")
    mapping: dict[int, int] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        line = line.replace("->", " ").replace("=", " ").replace(",", " ").replace(";", " ")
        tokens = [part for part in line.split() if part]
        if len(tokens) < 2:
            continue

        try:
            source = _parse_byte_token(tokens[0])
            target = _parse_byte_token(tokens[1])
        except ValueError as exc:
            raise ValueError(f"Ongeldige .cnv regel {line_no}: {exc}") from exc

        # Mapping direction is source -> target.
        mapping[source] = target

    if not mapping:
        raise ValueError(".cnv bestand bevat geen geldige mappingregels.")

    return mapping


def extract_volume_suffix(brl_filename: str) -> str:
    """Extract the required 3-digit volume suffix from a BRL filename.

    Expected pattern: ``*_NNN.brl``.

    Args:
        brl_filename: Filename (not full path) to validate.

    Returns:
        The volume string ``NNN``.

    Raises:
        ValueError: If the filename does not match the required pattern.
    """

    match = re.search(r"_(\d{3})\.brl$", brl_filename, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Bestandsnaam heeft geen geldig volume suffix _NNN.brl: {brl_filename}")
    return match.group(1)


def convert_brl_bytes(brl_content: bytes, conversion_table: dict[int, int]) -> bytes:
    """Convert BRL bytes to BRF bytes using a byte mapping.

    Unmapped bytes are passed through unchanged.
    """

    return bytes(conversion_table.get(byte, byte) for byte in brl_content)


def convert_brl_file_to_brf_file(brl_path: Path, brf_path: Path, conversion_table: dict[int, int]) -> int:
    """Convert one BRL file to BRF on disk.

    Processing is chunked to avoid loading full files into memory.

    Args:
        brl_path: Input BRL file path.
        brf_path: Output BRF file path.
        conversion_table: Byte mapping ``dict[int, int]``.

    Returns:
        Number of source bytes processed.
    """

    chunk_size = 64 * 1024
    converted_count = 0

    with brl_path.open("rb") as src, brf_path.open("wb") as dst:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            converted = convert_brl_bytes(chunk, conversion_table)
            dst.write(converted)
            converted_count += len(chunk)

    return converted_count
