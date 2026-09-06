import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from braille_models import ProcessingLimits
from pipeline_disk import run_pipeline_disk


class PipelineDiskTests(unittest.TestCase):
    def _write_cnv(self, path: Path) -> None:
        path.write_bytes(b"01 41\n02 42\n")

    def _add_book(
        self,
        archive: zipfile.ZipFile,
        book_number: str,
        lois_id: str,
        title: str,
        *,
        include_title: bool = True,
    ) -> None:
        title_xml = f"<title>{title}</title>" if include_title else ""
        archive.writestr(
            f"{book_number}/meta{lois_id}.xml",
            f"<document><lois_id>t{lois_id}</lois_id>{title_xml}</document>",
        )
        archive.writestr(f"{book_number}/p{lois_id}_001.brl", bytes([1, 2]))

    def test_run_pipeline_disk_success_one_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                self._add_book(archive, "65856", "378393", "De Zoete Zusjes gaan op avontuur")
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, cnv_file, output_zip)

            self.assertEqual(result.total_source_folders, 1)
            self.assertEqual(result.folder_results[0].status, "success")
            with zipfile.ZipFile(output_zip) as archive:
                names = set(archive.namelist())
            self.assertIn(
                "65856_De_Zoete_Zusjes_gaan_op_avontuur/65856_001_De_Zoete_Zusjes_gaan_op_avontuur.brf",
                names,
            )

    def test_run_pipeline_disk_success_multiple_folders(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                self._add_book(archive, "65856", "378393", "Eerste titel")
                self._add_book(archive, "66000", "379230", "Project 2024")
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, cnv_file, output_zip)

            self.assertEqual(result.total_source_folders, 2)
            self.assertTrue(all(item.status == "success" for item in result.folder_results))
            self.assertEqual({item.book_number for item in result.folder_results}, {"65856", "66000"})
            with zipfile.ZipFile(output_zip) as archive:
                output_folders = {name.split("/")[0] for name in archive.namelist() if "/" in name}
            self.assertEqual(len(output_folders), 2)

    def test_error_folder_is_kept_for_missing_xml_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                self._add_book(archive, "65856", "378393", "", include_title=False)
            self._write_cnv(cnv_file)

            result = run_pipeline_disk(input_zip, cnv_file, output_zip)

            self.assertEqual(result.folder_results[0].status, "error")
            with zipfile.ZipFile(output_zip) as archive:
                names = set(archive.namelist())
            self.assertIn("65856_error/error_report.txt", names)

    def test_run_pipeline_disk_applies_source_folder_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input.zip"
            cnv_file = root / "table.cnv"
            output_zip = root / "output.zip"
            with zipfile.ZipFile(input_zip, "w") as archive:
                self._add_book(archive, "65856", "378393", "Eerste titel")
                self._add_book(archive, "66000", "379230", "Tweede titel")
            self._write_cnv(cnv_file)

            with self.assertRaises(ValueError):
                run_pipeline_disk(
                    input_zip,
                    cnv_file,
                    output_zip,
                    limits=ProcessingLimits(max_source_folders=1),
                )


if __name__ == "__main__":
    unittest.main()
