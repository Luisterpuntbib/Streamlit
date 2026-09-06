import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from xml_metadata import parse_xml_book_record


class XmlMetadataTests(unittest.TestCase):
    def test_reads_explicit_metadata_fields(self) -> None:
        with TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "meta378393.xml"
            xml_path.write_text(
                "<document><lois_id>t378393</lois_id><title>De Zoete Zusjes gaan op avontuur</title></document>",
                encoding="utf-8",
            )

            record = parse_xml_book_record(xml_path, "65856")

            self.assertEqual(record.lois_id, "378393")
            self.assertEqual(record.book_number, "65856")
            self.assertEqual(record.title, "De Zoete Zusjes gaan op avontuur")
            self.assertEqual(record.title_slug, "De_Zoete_Zusjes_gaan_op_avontuur")

    def test_title_digits_are_not_used_as_lois_id(self) -> None:
        with TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "meta379230.xml"
            xml_path.write_text(
                "<document><lois_id>t379230</lois_id><title>Project 2024 Volume 3</title></document>",
                encoding="utf-8",
            )

            record = parse_xml_book_record(xml_path, "65000")

            self.assertEqual(record.lois_id, "379230")
            self.assertEqual(record.title, "Project 2024 Volume 3")

    def test_missing_explicit_lois_id_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "meta379230.xml"
            xml_path.write_text("<document><title>Herscht 07769</title></document>", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "geen expliciet <lois_id>-veld"):
                parse_xml_book_record(xml_path, "65000")

    def test_invalid_prefixed_lois_id_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "meta491409.xml"
            xml_path.write_text(
                "<document><lois_id>a491409</lois_id><title>Testboek</title></document>",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "ongeldige Lois ID"):
                parse_xml_book_record(xml_path, "65435")


if __name__ == "__main__":
    unittest.main()
