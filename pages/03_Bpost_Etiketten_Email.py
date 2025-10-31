import pandas as pd
import numpy as np
import time

from navigation import make_sidebar
import streamlit as st

make_sidebar()

# Titel
st.markdown("# 📧 Bpost Etiketten (met e-mail)")

# --- Upload: Formie-export ---
uploaded_file = st.file_uploader(
    "Kies hieronder de Formie-export uit je eigen bestanden (met kolom ‘E-mailadres’):"
)

def _lees_in_csv(uploaded):
    """Robuust inlezen: probeer ; en , zoals in de bestaande app/logica."""
    if uploaded is None:
        return None
    for sep in [';', ',']:
        try:
            df = pd.read_csv(uploaded, sep=sep, encoding='utf-8-sig')
            return df
        except Exception:
            uploaded.seek(0)  # reset file pointer voor herlees
            continue
    uploaded.seek(0)
    return pd.read_csv(uploaded)  # laatste poging

if uploaded_file is not None:
    st.write("Input-bestand:")
    in_csv = _lees_in_csv(uploaded_file)
    in_csv.index += 1
    st.write(in_csv.style.format())

@st.cache_data
def convert_df_with_email(in_csv: pd.DataFrame) -> pd.DataFrame:
    """
    Converteert Formie-export naar Bpost Shipping Manager CSV.
    Minimale wijziging t.o.v. de originele pagina:
    - 'Receiver email address' vullen vanuit Formie-kolom 'E-mailadres'
    - UTF-8 zonder BOM bij download (gebeurt buiten deze functie)
    Overig gedrag identiek.
    """

    # 1) headers_in + mapping zoals origineel
    headers_in = np.full(shape=44, fill_value=np.nan, dtype=object)
    headers_in[1] = 'Organisatie'
    headers_in[4] = 'Straat'
    headers_in[5] = 'Nummer'
    headers_in[6] = 'Bus'
    headers_in[7] = 'Postcode'
    headers_in[8] = 'Gemeente'

    # 2) headers_out zoals origineel, + 'Receiver email address' voor Shipping Manager V5
    headers_out = [
        'ProductId', 'Name', 'Contact Name', 'Contact Phone', 'Street',
        'Street Number', 'Box Number', 'Postal Code', 'City', 'Country',
        'Sender Name', 'Sender Contact Name', 'Sender Street',
        'Sender Street Number', 'Sender Box Number', 'Sender Postal Code',
        'Sender City', 'Weight', 'Customer Reference', 'Cost Center',
        'Free Message', 'COD Amount', 'COD Account', 'Signature', 'Insurance',
        'Automatic Second Presentation', 'Info Reminder', 'Info Reminder Language',
        'Info Reminder Type', 'Info Reminder Contact Data', 'Info Next Day',
        'Info Next Day Language', 'Info Next Day Type', 'Info Next Day Contact Data',
        'Info Distributed', 'Info Distributed Language', 'Info Distributed Type',
        'Info Distributed Contact Data', 'Saturday Delivery', 'Delivery point id',
        'Delivery point message language', 'Delivery point mobile phone',
        # Toegevoegd veld voor Shipping Manager V5:
        'Receiver email address',
        'Parcel locker reduced mobility zone'
    ]

    out_csv = pd.DataFrame(columns=headers_out)

    headers_dict = dict(zip(headers_out, headers_in))
    column_mapping = {k: v for k, v in headers_dict.items() if pd.Series(v).notna().all()}

    for column_out_csv, column_in_csv in column_mapping.items():
        if column_in_csv in in_csv.columns:
            out_csv[column_out_csv] = in_csv[column_in_csv]

    # 3) Datatypes/naamvelden (conform bestaande app)
    if 'Box Number' in out_csv.columns and str(out_csv['Box Number'].dtype) == 'float64':
        out_csv['Box Number'] = out_csv['Box Number'].astype('Int64')

    # In de bestaande Streamlit-pagina werd 'Contact Name' gevuld, 'Name' blijft organisatie
    if 'Contact Name' in out_csv.columns:
        fn, ln = 'Naam: First Name', 'Naam: Last Name'
        if fn in in_csv.columns and ln in in_csv.columns:
            out_csv['Contact Name'] = (in_csv[fn].fillna('') + ' ' + in_csv[ln].fillna('')).str.strip()

    # 4) Ontvanger e-mail: Shipping Manager kolom 'Receiver email address'
    if 'Receiver email address' in out_csv.columns:
        out_csv['Receiver email address'] = in_csv['E-mailadres'] if 'E-mailadres' in in_csv.columns else ''

    # 5) Standaard verzender + opties (ongewijzigd)
    info_LP = {
        'ProductId': 'BPACK24h', 'Country': 'BE',
        'Sender Name': 'Luisterpuntbibliotheek vzw',
        'Sender Street': 'Broekstraat', 'Sender Street Number': '49-53',
        'Sender Postal Code': 1000, 'Sender City': 'Brussel',
        'Signature': 'N', 'Insurance': 'N',
        'Automatic Second Presentation': 'N',
        'Info Reminder': 'N', 'Info Next Day': 'N',
        'Info Distributed': 'N',           # verzendermelding uit
        'Saturday Delivery': 'N'
    }
    for kolom, waarde in info_LP.items():
        if kolom in out_csv.columns:
            out_csv[kolom] = waarde

    return out_csv

# --- Voorvertoning + download ---
if uploaded_file is not None:
    out_csv = convert_df_with_email(in_csv)
    st.write("Output-bestand (voorbeeld):")
    st.write(out_csv.style.format())

    csv_bytes = out_csv.to_csv(sep=';', index=False, encoding='utf-8', lineterminator='\n').encode('utf-8')
    bestandsnaam_output = 'bpost_labels_email_' + time.strftime('%Y%m%d') + '.csv'

    st.download_button(
        label="Download CSV (met e-mail)",
        data=csv_bytes,
        file_name=bestandsnaam_output,
        mime="text/csv"
    )
