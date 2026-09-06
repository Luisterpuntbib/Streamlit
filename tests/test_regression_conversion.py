import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline_disk import run_pipeline_disk
from scripts.compare_output_zips import compare_output_zips


class RegressionConversionTests(unittest.TestCase):
    def test_pipeline_output_matches_reference_zip(self) -> None:
        """Regression test: pipeline output must match reference BRF/XML bytes."""

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_zip = root / "input_fixed.zip"
            expected_zip = root / "expected_reference.zip"
            actual_zip = root / "actual_pipeline.zip"

            xml_content = (
                b"<document><lois_id>t374170</lois_id>"
                b"<title>Aan mij heb je niks</title><meta>ongewijzigd</meta></document>"
            )
            brl_content = bytes([37, 93, 65, 66, 10])
            expected_brf_content = bytes([35, 62, 97, 98, 10])

            self._build_input_zip(input_zip, xml_content, brl_content)
            self._build_expected_zip(expected_zip, xml_content, expected_brf_content)
            cnv_path = Path(__file__).resolve().parents[1] / "brl2brf.cnv"

            run_pipeline_disk(
                input_zip_path=input_zip,
                cnv_path=cnv_path,
                output_zip_path=actual_zip,
            )

            result = compare_output_zips(expected_zip=expected_zip, actual_zip=actual_zip)

            details = [
                f"missing_folders={result.missing_folders}",
                f"extra_folders={result.extra_folders}",
                f"missing_files={result.missing_files}",
                f"extra_files={result.extra_files}",
                f"changed_xml={result.changed_xml_files}",
                f"changed_brf={result.changed_brf_files}",
                f"unreadable={result.unreadable_pairs}",
            ]
            self.assertTrue(result.identical, " | ".join(details))

    @staticmethod
    def _build_input_zip(path: Path, xml_content: bytes, brl_content: bytes) -> None:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("63773/meta374170.xml", xml_content)
            archive.writestr("63773/p374170_001.brl", brl_content)

    @staticmethod
    def _build_expected_zip(path: Path, xml_content: bytes, brf_content: bytes) -> None:
        folder = "63773_Aan_mij_heb_je_niks"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(f"{folder}/63773_meta_Aan_mij_heb_je_niks.xml", xml_content)
            archive.writestr(f"{folder}/63773_001_Aan_mij_heb_je_niks.brf", brf_content)


if __name__ == "__main__":
    unittest.main()
