"""Streamlit page for ZIP-based Braille conversion.

This page uploads input ZIP + Excel mapping, runs the disk pipeline with the
fixed project conversion table, and offers an output ZIP for download.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from navigation import make_sidebar
from pipeline_disk import run_pipeline_disk


def _run_zip_conversion(input_zip_bytes: bytes, excel_bytes: bytes, cnv_path: Path) -> tuple[bytes, list[dict[str, object]]]:
    """Run ZIP conversion from uploaded bytes and return output ZIP bytes.

    Args:
        input_zip_bytes: Raw bytes of uploaded input ZIP.
        excel_bytes: Raw bytes of uploaded Excel mapping file.
        cnv_path: Path to the fixed `.cnv` conversion table.

    Returns:
        Tuple ``(output_zip_bytes, summary_rows)`` where ``summary_rows`` is
        suitable for dataframe rendering.

    Raises:
        FileNotFoundError: If the conversion table is missing.
        Exception: Any pipeline-level processing failure.
    """

    if not cnv_path.is_file():
        raise FileNotFoundError(f"Conversietabel niet gevonden: {cnv_path}")

    with tempfile.TemporaryDirectory(prefix="braille_streamlit_") as temp_dir:
        temp_root = Path(temp_dir)
        input_zip_path = temp_root / "input.zip"
        excel_path = temp_root / "mapping.xlsx"
        output_zip_path = temp_root / "output.zip"

        input_zip_path.write_bytes(input_zip_bytes)
        excel_path.write_bytes(excel_bytes)

        pipeline_result = run_pipeline_disk(
            input_zip_path=input_zip_path,
            excel_path=excel_path,
            cnv_path=cnv_path,
            output_zip_path=output_zip_path,
        )

        summary_rows: list[dict[str, object]] = []
        for item in pipeline_result.folder_results:
            summary_rows.append(
                {
                    "Bronfolder": item.source_folder,
                    "Status": item.status,
                    "Geconverteerd": item.converted_count,
                    "Waarschuwingen": " | ".join(item.warnings) if item.warnings else "",
                    "Fouten": " | ".join(item.errors) if item.errors else "",
                }
            )

        output_bytes = output_zip_path.read_bytes()

    return output_bytes, summary_rows


make_sidebar()
st.markdown("# ⠃ Braille Conversie")
st.write(
    "Met deze pagina zet je braillebronbestanden om naar een output-ZIP die je direct kunt downloaden. "
    "Je uploadt één input-ZIP en één Excel-bestand."
)

with st.expander("Hulp: hoe gebruik ik deze pagina?", expanded=False):
    st.markdown(
        """
**Wat heb je nodig?**
- Een **input-ZIP** met één of meerdere bronfolders.
- Een **Excel-bestand** met boekgegevens.

**Hoe moet de ZIP opgebouwd zijn?**
- In de ZIP staan bronfolders op het hoogste niveau.
- Elke bronfolder bevat:
  - exact **1 XML-bestand**
  - **1 of meer `.brl`-bestanden**
- Voorbeeld:
  - `374170_1_1/meta374170.xml`
  - `374170_1_1/p374170_001.brl`

**Welke Excel-kolommen worden gebruikt?**
- **Kolom B** = titel
- **Kolom C** = Lois ID
- **Kolom E** = boeknummer
- **Rij 1 wordt overgeslagen** (koprij/titelrij)

**Hoe worden outputnamen gemaakt?**
- Outputfolder: `{boeknummer}_{titel_slug}`
- XML-bestandsnaam: `{boeknummer}_meta_{titel_slug}.xml`
- BRF-bestandsnaam: `{boeknummer}_{volume}_{titel_slug}.brf`

**Belangrijk**
- De **XML-inhoud wordt niet aangepast**.
- Alleen de **bestandsnaam** van de XML kan wijzigen.

**Veelvoorkomende fouten**
- "exact 1 XML-bestand": er ontbreekt XML of er staan er meerdere in een bronfolder.
- "minstens 1 .brl-bestand": er staan geen `.brl`-bestanden in een bronfolder.
- "Geen Excel-match op Lois ID": de Lois ID uit de input is niet teruggevonden in Excel kolom C.
- "Inconsistente Lois ID": de Lois ID in map-/bestandsnamen komt niet overeen binnen dezelfde bronfolder.
        """
    )

input_zip = st.file_uploader("Input ZIP", type=["zip"])
excel_file = st.file_uploader("Excel mapping", type=["xlsx", "xls"])

if st.button("Verwerken", type="primary"):
    if input_zip is None and excel_file is None:
        st.error("Upload eerst een input-ZIP en een Excel-bestand.")
    elif input_zip is None:
        st.error("Upload eerst een input-ZIP.")
    elif excel_file is None:
        st.error("Upload eerst een Excel-bestand.")
    else:
        try:
            cnv_path = Path(__file__).resolve().parents[1] / "brl2brf.cnv"
            output_bytes, summary_rows = _run_zip_conversion(
                input_zip_bytes=input_zip.getvalue(),
                excel_bytes=excel_file.getvalue(),
                cnv_path=cnv_path,
            )

            st.success("Verwerking voltooid.")
            st.subheader("Samenvatting per bronfolder")
            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

            st.download_button(
                label="Download output ZIP",
                data=output_bytes,
                file_name="braille_output.zip",
                mime="application/zip",
            )
        except Exception as exc:
            st.error(f"Verwerking mislukt: {exc}")
