import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from braille_models import ProcessingLimits
from validators import determine_lois_id_and_consistency, validate_source_folder


class ValidatorsTests(unittest.TestCase):
    def test_valid_source_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta374170.xml").write_text("<root><lois>t374170</lois></root>", encoding="utf-8")
            (folder / "p374170_001.brl").write_bytes(b"abc")

            errors = validate_source_folder(folder)
            self.assertEqual(errors, [])

    def test_requires_exactly_one_xml(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "one374170.xml").write_text("<root/>", encoding="utf-8")
            (folder / "two374170.xml").write_text("<root/>", encoding="utf-8")
            (folder / "p374170_001.brl").write_bytes(b"abc")

            errors = validate_source_folder(folder)
            self.assertTrue(any("exact 1 XML" in err for err in errors))

    def test_requires_at_least_one_brl(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta374170.xml").write_text("<root/>", encoding="utf-8")

            errors = validate_source_folder(folder)
            self.assertTrue(any("minstens 1 .brl" in err for err in errors))

    def test_rejects_invalid_brl_pattern(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta374170.xml").write_text("<root/>", encoding="utf-8")
            (folder / "book_1.brl").write_bytes(b"abc")

            errors = validate_source_folder(folder)
            self.assertTrue(any("_NNN.brl" in err for err in errors))

    def test_respects_brl_count_limit(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta374170.xml").write_text("<root/>", encoding="utf-8")
            (folder / "p374170_001.brl").write_bytes(b"a")
            (folder / "p374170_002.brl").write_bytes(b"b")

            errors = validate_source_folder(folder, limits=ProcessingLimits(max_brl_per_folder=1))
            self.assertTrue(any("overschrijdt maximum .brl-bestanden" in err for err in errors))

    def test_detects_inconsistent_lois_ids_between_sources(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta378531.xml").write_text("<root/>", encoding="utf-8")
            (folder / "p374170_001.brl").write_bytes(b"a")

            errors = validate_source_folder(folder)
            self.assertTrue(any("Inconsistente Lois ID tussen inputbronnen" in err for err in errors))

    def test_xml_content_is_ignored_for_lois_derivation(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "374170_1_1"
            folder.mkdir()
            (folder / "meta374170.xml").write_text("<root><lois_id>t378531</lois_id></root>", encoding="utf-8")
            (folder / "p374170_001.brl").write_bytes(b"a")

            lois_id, errors = determine_lois_id_and_consistency(folder)
            self.assertEqual(lois_id, "374170")
            self.assertEqual(errors, [])

    def test_xml_title_digits_herscht_are_not_treated_as_lois_id(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "379230_1_1"
            folder.mkdir()
            (folder / "meta379230.xml").write_text("<root><title>Herscht 07769</title></root>", encoding="utf-8")
            (folder / "p379230_001.brl").write_bytes(b"a")

            lois_id, errors = determine_lois_id_and_consistency(folder)
            self.assertEqual(lois_id, "379230")
            self.assertEqual(errors, [])

    def test_xml_title_digits_project_are_not_treated_as_lois_id(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "379230_1_1"
            folder.mkdir()
            (folder / "meta379230.xml").write_text("<root><title>Project 2024</title></root>", encoding="utf-8")
            (folder / "p379230_001.brl").write_bytes(b"a")

            lois_id, errors = determine_lois_id_and_consistency(folder)
            self.assertEqual(lois_id, "379230")
            self.assertEqual(errors, [])

    def test_xml_title_digits_volume_are_not_treated_as_lois_id(self) -> None:
        with TemporaryDirectory() as tmp:
            folder = Path(tmp) / "379230_1_1"
            folder.mkdir()
            (folder / "meta379230.xml").write_text("<root><title>Volume 3</title></root>", encoding="utf-8")
            (folder / "p379230_001.brl").write_bytes(b"a")

            lois_id, errors = determine_lois_id_and_consistency(folder)
            self.assertEqual(lois_id, "379230")
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
