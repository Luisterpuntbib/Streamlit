# Streamlit Luisterpunt

Via een Streamlit-app kan de IT-afdeling gemakkelijk losse scripts delen met collega's van andere afdelingen. Het gaat om scripts die op onregelmatige basis door de collega's zelf worden uitgevoerd en waarbij ze liever geen command line gebruiken.

## De Streamlit-app bevat de volgende scripts

- ✉️ Bpost-etiketten: een script voor Com&Prom om automatisch adresgegevens vanuit formulieren op de website om te zetten naar etiketten in een formaat dat Bpost accepteert.
- ⠃ Braille conversie: verwerking van bronfolders met XML + BRL naar BRF-output op basis van Excel-mapping en een vaste `.cnv` conversietabel.

## Braillefunctionaliteit

### Doel

De brailleflow verwerkt één input-ZIP met meerdere bronfolders. Per bronfolder wordt:
- de Lois ID gevalideerd en gematcht met Excel,
- XML ongewijzigd gekopieerd (alleen bestandsnaam wijzigt),
- elk `.brl`-bestand geconverteerd naar `.brf`,
- een outputfolder opgebouwd.

Bij fouten wordt nog steeds een outputfolder aangemaakt met `error_report.txt`.

### Verwachte input ZIP-structuur

```text
input.zip
  374170_1_1/
    meta374170.xml
    p374170_001.brl
    p374170_002.brl
  380532_1_1/
    meta380532.xml
    p380532_001.brl
```

Regels per bronfolder:
- exact 1 XML-bestand
- 1 of meer `.brl`-bestanden
- `.brl`-bestandsnamen volgen patroon `*_NNN.brl`

### Excel-kolommen

- Kolom B = titel
- Kolom C = Lois ID
- Kolom E = doel boeknummer

Lois ID wordt genormaliseerd voor matching (trim, lowercase, optionele `t`-prefix weg, daarna numerieke waarde).

### Outputnaamgeving

Voor een gematchte rij:
- `title_slug`: titel met spaties als underscores
- outputfolder: `{boeknummer}_{title_slug}`
- XML-bestandsnaam: `{boeknummer}_meta_{title_slug}.xml`
- BRF-bestandsnaam: `{boeknummer}_{volume}_{title_slug}.brf`

Voorbeeld:
- bron: `p380532_002.brl`
- titel: `Aan mij heb je niks`
- boeknummer: `63773`
- output: `63773_002_Aan_mij_heb_je_niks.brf`

### Lokaal testen

Eén bronfolder:

```bash
python scripts/manual_test_one_folder.py \
  --source-folder C:\path\to\source_folder \
  --excel-file C:\path\to\ECB.xlsx \
  --cnv-file C:\path\to\brl2brf.cnv \
  --output-root C:\path\to\test_output
```

Volledige ZIP-pipeline:

```bash
python scripts/manual_test_zip_pipeline.py \
  --input-zip C:\path\to\input.zip \
  --excel-file C:\path\to\ECB.xlsx \
  --cnv-file C:\path\to\brl2brf.cnv \
  --output-zip C:\path\to\result.zip
```

### Streamlit gebruik

Start de app via:

```bash
streamlit run .\main_page.py
```

Navigeer na login naar:
- `Braille Conversie` in de zijbalk of op de inhoudspagina.

De pagina `pages/04_Braille_Conversie.py` vraagt:
- input-ZIP upload
- Excel upload

Conversietabel is vast ingesteld op `brl2brf.cnv` in de projectroot.
