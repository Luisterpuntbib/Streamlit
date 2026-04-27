"""Streamlit page for ZIP-based Braille conversion.

This page uploads input ZIP + Excel mapping, runs the disk pipeline with the
fixed project conversion table, and offers an output ZIP for download.
"""

from __future__ import annotations

import shutil
import tempfile
import threading
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from braille_models import ProcessingLimits
from brl_conversion import parse_cnv_table_bytes
from excel_mapping import build_excel_index, parse_excel_mapping_file
from navigation import make_sidebar
from pipeline_disk import inspect_input_zip, run_pipeline_disk


@st.cache_data(show_spinner=False)
def _load_conversion_table_cached(cnv_path_str: str) -> dict[int, int]:
    """Load and parse the fixed conversion table once per app cache cycle."""

    cnv_path = Path(cnv_path_str)
    if not cnv_path.is_file():
        raise FileNotFoundError(f"Conversietabel niet gevonden: {cnv_path}")
    return parse_cnv_table_bytes(cnv_path.read_bytes())


def _save_uploaded_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile, destination: Path) -> None:
    """Write an uploaded file to disk without forcing full in-memory copies."""

    uploaded_file.seek(0)
    with destination.open("wb") as handle:
        shutil.copyfileobj(uploaded_file, handle)


def _clear_conversion_state() -> None:
    """Clear stored conversion results and force fresh uploader widgets."""

    st.session_state.braille_summary_rows = None
    st.session_state.braille_output_bytes = None
    st.session_state.braille_uploader_version = st.session_state.get("braille_uploader_version", 0) + 1


def _run_zip_conversion(
    input_zip_file: st.runtime.uploaded_file_manager.UploadedFile,
    excel_file: st.runtime.uploaded_file_manager.UploadedFile,
    cnv_path: Path,
    progress: st.delta_generator.DeltaGenerator,
    max_source_folders: int,
) -> tuple[bytes, list[dict[str, object]]]:
    """Run ZIP conversion from uploaded files and return output ZIP + summary."""

    _ = _load_conversion_table_cached(str(cnv_path.resolve()))

    with tempfile.TemporaryDirectory(prefix="braille_streamlit_") as temp_dir:
        temp_root = Path(temp_dir)
        input_zip_path = temp_root / "input.zip"
        excel_path = temp_root / "mapping.xlsx"
        output_zip_path = temp_root / "output.zip"

        progress.progress(5, text="Uploads voorbereiden...")
        _save_uploaded_file(input_zip_file, input_zip_path)
        _save_uploaded_file(excel_file, excel_path)

        progress.progress(15, text="Input ZIP controleren...")
        inspections = inspect_input_zip(input_zip_path)
        inspection_by_folder = {item["source_folder"]: item for item in inspections}
        folder_count = len(inspections)

        records = parse_excel_mapping_file(excel_path)
        excel_index = build_excel_index(records)

        progress.progress(25, text=f"{folder_count} bronfolders gevonden. Conversie starten...")

        result_box: dict[str, object] = {}

        def _pipeline_worker() -> None:
            try:
                result_box["pipeline_result"] = run_pipeline_disk(
                    input_zip_path=input_zip_path,
                    excel_path=excel_path,
                    cnv_path=cnv_path,
                    output_zip_path=output_zip_path,
                    limits=ProcessingLimits(max_source_folders=max_source_folders),
                )
            except Exception as exc:
                result_box["error"] = exc

        worker = threading.Thread(target=_pipeline_worker, daemon=True)
        worker.start()

        animated_values = [35, 45, 55, 65, 75, 85]
        idx = 0
        while worker.is_alive():
            progress.progress(
                animated_values[idx % len(animated_values)],
                text=f"Bronfolders verwerken... ({folder_count} totaal)",
            )
            idx += 1
            time.sleep(0.25)

        worker.join()

        if "error" in result_box:
            raise result_box["error"]

        if "pipeline_result" not in result_box:
            raise RuntimeError("Verwerking mislukt: pipeline gaf geen resultaat terug.")

        pipeline_result = result_box["pipeline_result"]

        progress.progress(95, text="Resultaten verzamelen...")
        summary_rows: list[dict[str, object]] = []
        for item in pipeline_result.folder_results:
            inspection = inspection_by_folder.get(item.source_folder, {})
            lois_id = inspection.get("lois_id")
            record = excel_index.by_lois_id.get(lois_id) if lois_id else None

            summary_rows.append(
                {
                    "Bronfolder": item.source_folder,
                    "Boeknummer": record.book_number if record else "",
                    "Titel": record.title if record else "",
                    "Outputfolder (boeknummer_titel)": item.output_folder,
                    "Status": item.status,
                    "Geconverteerd": item.converted_count,
                    "Waarschuwingen": " | ".join(item.warnings) if item.warnings else "",
                    "Fouten": " | ".join(item.errors) if item.errors else "",
                }
            )

        output_bytes = output_zip_path.read_bytes()

    progress.progress(100, text="Klaar")
    return output_bytes, summary_rows


make_sidebar()
st.markdown("# 📚 Braille Conversie")
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

# Persist conversion results across reruns (e.g. clicking download buttons).
if "braille_summary_rows" not in st.session_state:
    st.session_state.braille_summary_rows = None
if "braille_output_bytes" not in st.session_state:
    st.session_state.braille_output_bytes = None
if "braille_uploader_version" not in st.session_state:
    st.session_state.braille_uploader_version = 0

uploader_version = st.session_state.braille_uploader_version
input_zip = st.file_uploader("Input ZIP", type=["zip"], key=f"braille_input_zip_{uploader_version}")
excel_file = st.file_uploader("Excel mapping", type=["xlsx", "xls"], key=f"braille_excel_file_{uploader_version}")

max_source_folders = st.number_input(
    "Maximum aantal bronfolders",
    min_value=1,
    max_value=5000,
    value=150,
    step=1,
    help="Verhoog dit als je input-ZIP meer dan 150 bronfolders bevat.",
)

if st.button("Verwerken", type="primary"):
    if input_zip is None and excel_file is None:
        st.error("Upload eerst een input-ZIP en een Excel-bestand.")
    elif input_zip is None:
        st.error("Upload eerst een input-ZIP.")
    elif excel_file is None:
        st.error("Upload eerst een Excel-bestand.")
    else:
        progress = st.progress(0, text="Starten...")
        try:
            cnv_path = Path(__file__).resolve().parents[1] / "brl2brf.cnv"
            output_bytes, summary_rows = _run_zip_conversion(
                input_zip_file=input_zip,
                excel_file=excel_file,
                cnv_path=cnv_path,
                progress=progress,
                max_source_folders=int(max_source_folders),
            )

            st.session_state.braille_summary_rows = summary_rows
            st.session_state.braille_output_bytes = output_bytes
            st.success("Verwerking voltooid.")
        except Exception as exc:
            st.error(f"Verwerking mislukt: {exc}")

if st.session_state.braille_summary_rows and st.session_state.braille_output_bytes:
    st.subheader("Samenvatting per bronfolder")

    summary_df = pd.DataFrame(st.session_state.braille_summary_rows)
    st.dataframe(summary_df, width="stretch")

    summary_csv = summary_df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        label="Download samenvatting (CSV)",
        data=summary_csv,
        file_name="braille_summary.csv",
        mime="text/csv",
    )

    st.download_button(
        label="Download output ZIP",
        data=st.session_state.braille_output_bytes,
        file_name="braille_output.zip",
        mime="application/zip",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Nieuwe conversie"):
            _clear_conversion_state()
            st.rerun()
    with col2:
        if st.button("Terug naar inhoud"):
            _clear_conversion_state()
            st.switch_page("pages/01_inhoud.py")
