import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from folder_processor import process_source_folder


class FolderProcessorTests(unittest.TestCase):
    def _make_source(self, root: Path, *, xml_lois: str = "t378393", file_lois: str = "378393") -> Path:
        source = root / "65856"
        source.mkdir()
        (source / f"meta{file_lois}.xml").write_text(
            f"<document><lois_id>{xml_lois}</lois_id><title>De Zoete Zusjes gaan op avontuur</title></document>",
            encoding="utf-8",
        )
        (source / f"p{file_lois}_001.brl").write_bytes(bytes([1, 2]))
        return source

    def test_processes_folder_with_xml_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root)
            output = root / "out"
            output.mkdir()
            original_xml = (source / "meta378393.xml").read_bytes()

            result = process_source_folder(source, output, {1: 65, 2: 66})

            self.assertEqual(result.status, "success")
            self.assertEqual(result.book_number, "65856")
            self.assertEqual(result.lois_id, "378393")
            self.assertEqual(result.title, "De Zoete Zusjes gaan op avontuur")
            folder = output / "65856_De_Zoete_Zusjes_gaan_op_avontuur"
            self.assertEqual(
                (folder / "65856_meta_De_Zoete_Zusjes_gaan_op_avontuur.xml").read_bytes(),
                original_xml,
            )
            self.assertEqual(
                (folder / "65856_001_De_Zoete_Zusjes_gaan_op_avontuur.brf").read_bytes(),
                b"AB",
            )

    def test_reports_xml_metadata_and_filename_lois_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self._make_source(root, xml_lois="t999999")
            output = root / "out"
            output.mkdir()

            result = process_source_folder(source, output, {1: 65, 2: 66})

            self.assertEqual(result.status, "error")
            self.assertTrue(any("XML-metadata komt niet overeen" in error for error in result.errors))
            self.assertTrue((output / "65856_error" / "error_report.txt").exists())

    def test_reports_missing_title_field(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "65856"
            source.mkdir()
            (source / "meta378393.xml").write_text(
                "<document><lois_id>t378393</lois_id></document>", encoding="utf-8"
            )
            (source / "p378393_001.brl").write_bytes(b"x")
            output = root / "out"
            output.mkdir()

            result = process_source_folder(source, output, {})

            self.assertEqual(result.status, "error")
            self.assertTrue(any("geen expliciet <title>-veld" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
