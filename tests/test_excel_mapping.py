import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from excel_mapping import build_excel_index, normalize_lois_id, parse_excel_mapping_file


class ExcelMappingTests(unittest.TestCase):
    def test_normalize_lois_id(self) -> None:
        self.assertEqual(normalize_lois_id("t374170"), "374170")
        self.assertEqual(normalize_lois_id("T374170"), "374170")
        self.assertEqual(normalize_lois_id("374170"), "374170")
        self.assertEqual(normalize_lois_id("  t374170  "), "374170")

    @patch("excel_mapping.pd.read_excel")
    def test_parse_excel_mapping_file_skips_first_row(self, mock_read_excel) -> None:
        mock_read_excel.return_value = pd.DataFrame(
            [
                ["Titelrij", "Geen data", "Geen Lois ID", None, "Geen boeknummer"],
                [None, "Aan mij heb je niks", "t374170", None, "63773"],
                [None, "Tweede boek", "T380532", None, "12345"],
            ]
        )

        records = parse_excel_mapping_file(Path("dummy.xlsx"))

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].lois_id, "374170")
        self.assertEqual(records[1].lois_id, "380532")
        self.assertEqual(records[0].title, "Aan mij heb je niks")
        self.assertEqual(records[0].title_slug, "Aan_mij_heb_je_niks")
        self.assertEqual(records[0].book_number, "63773")

    @patch("excel_mapping.pd.read_excel")
    def test_parse_excel_mapping_file_empty_title_raises(self, mock_read_excel) -> None:
        mock_read_excel.return_value = pd.DataFrame(
            [
                ["Titelrij", "Geen data", "Geen Lois ID", None, "Geen boeknummer"],
                [None, "", "t374170", None, "63773"],
            ]
        )

        with self.assertRaises(ValueError):
            parse_excel_mapping_file(Path("dummy.xlsx"))

    @patch("excel_mapping.pd.read_excel")
    def test_parse_excel_mapping_file_empty_lois_id_raises(self, mock_read_excel) -> None:
        mock_read_excel.return_value = pd.DataFrame(
            [
                ["Titelrij", "Geen data", "Geen Lois ID", None, "Geen boeknummer"],
                [None, "Titel", "", None, "63773"],
            ]
        )

        with self.assertRaises(ValueError):
            parse_excel_mapping_file(Path("dummy.xlsx"))

    @patch("excel_mapping.pd.read_excel")
    def test_parse_excel_mapping_file_duplicate_lois_id_after_normalization_raises(self, mock_read_excel) -> None:
        mock_read_excel.return_value = pd.DataFrame(
            [
                ["Titelrij", "Geen data", "Geen Lois ID", None, "Geen boeknummer"],
                [None, "Titel 1", "t374170", None, "63773"],
                [None, "Titel 2", "374170", None, "12345"],
            ]
        )

        with self.assertRaises(ValueError):
            parse_excel_mapping_file(Path("dummy.xlsx"))

    @patch("excel_mapping.pd.read_excel")
    def test_build_excel_index(self, mock_read_excel) -> None:
        mock_read_excel.return_value = pd.DataFrame(
            [
                ["Titelrij", "Geen data", "Geen Lois ID", None, "Geen boeknummer"],
                [None, "Aan mij heb je niks", "t374170", None, "63773"],
            ]
        )

        records = parse_excel_mapping_file(Path("dummy.xlsx"))
        index = build_excel_index(records)
        self.assertIn("63773", index.by_book_number)
        self.assertIn("374170", index.by_lois_id)
        self.assertEqual(index.by_lois_id["374170"].title_slug, "Aan_mij_heb_je_niks")


if __name__ == "__main__":
    unittest.main()
