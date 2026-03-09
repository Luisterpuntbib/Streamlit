"""Deep diagnostic comparer for two BRF files.

Usage:
  python scripts/debug_compare_brf.py \
    --expected-file C:\\path\\to\\expected.brf \
    --actual-file C:\\path\\to\\actual.brf
"""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for BRF deep comparison."""

    parser = argparse.ArgumentParser(description="Deep-compare two .brf files")
    parser.add_argument("--expected-file", required=True, type=Path, help="Reference BRF file")
    parser.add_argument("--actual-file", required=True, type=Path, help="BRF file to compare")
    return parser.parse_args()


def _format_hex_window(data: bytes, start: int, width: int = 16) -> str:
    """Render a compact hex + ASCII line for manual inspection."""

    chunk = data[start : start + width]
    hex_part = " ".join(f"{byte:02X}" for byte in chunk)
    ascii_part = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in chunk)
    return f"{start:08X}  {hex_part:<{width * 3 - 1}}  |{ascii_part}|"


def _collect_diff_offsets(expected: bytes, actual: bytes) -> list[int]:
    """Return all byte offsets where the two byte arrays differ."""

    min_len = min(len(expected), len(actual))
    offsets = [i for i in range(min_len) if expected[i] != actual[i]]
    if len(expected) != len(actual):
        offsets.extend(range(min_len, max(len(expected), len(actual))))
    return offsets


def _line_ending_stats(data: bytes) -> tuple[int, int, int]:
    """Return counts of CRLF, LF-only, and CR-only line endings."""

    crlf = data.count(b"\r\n")
    lf_only = data.count(b"\n") - crlf
    cr_only = data.count(b"\r") - crlf
    return crlf, max(lf_only, 0), max(cr_only, 0)


def _detect_newline_pattern(expected: bytes, actual: bytes) -> str | None:
    """Detect likely systematic CRLF/LF newline normalization differences."""

    expected_lf = expected.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    actual_lf = actual.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    if expected_lf == actual_lf and expected != actual:
        return "Inhoud lijkt gelijk na newline-normalisatie (mogelijk CRLF vs LF verschil)."
    return None


def main() -> int:
    """Run deep comparison and print a readable diagnostic report."""

    args = parse_args()

    if not args.expected_file.is_file():
        print(f"ERROR: expected file niet gevonden: {args.expected_file}")
        return 2
    if not args.actual_file.is_file():
        print(f"ERROR: actual file niet gevonden: {args.actual_file}")
        return 2

    expected = args.expected_file.read_bytes()
    actual = args.actual_file.read_bytes()

    expected_size = len(expected)
    actual_size = len(actual)
    size_equal = expected_size == actual_size

    diff_offsets = _collect_diff_offsets(expected, actual)
    first_diff = diff_offsets[0] if diff_offsets else None

    print("=== BRF Diepvergelijking ===")
    print(f"Expected: {args.expected_file}")
    print(f"Actual:   {args.actual_file}")

    print("\n=== Grootte ===")
    print(f"Expected grootte: {expected_size} bytes")
    print(f"Actual grootte:   {actual_size} bytes")
    print(f"Grootte gelijk:   {'ja' if size_equal else 'nee'}")

    print("\n=== Byteverschillen ===")
    if first_diff is None:
        print("Geen byteverschillen: bestanden zijn identiek.")
    else:
        print(f"Eerste verschil op offset: {first_diff} (0x{first_diff:X})")
        print(f"Aantal verschillende bytes: {len(diff_offsets)}")

    print("\n=== Hex-dump rond eerste 10 verschillen ===")
    if not diff_offsets:
        print("- geen")
    else:
        for idx, offset in enumerate(diff_offsets[:10], start=1):
            start = max(0, offset - 8)
            print(f"\nVerschil #{idx} op offset {offset} (0x{offset:X})")
            print("Expected:")
            print(_format_hex_window(expected, start))
            print("Actual:")
            print(_format_hex_window(actual, start))

    print("\n=== Newline-analyse ===")
    e_crlf, e_lf, e_cr = _line_ending_stats(expected)
    a_crlf, a_lf, a_cr = _line_ending_stats(actual)
    print(f"Expected CRLF/LF/CR: {e_crlf}/{e_lf}/{e_cr}")
    print(f"Actual   CRLF/LF/CR: {a_crlf}/{a_lf}/{a_cr}")

    newline_hint = _detect_newline_pattern(expected, actual)
    if newline_hint:
        print(f"Hint: {newline_hint}")

    print("\n=== Samenvatting ===")
    if not diff_offsets:
        print("VOLLEDIG IDENTIEK")
        return 0

    print("NIET IDENTIEK")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
