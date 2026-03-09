import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from brl_conversion import (
    convert_brl_bytes,
    convert_brl_file_to_brf_file,
    extract_volume_suffix,
    parse_cnv_table_bytes,
)


class BrlConversionTests(unittest.TestCase):
    def test_parse_cnv_table_bytes_decimal_source_to_target(self) -> None:
        data = b"37;35\n93;62\n65;97\n66;98\n"
        mapping = parse_cnv_table_bytes(data)
        self.assertEqual(mapping[37], 35)
        self.assertEqual(mapping[93], 62)
        self.assertEqual(mapping[65], 97)
        self.assertEqual(mapping[66], 98)

    def test_parse_cnv_table_bytes_hex_prefixed_supported(self) -> None:
        data = b"0x20 0x41\n0x21 0x42\n"
        mapping = parse_cnv_table_bytes(data)
        self.assertEqual(mapping[0x20], 0x41)
        self.assertEqual(mapping[0x21], 0x42)

    def test_convert_brl_bytes_applies_source_to_target_mapping(self) -> None:
        mapping = {37: 35, 93: 62, 65: 97, 66: 98}
        source = bytes([37, 93, 65, 66, 90])
        target = convert_brl_bytes(source, mapping)
        self.assertEqual(target, bytes([35, 62, 97, 98, 90]))

    def test_convert_brl_bytes_with_default_passthrough(self) -> None:
        mapping = {1: 65, 2: 66}
        self.assertEqual(convert_brl_bytes(bytes([1, 2, 3]), mapping), bytes([65, 66, 3]))

    def test_extract_volume_suffix(self) -> None:
        self.assertEqual(extract_volume_suffix("p380532_002.brl"), "002")

    def test_extract_volume_suffix_invalid(self) -> None:
        with self.assertRaises(ValueError):
            extract_volume_suffix("p380532_2.brl")

    def test_convert_brl_file_to_brf_file(self) -> None:
        mapping = {37: 35, 93: 62, 65: 97, 66: 98}
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.brl"
            dst = Path(tmp) / "out.brf"
            src.write_bytes(bytes([37, 93, 65, 66, 90]))

            converted_count = convert_brl_file_to_brf_file(src, dst, mapping)
            self.assertEqual(converted_count, 5)
            self.assertEqual(dst.read_bytes(), bytes([35, 62, 97, 98, 90]))


if __name__ == "__main__":
    unittest.main()
