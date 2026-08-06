import io
import unittest

import pandas as pd

from bpost_conversion import build_contact_names, read_formie_csv


class ReadFormieCsvTests(unittest.TestCase):
    def test_reads_semicolon_separated_windows_1252(self):
        source = io.BytesIO("Naam: Voornaam;Naam: Familienaam;Tekst\nRené;Peeters;Iederéén\n".encode("cp1252"))

        result = read_formie_csv(source)

        self.assertEqual(list(result.columns), ["Naam: Voornaam", "Naam: Familienaam", "Tekst"])
        self.assertEqual(result.loc[0, "Tekst"], "Iederéén")

    def test_reads_comma_separated_utf8(self):
        source = io.BytesIO("Naam: First Name,Naam: Last Name\nRené,Peeters\n".encode("utf-8"))

        result = read_formie_csv(source)

        self.assertEqual(list(result.columns), ["Naam: First Name", "Naam: Last Name"])


class BuildContactNamesTests(unittest.TestCase):
    def test_combines_dutch_name_columns(self):
        input_data = pd.DataFrame({"Naam: Voornaam": ["Jan"], "Naam: Familienaam": ["Peeters"]})

        result = build_contact_names(input_data)

        self.assertEqual(result.tolist(), ["Jan Peeters"])

    def test_combines_english_name_columns(self):
        input_data = pd.DataFrame({"Naam: First Name": ["Jane"], "Naam: Last Name": ["Doe"]})

        result = build_contact_names(input_data)

        self.assertEqual(result.tolist(), ["Jane Doe"])

    def test_trims_name_and_accepts_missing_part(self):
        input_data = pd.DataFrame({"Naam: Voornaam": ["  Jan  ", None], "Naam: Familienaam": [None, "  Peeters "]})

        result = build_contact_names(input_data)

        self.assertEqual(result.tolist(), ["Jan", "Peeters"])

    def test_returns_empty_values_without_supported_headers(self):
        input_data = pd.DataFrame({"Organisatie": ["Voorbeeld"]})

        result = build_contact_names(input_data)

        self.assertEqual(result.tolist(), [""])


if __name__ == "__main__":
    unittest.main()
