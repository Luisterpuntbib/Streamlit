import unittest

from naming_rules import (
    make_output_brf_name,
    make_output_folder_name,
    make_output_xml_name,
    make_title_slug,
    sanitize_path_name,
)


class NamingRulesTests(unittest.TestCase):
    def test_make_title_slug_replaces_spaces(self) -> None:
        self.assertEqual(make_title_slug("Aan mij heb je niks"), "Aan_mij_heb_je_niks")

    def test_make_title_slug_collapses_whitespace(self) -> None:
        self.assertEqual(make_title_slug("  Aan   mij\t heb je  niks  "), "Aan_mij_heb_je_niks")

    def test_output_name_builders(self) -> None:
        slug = "Aan_mij_heb_je_niks"
        self.assertEqual(make_output_folder_name("63773", slug), "63773_Aan_mij_heb_je_niks")
        self.assertEqual(make_output_xml_name("63773", slug), "63773_meta_Aan_mij_heb_je_niks.xml")
        self.assertEqual(make_output_brf_name("63773", "002", slug), "63773_002_Aan_mij_heb_je_niks.brf")

    def test_sanitize_path_name_replaces_invalid_chars(self) -> None:
        self.assertEqual(sanitize_path_name('ab:c*de?'), "ab_c_de_")


if __name__ == "__main__":
    unittest.main()
