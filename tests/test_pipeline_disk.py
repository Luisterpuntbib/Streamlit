import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from braille_models import ProcessingLimits
from pipeline_disk import run_pipeline_disk


class PipelineDiskTests(unittest.TestCase):
    def _write_cnv(self, path: Path) -> None:
        path.write_bytes(b"01 41\n02 42\n")

    def _write_excel(self, path: Path) -> None:
        import pandas as pd

        rows = [
            ["kop", "titel", "lois", "x", "boeknr"],
            [None, "Aan mij heb je niks", "t374170", None, "63773"],
            [None, "Tweede titel", "t380532", None, "70000"],
        ]
        pd.DataFrame(rows).to_excel(path, index=False, header=False)

    def _make_input_zip_success(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("374170_1_1/meta374170.xml", "<root/>")
            archive.writestr("374170_1_1/p374170_001.brl", bytes([1, 2]))
            archive.writestr("380532_1_1/meta380532.xml", "<root/>")
            archive.writestr("380532_1_1/p380532_001.brl", bytes([2, 1]))

    def _make_input_zip_with_book_number_folders(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("63773_voorrang/meta374170.xml", "<root/>")
            archive.writestr("63773_voorrang/p374170_001.brl", bytes([1, 2]))
            archive.writestr("70000_voorrang/meta380532.xml", "<root/>")
            archive.writestr("70000_voorrang/p380532_001.brl", bytes([2, 1]))

    def _make_input_zip_with_error_folder(self, path: Path) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("374170_1_1/meta374170.xml", "<root/>")
            archive.writestr("374170_1_1/p374170_001.brl", bytes([1, 2]))
            archive.writestr("999999_1_1/meta999999.xml", "<root/>")
            archive.writestr("999999_1_1/p999999_001.brl", bytes([2, 1]))

    def test_run_pipeline_disk_success_two_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            excel_file = root / "map.xlsx"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"

            self._make_input_zip_success(input_zip)
            self._write_excel(excel_file)
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, excel_file, cnv_file, output_zip)

            self.assertTrue(output_zip.exists())
            self.assertEqual(result.total_source_folders, 2)
            self.assertEqual(len(result.folder_results), 2)
            self.assertTrue(all(item.status == "success" for item in result.folder_results))

            with zipfile.ZipFile(output_zip, "r") as archive:
                names = set(archive.namelist())

            self.assertIn("63773_Aan_mij_heb_je_niks/63773_001_Aan_mij_heb_je_niks.brf", names)
            self.assertIn("70000_Tweede_titel/70000_001_Tweede_titel.brf", names)
            self.assertIn("63773_Aan_mij_heb_je_niks/63773_meta_Aan_mij_heb_je_niks.xml", names)
            self.assertIn("70000_Tweede_titel/70000_meta_Tweede_titel.xml", names)

    def test_run_pipeline_disk_keeps_output_count_when_one_folder_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            excel_file = root / "map.xlsx"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"

            self._make_input_zip_with_error_folder(input_zip)
            self._write_excel(excel_file)
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, excel_file, cnv_file, output_zip)

            self.assertEqual(result.total_source_folders, 2)
            self.assertEqual(len(result.folder_results), 2)

            success_count = sum(1 for item in result.folder_results if item.status == "success")
            error_count = sum(1 for item in result.folder_results if item.status == "error")
            self.assertEqual(success_count, 1)
            self.assertEqual(error_count, 1)

            with zipfile.ZipFile(output_zip, "r") as archive:
                names = set(archive.namelist())
                output_folders = {name.split("/")[0] for name in names if "/" in name}

            self.assertEqual(len(output_folders), 2)
            self.assertTrue(any(name.endswith("error_report.txt") for name in names))

    def test_run_pipeline_disk_accepts_book_number_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            excel_file = root / "map.xlsx"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"

            self._make_input_zip_with_book_number_folders(input_zip)
            self._write_excel(excel_file)
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, excel_file, cnv_file, output_zip)

            self.assertEqual(result.total_source_folders, 2)
            self.assertTrue(all(item.status == "success" for item in result.folder_results))
            self.assertEqual({item.book_number for item in result.folder_results}, {"63773", "70000"})

            with zipfile.ZipFile(output_zip, "r") as archive:
                names = set(archive.namelist())

            self.assertIn("63773_Aan_mij_heb_je_niks/63773_001_Aan_mij_heb_je_niks.brf", names)
            self.assertIn("70000_Tweede_titel/70000_001_Tweede_titel.brf", names)

    def test_run_pipeline_disk_applies_source_folder_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            excel_file = root / "map.xlsx"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"

            self._make_input_zip_success(input_zip)
            self._write_excel(excel_file)
            self._write_cnv(cnv_file)

            with self.assertRaises(ValueError):
                run_pipeline_disk(
                    input_zip,
                    excel_file,
                    cnv_file,
                    output_zip,
                    limits=ProcessingLimits(max_source_folders=1),
                )


if __name__ == "__main__":
    unittest.main()
