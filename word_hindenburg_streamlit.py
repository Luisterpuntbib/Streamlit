import streamlit as st

from docx import Document
from html import escape
from datetime import datetime

# ========================================================
# FUNCTIE: WORD-STIJL OMZETTEN NAAR HINDENBURG-TAG
# ========================================================

def bepaal_hindenburg_tag(style_name):
    """
    Zet een Word-kopstijl om naar een Hindenburg-tag.

    Mogelijke resultaten:

        h1
        h2
        h3
        h4
        h5
        h6

    Wanneer geen ondersteunde kopstijl wordt
    gevonden, wordt None teruggegeven.
    """

    style_name = style_name.lower()

    stijl_mapping = {
        "kop 1": "h1",
        "kop 2": "h2",
        "kop 3": "h3",
        "kop 4": "h4",
        "kop 5": "h5",
        "kop 6": "h6",
        "heading 1": "h1",
        "heading 2": "h2",
        "heading 3": "h3",
        "heading 4": "h4",
        "heading 5": "h5",
        "heading 6": "h6",
    }

    for stijl, tag in stijl_mapping.items():

        if style_name.startswith(stijl):
            return tag

    return None

# ========================================================
# Lege container voor streamlit
# ========================================================

def verwerk_document (docx_bestand):
    # ========================================================
    # DOCUMENT OPENEN
    # ========================================================

    try:

        doc = Document(docx_bestand)

    except Exception as fout:

        st.error(
            f"Fout bij openen document: {fout}"
        )

        return None, None

# ========================================================
# STARTTIJD REGISTREREN
# ========================================================

    start_time = datetime.now()

# ========================================================
# UITVOERLIJSTEN INITIALISEREN
# ========================================================

    html_output = ["<body>"]
    log_output = []

# ========================================================
# LOGBESTAND OPSTARTEN
# ========================================================

    log_output.append("=" * 60)
    log_output.append("VERWERKINGSLOG")
    log_output.append("=" * 60)
    log_output.append("")
    log_output.append(f"Inputbestand : {docx_bestand}")
    log_output.append(f"Starttijd    : {start_time}")
    log_output.append("")

# ========================================================
# TELLERS
# ========================================================

    counter = 1

    count_h1 = 0
    count_h2 = 0
    count_h3 = 0
    count_h4 = 0
    count_h5 = 0
    count_h6 = 0

# ========================================================
# ALLE PARAGRAFEN DOORLOPEN
# ========================================================

    for para in doc.paragraphs:

    # ----------------------------------------------------
    # TEKST OPHALEN
    # ----------------------------------------------------

        text = para.text.strip()

        # ----------------------------------------------------
        # LEGE PARAGRAFEN OVERSLAAN
        # ----------------------------------------------------

        if not text:
            continue

        # ----------------------------------------------------
        # HINDENBURG-TAG BEPALEN
        # ----------------------------------------------------

        tag = bepaal_hindenburg_tag(
            para.style.name
        )

        # ----------------------------------------------------
        # ALLE NIET-KOPPEN OVERSLAAN
        # ----------------------------------------------------

        if tag is None:
            continue

        # ----------------------------------------------------
        # UNIEKE ID AANMAKEN
        # ----------------------------------------------------

        element_id = f"hix{counter:05d}"

        # ----------------------------------------------------
        # TELLERS BIJWERKEN
        # ----------------------------------------------------

        if tag == "h1":
            count_h1 += 1

        elif tag == "h2":
            count_h2 += 1

        elif tag == "h3":
            count_h3 += 1

        elif tag == "h4":
            count_h4 += 1

        elif tag == "h5":
            count_h5 += 1

        elif tag == "h6":
            count_h6 += 1

        # ----------------------------------------------------
        # HTML TOEVOEGEN
        # ----------------------------------------------------

        html_output.append(
            f'<{tag} id="{element_id}">'
            f'{escape(text)}'
            f'</{tag}>'
        )

        # ----------------------------------------------------
        # LOGREGEL TOEVOEGEN
        # ----------------------------------------------------

        log_output.append("-" * 60)
        log_output.append(f"Element     : {counter}")
        log_output.append(f"ID          : {element_id}")
        log_output.append(f"Word stijl  : {para.style.name}")
        log_output.append(f"Hindenburg  : {tag}")
        log_output.append(f"Inhoud      : {text}")
        log_output.append("")

        # ----------------------------------------------------
        # VOORTGANG TONEN
        # ----------------------------------------------------

        preview = text[:70]

        counter += 1

# ========================================================
# HTML AFSLUITEN
# ========================================================

    html_output.append("</body>")

    # ========================================================
    # SAMENVATTING LOG
    # ========================================================

    log_output.append("")
    log_output.append("=" * 60)
    log_output.append("SAMENVATTING")
    log_output.append("=" * 60)

    log_output.append(f"Totaal elementen : {counter - 1}")
    log_output.append(f"H1               : {count_h1}")
    log_output.append(f"H2               : {count_h2}")
    log_output.append(f"H3               : {count_h3}")
    log_output.append(f"H4               : {count_h4}")
    log_output.append(f"H5               : {count_h5}")
    log_output.append(f"H6               : {count_h6}")

    log_output.append("")

    log_output.append("Bronbestand       : bronbestand.txt")
    log_output.append("Logbestand        : verwerkingslog.txt")
    log_output.append("")
    log_output.append(f"Eindtijd         : {datetime.now()}")
# ========================================================
# bronbestand en logbestand schrijven
# ========================================================
    bronbestand = "\n".join(html_output)
    logbestand = "\n".join(log_output)

    return bronbestand, logbestand

# ========================================================
# Streamlit
# ========================================================
st.title("Word naar Hindenburg Bronbestand")

uploaded_file = st.file_uploader(
    "kies een Word-document",
    type=["docx"]
)
if uploaded_file is not None:
    bronbestand,logbestand = verwerk_document(
        uploaded_file
    )

    if bronbestand is None:
        st.stop()
# ========================================================
# Succesmelding
# ========================================================

    st.success("Verwerking voltooid")

# ========================================================
# Downloadknop
# ========================================================

    st.download_button(
        label="Download bronbestand",
        data=bronbestand,
        file_name="bronbestand.txt",
        mime="text/plain"
    )

# ========================================================
# Downloadknop logbestand
# ========================================================

    st.download_button(
        label="Download logbestand",
        data=logbestand,
        file_name="verwerkingslog.txt",
        mime="text/plain"
    )
