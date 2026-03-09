import unittest

from braille_models import BookRecord
from excel_mapping import ExcelIndex
from reporting import build_excel_no_match_report


class ReportingTests(unittest.TestCase):
    def test_build_excel_no_match_report_with_suggestion(self) -> None:
        record = BookRecord(
            excel_row=2,
            title="Titel",
            title_slug="Titel",
            book_number="1000",
            lois_id="378851",
        )
        index = ExcelIndex(by_lois_id={record.lois_id: record}, by_book_number={record.book_number: record})

        lines = build_excel_no_match_report("378531", index)

        self.assertTrue(any("Geen Excel-match op Lois ID" in line for line in lines))
        self.assertTrue(any("Lois ID in Excel lijkt fout (mogelijke typefout)." in line for line in lines))
        self.assertTrue(any("Gevonden Lois ID uit input: 378531" in line for line in lines))
        self.assertTrue(any("Dichtstbijzijnde Lois ID in Excel: 378851" in line for line in lines))

    def test_build_excel_no_match_report_without_suggestion(self) -> None:
        record = BookRecord(
            excel_row=2,
            title="Titel",
            title_slug="Titel",
            book_number="1000",
            lois_id="374170",
        )
        index = ExcelIndex(by_lois_id={record.lois_id: record}, by_book_number={record.book_number: record})

        lines = build_excel_no_match_report("999999", index)

        self.assertTrue(any("Geen Excel-match op Lois ID" in line for line in lines))
        self.assertFalse(any("Lois ID in Excel lijkt fout (mogelijke typefout)." in line for line in lines))


if __name__ == "__main__":
    unittest.main()
