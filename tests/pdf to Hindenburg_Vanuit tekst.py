import streamlit as st
import pymupdf

# ============================================================
# PAGINA-INSTELLINGEN
# ============================================================

st.set_page_config(
    page_title="PDF naar ncc",
    layout="wide",
)


# ============================================================
# TITEL
# ============================================================

st.title("PDF naar Hindenburg-bronbestand")

st.write(
    "Upload een PDF, stel de verwerking in en maak "
    "automatisch een Hindenburg-bronbestand."
)


# ============================================================
# PDF-BESTAND
# ============================================================

st.header("PDF-bestand")

pdf_bestand = st.file_uploader(
    "Selecteer het PDF-bestand",
    type=["pdf"]
)

if pdf_bestand is not None:
    st.success(f"PDF geladen: {pdf_bestand.name}")

# ============================================================
# PDF ANALYSEREN
# ============================================================

gesorteerde_profielen = []
profiel_nummers = {}
voorbeelden = {}
aantal_pdf_paginas = 0
opmaakprofielen_html = ""

if pdf_bestand is not None:

    pdf_bytes = pdf_bestand.getvalue()

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    aantal_pdf_paginas = len(document)

    opmaakprofielen = set()
    voorbeelden = {}

    for pagina_nummer, pagina in enumerate(document, start=1):

        pagina_data = pagina.get_text("dict")

        for blok in pagina_data["blocks"]:

            if "lines" not in blok:
                continue

            for regel in blok["lines"]:

                for span in regel["spans"]:

                    grootte = round(span["size"] * 2) / 2

                    profiel = (
                        span["font"],
                        grootte,
                        span["flags"],
                        span["color"],
                    )

                    opmaakprofielen.add(profiel)

                    tekst = span["text"].strip()

                    if tekst:

                        if profiel not in voorbeelden:
                            voorbeelden[profiel] = []

                        if len(voorbeelden[profiel]) < 5:
                            voorbeelden[profiel].append(tekst)

    gesorteerde_profielen = sorted(
        opmaakprofielen,
        key=lambda profiel: (
            -profiel[1],
            profiel[0],
            profiel[2],
            profiel[3],
        )
    )

    profiel_nummers = {
        profiel: nummer
        for nummer, profiel in enumerate(
            gesorteerde_profielen,
            start=1
        )
    }

    document.close()

    # ========================================================
    # HTML-RAPPORT OPMAAKPROFIELEN OPBOUWEN
    # ========================================================

    html_regels = [
        "<!DOCTYPE html>",
        "<html lang='nl'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>Opmaakprofielen</title>",
        "<style>",
        "body {",
        "    font-family: Arial, sans-serif;",
        "    max-width: 1000px;",
        "    margin: 40px auto;",
        "    padding: 0 20px;",
        "    color: #222222;",
        "}",
        "h1 {",
        "    border-bottom: 2px solid #333333;",
        "    padding-bottom: 10px;",
        "}",
        ".profiel {",
        "    border: 1px solid #cccccc;",
        "    border-radius: 8px;",
        "    padding: 20px;",
        "    margin-bottom: 25px;",
        "    background-color: #f8f8f8;",
        "}",
        ".profiel h2 {",
        "    margin-top: 0;",
        "}",
        ".technische-info {",
        "    line-height: 1.6;",
        "}",
        ".kleurvlak {",
        "    display: inline-block;",
        "    width: 18px;",
        "    height: 18px;",
        "    border: 1px solid #777777;",
        "    vertical-align: middle;",
        "    margin-left: 8px;",
        "}",
        ".voorbeeld {",
        "    background-color: #ffffff;",
        "    padding: 8px 12px;",
        "    margin: 6px 0;",
        "    border-left: 4px solid #cccccc;",
        "}",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Opmaakprofielen</h1>",
    ]

    for profiel_nummer, profiel in enumerate(
        gesorteerde_profielen,
        start=1
    ):
        font = profiel[0]
        grootte = profiel[1]
        flags = profiel[2]
        kleur = profiel[3]

        rood = (kleur >> 16) & 255
        groen = (kleur >> 8) & 255
        blauw = kleur & 255

        html_kleur = f"#{rood:02X}{groen:02X}{blauw:02X}"

        # Helderheid van de originele tekstkleur bepalen
        helderheid = (
                0.299 * rood
                + 0.587 * groen
                + 0.114 * blauw
        )

        # Te lichte tekst is slecht leesbaar op de witte achtergrond.
        # In dat geval gebruiken we alleen voor het voorbeeld zwart.
        if helderheid > 180:
            voorbeeld_kleur = "#000000"
        else:
            voorbeeld_kleur = html_kleur

        html_regels.append(
            "<div class='profiel'>"
        )

        html_regels.append(
            f"<h2>Opmaakprofiel {profiel_nummer}</h2>"
        )

        html_regels.append(
            "<div class='technische-info'>"
        )

        html_regels.append(
            f"<strong>Font:</strong> {font}<br>"
        )

        html_regels.append(
            f"<strong>Grootte:</strong> {grootte}<br>"
        )

        html_regels.append(
            f"<strong>Flags:</strong> {flags}<br>"
        )

        html_regels.append(
            f"<strong>Kleur:</strong> {html_kleur}"
            f"<span class='kleurvlak' "
            f"style='background-color: {html_kleur};'></span>"
        )

        html_regels.append(
            "</div>"
        )

        html_regels.append(
            "<h3>Voorbeelden</h3>"
        )

        for tekst in voorbeelden.get(profiel, []):
            html_regels.append(
                f"<div class='voorbeeld' "
                f"style=\""
                f"font-family: '{font}', Arial, sans-serif; "
                f"font-size: {grootte}pt; "
                f"color: {voorbeeld_kleur};"
                f"\">"
                f"{tekst}"
                f"</div>"
            )

        html_regels.append(
            "</div>"
        )

    html_regels.extend([
        "</body>",
        "</html>",
    ])

    opmaakprofielen_html = "\n".join(html_regels)

# ============================================================
# INSTELLINGEN
# ============================================================

st.header("Instellingen")


# ------------------------------------------------------------
# TITEL
# ------------------------------------------------------------

st.subheader("Titel")

Titel = st.text_input(
    "Titel van het boek"
)


# ------------------------------------------------------------
# START EN EINDE BOEK
# ------------------------------------------------------------

st.subheader("Start en einde boek")

st.markdown("#### Start")

start_boekpagina = st.number_input(
    "Eerste pagina boek",
    min_value=1,
    value=1,
    step=1
)

start_fysieke_pagina = st.number_input(
    "Eerste pagina PDF",
    min_value=1,
    value=1,
    step=1
)

st.markdown("#### Einde")

eind_fysieke_pagina = st.number_input(
    "Laatste pagina PDF",
    min_value=1,
    value=1,
    step=1
)


# ------------------------------------------------------------
# PAGINA-INDELING
# ------------------------------------------------------------

st.subheader("Pagina-indeling")

boekpaginas_per_fysieke_pagina = st.radio(
    "Aantal boekpagina's per PDF-pagina",
    options=[1, 2],
    horizontal=True
)

if boekpaginas_per_fysieke_pagina == 2:

    start_deelpagina = st.radio(
        "Positie eerste boekpagina",
        options=[1, 2],
        horizontal=True
    )

    eind_deelpagina = st.radio(
        "Positie laatste boekpagina",
        options=[1, 2],
        horizontal=True
    )

else:
    start_deelpagina = 1
    eind_deelpagina = 1

# ------------------------------------------------------------
# OPMAAKPROFIELEN TOEWIJZEN AAN HEADERS
# ------------------------------------------------------------

st.subheader("Opmaakprofielen toewijzen aan Headers")

if pdf_bestand is not None:

    st.download_button(
        label="Download opmaakprofielen",
        data=opmaakprofielen_html,
        file_name="opmaakprofielen.html",
        mime="text/html",
        key="download_opmaakprofielen"
    )

else:
    st.info("Upload eerst een PDF-bestand.")

st.write(
    "Vul per Headerniveau de nummers van de gewenste "
    "opmaakprofielen in. Scheid meerdere profielnummers "
    "met een komma."
)

header_profielen = {}
header_fouten = []

for header_niveau in range(1, 7):

    invoer = st.text_input(
        f"Header {header_niveau}",
        key=f"header_{header_niveau}"
    )

    if invoer:

        profiel_invoer = invoer.split(",")

        for profiel_nummer in profiel_invoer:

            profiel_nummer = profiel_nummer.strip()

            # Leeg onderdeel negeren
            if not profiel_nummer:
                continue

            # Controle: is de invoer een getal?
            if not profiel_nummer.isdigit():

                header_fouten.append(
                    f"'{profiel_nummer}' is geen geldig "
                    f"opmaakprofielnummer bij Header {header_niveau}."
                )

                continue

            profiel_nummer = int(profiel_nummer)

            # Controle: bestaat dit profiel?
            if (
                pdf_bestand is not None
                and profiel_nummer > len(gesorteerde_profielen)
            ):

                header_fouten.append(
                    f"Opmaakprofiel {profiel_nummer} bestaat niet. "
                    f"De PDF bevat {len(gesorteerde_profielen)} "
                    f"opmaakprofielen."
                )

                continue

            # Controle: is dit profiel al aan een andere Header toegewezen?
            if profiel_nummer in header_profielen:

                bestaand_niveau = header_profielen[profiel_nummer]

                if bestaand_niveau != header_niveau:

                    header_fouten.append(
                        f"Opmaakprofiel {profiel_nummer} is zowel "
                        f"aan Header {bestaand_niveau} als "
                        f"Header {header_niveau} toegewezen."
                    )

                    continue

            header_profielen[profiel_nummer] = header_niveau

for fout in header_fouten:
    st.error(fout)

# ------------------------------------------------------------
# ALGEMENE OPMAAK begin
# ------------------------------------------------------------

st.subheader("Algemene opmaak")

st.markdown("#### Begin")


# Standaardlijst één keer aanmaken
if "opmaak_begin" not in st.session_state:

    st.session_state.opmaak_begin = [
        {"tekst": "Bibliotheekgegevens", "actief": True},
        {"tekst": "Boekgegevens", "actief": True},
        {"tekst": "Omslagtekst", "actief": True},
        {"tekst": "Inhoud", "actief": True},
        {"tekst": "Citaat", "actief": False},
        {"tekst": "Opdracht", "actief": False},
        {"tekst": "Voorwoord", "actief": False},
        {"tekst": "Dankwoord", "actief": False},
    ]


# ------------------------------------------------------------
# BESTAANDE ITEMS TONEN
# ------------------------------------------------------------

for index, item in enumerate(st.session_state.opmaak_begin):

    kolom_selectie, kolom_tekst, kolom_omhoog, kolom_omlaag = st.columns(
        [1, 6, 1, 1]
    )

    with kolom_selectie:
        item["actief"] = st.checkbox(
            "Gebruiken",
            value=item["actief"],
            key=f"begin_actief_{index}",
            label_visibility="collapsed"
        )

    with kolom_tekst:
        st.write(item["tekst"])

    with kolom_omhoog:
        if st.button(
            "↑",
            key=f"begin_omhoog_{index}",
            disabled=(index == 0)
        ):
            st.session_state.opmaak_begin[index - 1], st.session_state.opmaak_begin[index] = (
                st.session_state.opmaak_begin[index],
                st.session_state.opmaak_begin[index - 1]
            )
            st.rerun()

    with kolom_omlaag:
        if st.button(
            "↓",
            key=f"begin_omlaag_{index}",
            disabled=(index == len(st.session_state.opmaak_begin) - 1)
        ):
            st.session_state.opmaak_begin[index + 1], st.session_state.opmaak_begin[index] = (
                st.session_state.opmaak_begin[index],
                st.session_state.opmaak_begin[index + 1]
            )
            st.rerun()

# ------------------------------------------------------------
# EXTRA ITEM TOEVOEGEN
# ------------------------------------------------------------

def voeg_extra_begin_toe():

    tekst = st.session_state.extra_begin.strip()

    if tekst:
        st.session_state.opmaak_begin.append(
            {
                "tekst": tekst,
                "actief": True
            }
        )

        st.session_state.extra_begin = ""


st.text_input(
    "Extra onderdeel",
    key="extra_begin"
)

st.button(
    "Extra item toevoegen",
    key="extra_begin_toevoegen",
    on_click=voeg_extra_begin_toe
)

# ------------------------------------------------------------
# DEFINITIEVE LIJST OPBOUWEN
# ------------------------------------------------------------

extra_headers_begin = [Titel]

for item in st.session_state.opmaak_begin:

    if item["actief"]:
        extra_headers_begin.append(item["tekst"])

# ------------------------------------------------------------
# ALGEMENE OPMAAK - EINDE
# ------------------------------------------------------------

st.markdown("#### Einde")


# Standaardlijst één keer aanmaken
if "opmaak_einde" not in st.session_state:

    st.session_state.opmaak_einde = [
        {"tekst": "Register", "actief": False},
        {"tekst": "Bibliografie", "actief": False},
        {"tekst": "Index", "actief": False},
        {"tekst": "Einde van het boek", "actief": True},
    ]


# ------------------------------------------------------------
# BESTAANDE ITEMS TONEN
# ------------------------------------------------------------

for index, item in enumerate(st.session_state.opmaak_einde):

    kolom_selectie, kolom_tekst, kolom_omhoog, kolom_omlaag = st.columns(
        [1, 6, 1, 1]
    )

    with kolom_selectie:
        item["actief"] = st.checkbox(
            "Gebruiken",
            value=item["actief"],
            key=f"einde_actief_{index}",
            label_visibility="collapsed"
        )

    with kolom_tekst:
        st.write(item["tekst"])

    with kolom_omhoog:
        if st.button(
            "↑",
            key=f"einde_omhoog_{index}",
            disabled=(index == 0)
        ):
            st.session_state.opmaak_einde[index - 1], st.session_state.opmaak_einde[index] = (
                st.session_state.opmaak_einde[index],
                st.session_state.opmaak_einde[index - 1]
            )
            st.rerun()

    with kolom_omlaag:
        if st.button(
            "↓",
            key=f"einde_omlaag_{index}",
            disabled=(index == len(st.session_state.opmaak_einde) - 1)
        ):
            st.session_state.opmaak_einde[index + 1], st.session_state.opmaak_einde[index] = (
                st.session_state.opmaak_einde[index],
                st.session_state.opmaak_einde[index + 1]
            )
            st.rerun()


# ------------------------------------------------------------
# EXTRA ITEM TOEVOEGEN
# ------------------------------------------------------------

def voeg_extra_einde_toe():

    tekst = st.session_state.extra_einde.strip()

    if tekst:
        st.session_state.opmaak_einde.append(
            {
                "tekst": tekst,
                "actief": True
            }
        )

        st.session_state.extra_einde = ""


st.text_input(
    "Extra onderdeel einde",
    key="extra_einde"
)

st.button(
    "Extra item toevoegen",
    key="extra_einde_toevoegen",
    on_click=voeg_extra_einde_toe
)


# ------------------------------------------------------------
# DEFINITIEVE LIJST OPBOUWEN
# ------------------------------------------------------------

extra_headers_einde = []

for item in st.session_state.opmaak_einde:

    if item["actief"]:
        extra_headers_einde.append(item["tekst"])

# ============================================================
# INSTELLINGEN CONTROLEREN
# ============================================================

basis_fouten = []


# ------------------------------------------------------------
# TITEL CONTROLEREN
# ------------------------------------------------------------

if not Titel.strip():
    basis_fouten.append(
        "Vul eerst de titel van het boek in."
    )


# ------------------------------------------------------------
# BEGIN- EN EINDPAGINA CONTROLEREN
# ------------------------------------------------------------

if eind_fysieke_pagina < start_fysieke_pagina:
    basis_fouten.append(
        "De laatste PDF-pagina moet gelijk aan of groter zijn "
        "dan de eerste PDF-pagina."
    )


# ------------------------------------------------------------
# PDF-PAGINABEREIK CONTROLEREN
# ------------------------------------------------------------

if pdf_bestand is not None:

    if start_fysieke_pagina > aantal_pdf_paginas:
        basis_fouten.append(
            f"Eerste PDF-pagina {start_fysieke_pagina} bestaat niet. "
            f"De PDF bevat {aantal_pdf_paginas} pagina's."
        )

    if eind_fysieke_pagina > aantal_pdf_paginas:
        basis_fouten.append(
            f"Laatste PDF-pagina {eind_fysieke_pagina} bestaat niet. "
            f"De PDF bevat {aantal_pdf_paginas} pagina's."
        )


# ------------------------------------------------------------
# FOUTMELDINGEN TONEN
# ------------------------------------------------------------

for fout in basis_fouten:
    st.error(fout)

# ------------------------------------------------------------
# ALLE CONTROLES SAMENBRENGEN
# ------------------------------------------------------------

alle_fouten = header_fouten + basis_fouten

instellingen_geldig = (
    pdf_bestand is not None
    and len(alle_fouten) == 0
)

# ============================================================
# VERWERKING
# ============================================================

st.header("Verwerking")

boekstructuur = []
hindenburg_bronbestand = ""
logbestand = ""

if instellingen_geldig:

    # PDF opnieuw openen voor de eigenlijke verwerking
    pdf_bytes = pdf_bestand.getvalue()

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    huidig_header_profiel = None
    huidig_header_niveau = None
    huidige_header_teksten = []
    huidige_header_boekpagina = None

    for pagina_nummer, pagina in enumerate(document, start=1):

        if pagina_nummer < start_fysieke_pagina:
            continue

        if pagina_nummer > eind_fysieke_pagina:
            break

        # Sluit een eventuele Header van de vorige fysieke pagina af
        if huidig_header_profiel is not None and huidige_header_teksten:
            boekstructuur.append({
                "type": "header",
                "niveau": huidig_header_niveau,
                "tekst": " ".join(huidige_header_teksten),
                "boekpagina": huidige_header_boekpagina,
            })

            huidig_header_profiel = None
            huidig_header_niveau = None
            huidige_header_teksten = []
            huidige_header_boekpagina = None

        pagina_data = pagina.get_text("dict")

        # ====================================================
        # TYPE 1: één boekpagina per fysieke PDF-pagina
        # ====================================================

        if boekpaginas_per_fysieke_pagina == 1:

            boekpagina = start_boekpagina + (
                pagina_nummer - start_fysieke_pagina
            )

            boekstructuur.append({
                "type": "pagina",
                "boekpagina": boekpagina,
                "fysieke_pagina": pagina_nummer,
            })

            for blok in pagina_data["blocks"]:

                if "lines" not in blok:
                    continue

                for regel in blok["lines"]:

                    for span in regel["spans"]:

                        grootte = round(span["size"] * 2) / 2

                        profiel = (
                            span["font"],
                            grootte,
                            span["flags"],
                            span["color"],
                        )

                        profiel_nummer = profiel_nummers[profiel]

                        if profiel_nummer in header_profielen:
                            header_niveau = header_profielen[profiel_nummer]
                            tekst = span["text"].strip()

                            if huidig_header_profiel == profiel_nummer:

                                if tekst:
                                    huidige_header_teksten.append(tekst)

                            else:

                                if (
                                    huidig_header_profiel is not None
                                    and huidige_header_teksten
                                ):
                                    boekstructuur.append({
                                        "type": "header",
                                        "niveau": huidig_header_niveau,
                                        "tekst": " ".join(
                                            huidige_header_teksten
                                        ),
                                        "boekpagina":
                                            huidige_header_boekpagina,
                                    })

                                huidig_header_profiel = profiel_nummer
                                huidig_header_niveau = header_niveau
                                huidige_header_teksten = []
                                huidige_header_boekpagina = boekpagina

                                if tekst:
                                    huidige_header_teksten.append(tekst)

        # ====================================================
        # TYPE 2: twee boekpagina's per fysieke PDF-pagina
        # ====================================================

        elif boekpaginas_per_fysieke_pagina == 2:

            midden_x = pagina.rect.width / 2
            fysieke_offset = pagina_nummer - start_fysieke_pagina

            linker_boekpagina = (
                start_boekpagina
                + fysieke_offset * 2
                - (start_deelpagina - 1)
            )

            rechter_boekpagina = linker_boekpagina + 1

            # We verwerken bewust eerst links en daarna rechts
            for deelpagina in (1, 2):

                # Linkerhelft van de eerste spread eventueel overslaan
                if (
                    pagina_nummer == start_fysieke_pagina
                    and deelpagina < start_deelpagina
                ):
                    continue

                # Rechterhelft van de laatste spread eventueel overslaan
                if (
                    pagina_nummer == eind_fysieke_pagina
                    and deelpagina > eind_deelpagina
                ):
                    continue

                if deelpagina == 1:
                    boekpagina = linker_boekpagina
                else:
                    boekpagina = rechter_boekpagina

                # Een eventuele Header van de vorige deelpagina afsluiten
                if (
                    huidig_header_profiel is not None
                    and huidige_header_teksten
                ):
                    boekstructuur.append({
                        "type": "header",
                        "niveau": huidig_header_niveau,
                        "tekst": " ".join(huidige_header_teksten),
                        "boekpagina": huidige_header_boekpagina,
                    })

                    huidig_header_profiel = None
                    huidig_header_niveau = None
                    huidige_header_teksten = []
                    huidige_header_boekpagina = None

                # Eerst de paginamarkering
                boekstructuur.append({
                    "type": "pagina",
                    "boekpagina": boekpagina,
                    "fysieke_pagina": pagina_nummer,
                })

                # Daarna uitsluitend deze helft onderzoeken
                for blok in pagina_data["blocks"]:

                    if "lines" not in blok:
                        continue

                    for regel in blok["lines"]:

                        for span in regel["spans"]:

                            x0 = span["bbox"][0]

                            if deelpagina == 1 and x0 >= midden_x:
                                continue

                            if deelpagina == 2 and x0 < midden_x:
                                continue

                            grootte = round(span["size"] * 2) / 2

                            profiel = (
                                span["font"],
                                grootte,
                                span["flags"],
                                span["color"],
                            )

                            profiel_nummer = profiel_nummers[profiel]

                            if profiel_nummer in header_profielen:
                                header_niveau = (
                                    header_profielen[profiel_nummer]
                                )
                                tekst = span["text"].strip()

                                if (
                                    huidig_header_profiel
                                    == profiel_nummer
                                ):

                                    if tekst:
                                        huidige_header_teksten.append(
                                            tekst
                                        )

                                else:

                                    if (
                                        huidig_header_profiel is not None
                                        and huidige_header_teksten
                                    ):
                                        boekstructuur.append({
                                            "type": "header",
                                            "niveau":
                                                huidig_header_niveau,
                                            "tekst": " ".join(
                                                huidige_header_teksten
                                            ),
                                            "boekpagina":
                                                huidige_header_boekpagina,
                                        })

                                    huidig_header_profiel = (
                                        profiel_nummer
                                    )
                                    huidig_header_niveau = header_niveau
                                    huidige_header_teksten = []
                                    huidige_header_boekpagina = boekpagina

                                    if tekst:
                                        huidige_header_teksten.append(
                                            tekst
                                        )

    # Sluit een eventuele laatste Header van het boek af
    if huidig_header_profiel is not None and huidige_header_teksten:
        boekstructuur.append({
            "type": "header",
            "niveau": huidig_header_niveau,
            "tekst": " ".join(huidige_header_teksten),
            "boekpagina": huidige_header_boekpagina,
        })

    document.close()

    # ========================================================
    # HINDENBURG-BRONBESTAND OPBOUWEN
    # ========================================================

    hindenburg_regels = ["<body>"]
    hix_teller = 1

    # Aanvullende Headers aan het begin van het boek
    for tekst in extra_headers_begin:

        hix_id = f"hix{hix_teller:05d}"

        regel = f'<h1 id="{hix_id}">{tekst}</h1>'

        hindenburg_regels.append(regel)
        hix_teller += 1

    # Gereconstrueerde boekstructuur toevoegen
    for element in boekstructuur:

        hix_id = f"hix{hix_teller:05d}"

        if element["type"] == "pagina":

            regel = (
                f'<span id="{hix_id}" '
                f'class="pagenum">{element["boekpagina"]}</span>'
            )

        elif element["type"] == "header":

            niveau = element["niveau"]
            tekst = element["tekst"]

            regel = (
                f'<h{niveau} id="{hix_id}">'
                f'{tekst}</h{niveau}>'
            )

        else:
            continue

        hindenburg_regels.append(regel)
        hix_teller += 1

    # Aanvullende Headers aan het einde van het boek
    for tekst in extra_headers_einde:

        hix_id = f"hix{hix_teller:05d}"

        regel = f'<h1 id="{hix_id}">{tekst}</h1>'

        hindenburg_regels.append(regel)
        hix_teller += 1

    hindenburg_regels.append("</body>")

    hindenburg_bronbestand = "\n".join(hindenburg_regels)

    # ========================================================
    # LOGBESTAND OPBOUWEN
    # ========================================================

    log_regels = [
        "LOGBESTAND PDF NAAR HINDENBURG",
        "=" * 60,
        "",
        "PDF",
        f"Bestandsnaam: {pdf_bestand.name}",
        f"Aantal fysieke PDF-pagina's: {aantal_pdf_paginas}",
        "",
        "BOEK",
        f"Titel: {Titel}",
        "",
        "PAGINERING",
        f"Eerste boekpagina: {start_boekpagina}",
        f"Eerste PDF-pagina: {start_fysieke_pagina}",
        f"Laatste PDF-pagina: {eind_fysieke_pagina}",
        (
            "Boekpagina's per PDF-pagina: "
            f"{boekpaginas_per_fysieke_pagina}"
        ),
    ]

    # Alleen toevoegen bij twee boekpagina's per PDF-pagina
    if boekpaginas_per_fysieke_pagina == 2:
        log_regels.extend([
            f"Positie eerste boekpagina: {start_deelpagina}",
            f"Positie laatste boekpagina: {eind_deelpagina}",
        ])

    # --------------------------------------------------------
    # HEADERPROFIELEN
    # --------------------------------------------------------

    log_regels.extend([
        "",
        "HEADERPROFIELEN",
    ])

    for header_niveau in range(1, 7):

        profielen = [
            profiel_nummer
            for profiel_nummer, niveau in header_profielen.items()
            if niveau == header_niveau
        ]

        if profielen:
            profielen.sort()

            profiel_tekst = ", ".join(
                str(profiel_nummer)
                for profiel_nummer in profielen
            )

            log_regels.append(
                f"Header {header_niveau}: "
                f"opmaakprofiel(en) {profiel_tekst}"
            )

    # --------------------------------------------------------
    # ALGEMENE OPMAAK BEGIN
    # --------------------------------------------------------

    log_regels.extend([
        "",
        "ALGEMENE OPMAAK BEGIN",
    ])

    for nummer, tekst in enumerate(
            extra_headers_begin,
            start=1
    ):
        log_regels.append(
            f"{nummer}. {tekst}"
        )

    # --------------------------------------------------------
    # ALGEMENE OPMAAK EINDE
    # --------------------------------------------------------

    log_regels.extend([
        "",
        "ALGEMENE OPMAAK EINDE",
    ])

    for nummer, tekst in enumerate(
            extra_headers_einde,
            start=1
    ):
        log_regels.append(
            f"{nummer}. {tekst}"
        )

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    aantal_paginamarkeringen = sum(
        1
        for element in boekstructuur
        if element["type"] == "pagina"
    )

    aantal_headers = sum(
        1
        for element in boekstructuur
        if element["type"] == "header"
    )

    log_regels.extend([
        "",
        "RESULTAAT",
        f"Aantal paginamarkeringen: {aantal_paginamarkeringen}",
        f"Aantal gevonden Headers: {aantal_headers}",
        (
            "Aantal gevonden opmaakprofielen: "
            f"{len(gesorteerde_profielen)}"
        ),
        "",
        "Verwerking voltooid.",
    ])

    # --------------------------------------------------------
    # LOGREGELS SAMENVOEGEN
    # --------------------------------------------------------

    logbestand = "\n".join(log_regels)

    st.success("PDF-verwerking voltooid.")

else:
    if pdf_bestand is None:
        st.info("Upload eerst een PDF-bestand.")
    else:
        st.warning(
            "De verwerking kan pas starten wanneer "
            "alle bovenstaande fouten zijn opgelost."
        )

# ============================================================
# OUTPUT
# ============================================================

st.header("Output")

if instellingen_geldig:

    st.download_button(
        label="Download Hindenburg-bronbestand",
        data=hindenburg_bronbestand,
        file_name="bronbestand.txt",
        mime="text/plain"
    )

    st.download_button(
        label="Download logbestand",
        data=logbestand,
        file_name="log.txt",
        mime="text/plain"
    )

else:
    st.info(
        "De uitvoerbestanden worden beschikbaar "
        "zodra alle instellingen geldig zijn."
    )