import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from braille_models import BookRecord
from excel_mapping import ExcelIndex
from folder_processor import process_source_folder


class FolderProcessorTests(unittest.TestCase):
    def _build_excel_index_for_correct_match(self) -> ExcelIndex:
        record = BookRecord(
            excel_row=2,
            title="Aan mij heb je niks",
            title_slug="Aan_mij_heb_je_niks",
            book_number="63773",
            lois_id="374170",
        )
        return ExcelIndex(by_book_number={record.book_number: record}, by_lois_id={record.lois_id: record})

    def _build_excel_index_typo_case(self) -> ExcelIndex:
        record = BookRecord(
            excel_row=2,
            title="Typo boek",
            title_slug="Typo_boek",
            book_number="70001",
            lois_id="378851",
        )
        return ExcelIndex(by_book_number={record.book_number: record}, by_lois_id={record.lois_id: record})

    def test_process_source_folder_correct_match(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "374170_1_1"
            output = root / "out"
            source.mkdir()
            output.mkdir()

            xml_content = "<boek><meta>ongewijzigd</meta></boek>"
            (source / "meta374170.xml").write_text(xml_content, encoding="utf-8")
            (source / "p374170_001.brl").write_bytes(bytes([1, 2]))

            result = process_source_folder(
                source_folder=source,
                output_root=output,
                excel_index=self._build_excel_index_for_correct_match(),
                conversion_table={1: 65, 2: 66},
            )

            self.assertEqual(result.status, "success")
            folder = output / result.output_folder
            self.assertTrue((folder / "63773_001_Aan_mij_heb_je_niks.brf").exists())
            self.assertEqual((folder / "63773_meta_Aan_mij_heb_je_niks.xml").read_text(encoding="utf-8"), xml_content)

    def test_process_source_folder_with_book_number_in_folder_name(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "63773_voorrang"
            output = root / "out"
            source.mkdir()
            output.mkdir()

            xml_content = "<boek><meta>ongewijzigd</meta></boek>"
            (source / "meta374170.xml").write_text(xml_content, encoding="utf-8")
            (source / "p374170_001.brl").write_bytes(bytes([1, 2]))

            result = process_source_folder(
                source_folder=source,
                output_root=output,
                excel_index=self._build_excel_index_for_correct_match(),
                conversion_table={1: 65, 2: 66},
            )

            self.assertEqual(result.status, "success")
            self.assertEqual(result.book_number, "63773")
            self.assertEqual(result.lois_id, "374170")
            folder = output / result.output_folder
            self.assertTrue((folder / "63773_001_Aan_mij_heb_je_niks.brf").exists())
            self.assertEqual((folder / "63773_meta_Aan_mij_heb_je_niks.xml").read_text(encoding="utf-8"), xml_content)

    def test_reports_excel_column_c_mismatch_for_book_number_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "70001_voorrang"
            output = root / "out"
            source.mkdir()
            output.mkdir()

            (source / "meta378531.xml").write_text("<boek/>", encoding="utf-8")
            (source / "p378531_001.brl").write_bytes(b"x")

            result = process_source_folder(
                source_folder=source,
                output_root=output,
                excel_index=self._build_excel_index_typo_case(),
                conversion_table={1: 65},
            )

            self.assertEqual(result.status, "error")
            self.assertEqual(result.book_number, "70001")
            self.assertTrue(any("Lois ID in XML/BRL komt niet overeen" in err for err in result.errors))
            self.assertTrue(any("Gevonden Lois ID in XML/BRL: 378531" in err for err in result.errors))
            self.assertTrue(any("Excel rij 2, kolom C: 378851" in err for err in result.errors))

    def test_process_source_folder_excel_typo_suggestion(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "378531_1_1"
            output = root / "out"
            source.mkdir()
            output.mkdir()

            (source / "meta378531.xml").write_text("<boek/>", encoding="utf-8")
            (source / "p378531_001.brl").write_bytes(b"x")

            result = process_source_folder(
                source_folder=source,
                output_root=output,
                excel_index=self._build_excel_index_typo_case(),
                conversion_table={1: 65},
            )

            self.assertEqual(result.status, "error")
            self.assertTrue(any("Geen Excel-match op Lois ID" in err for err in result.errors))
            self.assertTrue(any("Lois ID in Excel lijkt fout (mogelijke typefout)." in err for err in result.errors))
            self.assertTrue(any("Gevonden Lois ID uit input: 378531" in err for err in result.errors))
            self.assertTrue(any("Dichtstbijzijnde Lois ID in Excel: 378851" in err for err in result.errors))

            report = output / result.output_folder / "error_report.txt"
            self.assertTrue(report.exists())
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Lois ID in Excel lijkt fout (mogelijke typefout).", report_text)

    def test_process_source_folder_no_excel_match_for_999999(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "999999_1_1"
            output = root / "out"
            source.mkdir()
            output.mkdir()

            (source / "meta999999.xml").write_text("<boek/>", encoding="utf-8")
            (source / "p999999_001.brl").write_bytes(b"x")

            result = process_source_folder(
                source_folder=source,
                output_root=output,
                excel_index=self._build_excel_index_for_correct_match(),
                conversion_table={1: 65},
            )

            self.assertEqual(result.status, "error")
            self.assertTrue(any("Geen Excel-match op Lois ID" in err for err in result.errors))
            self.assertTrue(any("Gevonden Lois ID uit input: 999999" in err for err in result.errors))
            report = output / result.output_folder / "error_report.txt"
            self.assertTrue(report.exists())


if __name__ == "__main__":
    unittest.main()
