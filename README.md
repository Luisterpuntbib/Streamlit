# Streamlit Luisterpunt

Via deze Streamlit-app kan de IT-afdeling losse conversiescripts beschikbaar maken voor collega's.

## Functionaliteiten

- Bpost-etiketten: zet adresgegevens uit webformulieren om naar het Bpost-formaat.
- Brailleconversie: verwerkt XML- en BRL-bronbestanden naar hernoemde XML- en BRF-output.

## Brailleconversie zonder Excel

De Brailleflow leest alle benodigde metadata uit de input zelf:

- Belgisch boeknummer: uit de naam van de bronfolder.
- Lois ID: uit het expliciete XML-veld `lois_id`.
- Titel: uit het expliciete XML-veld `title`.

Excel is niet nodig. De XML-inhoud wordt exact en ongewijzigd gekopieerd; alleen de XML-bestandsnaam verandert.

### Input-ZIP

De ZIP bevat één of meerdere bronfolders op het hoogste niveau:

```text
input.zip
  65856/
    meta378393.xml
    p378393_001.brl
    p378393_002.brl
  66000/
    meta379230.xml
    p379230_001.brl
```

Per bronfolder gelden deze regels:

- de foldernaam bevat het Belgische boeknummer;
- exact één XML-bestand;
- één of meer `.brl`-bestanden;
- iedere BRL-naam eindigt op `_NNN.brl`;
- XML- en BRL-bestandsnamen bevatten dezelfde Lois ID;
- de XML bevat precies bruikbare `lois_id`- en `title`-velden;
- de Lois ID uit XML komt overeen met de bestandsnamen.

Een titel mag cijfers bevatten. Alleen het expliciete `lois_id`-veld wordt als Lois ID geïnterpreteerd.

### Outputnamen

- titel-slug: spaties in de titel worden underscores;
- outputfolder: `{boeknummer}_{titel_slug}`;
- XML: `{boeknummer}_meta_{titel_slug}.xml`;
- BRF: `{boeknummer}_{volume}_{titel_slug}.brf`.

Voorbeeld:

```text
65856_De_Zoete_Zusjes_gaan_op_avontuur/
  65856_meta_De_Zoete_Zusjes_gaan_op_avontuur.xml
  65856_001_De_Zoete_Zusjes_gaan_op_avontuur.brf
```

Bij een fout wordt voor het betreffende boek toch een outputfolder gemaakt met `error_report.txt`.

### Lokaal testen

```powershell
python scripts/manual_test_zip_pipeline.py `
  --input-zip C:\path\to\input.zip `
  --cnv-file C:\path\to\brl2brf.cnv `
  --output-zip C:\path\to\result.zip
```

Een losse bronfolder testen:

```powershell
python scripts/manual_test_one_folder.py `
  --source-folder C:\path\to\65856 `
  --cnv-file C:\path\to\brl2brf.cnv `
  --output-root C:\path\to\output
```

### Streamlit

```powershell
streamlit run .\main_page.py
```

Open na het aanmelden `Braille Conversie Dedicon Luisterpunt`. Upload uitsluitend de input-ZIP en klik op `Verwerken`. De conversietabel `brl2brf.cnv` wordt uit de projectroot gebruikt.
