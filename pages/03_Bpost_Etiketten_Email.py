import csv, os
import pandas as pd
import numpy as np
import time

from bpost_conversion import build_contact_names, read_formie_csv
from navigation import make_sidebar
import streamlit as st

make_sidebar()

# titel op pagina en in menu instellen
st.markdown("# ✉️ Bpost Etiketten (met e-mail)")

# uploadknop en uploaden csv instellen — IDENTIEK AAN ORIGINEEL
uploaded_file = st.file_uploader("Kies hieronder de Formie-export uit je eigen bestanden:")
if uploaded_file is not None:
    st.write('Input-bestand:')
    in_csv = read_formie_csv(uploaded_file)
    in_csv.index += 1                              # <== zelfde als orig.
    st.write(in_csv.style.format())

@st.cache_data
def convert_df(in_csv: pd.DataFrame) -> pd.DataFrame:
    # kolomnamen waarvan de input variabel is opgelijst naar format van output csv — IDENTIEK
    headers_in = np.full(shape=44, fill_value=np.nan, dtype=object)

    # waarden aanpassen van kolommen — IDENTIEK
    headers_in[1] = 'Organisatie'
    headers_in[4] = 'Straat'
    headers_in[5] = 'Nummer'
    headers_in[6] = 'Bus'
    headers_in[7] = 'Postcode'
    headers_in[8] = 'Gemeente'

    # lijst met headers uit bpost-model — IDENTIEK
    headers_out = [
        'ProductId','Name','Contact Name','Contact Phone','Street','Street Number','Box Number','Postal Code','City','Country',
        'Sender Name','Sender Contact Name','Sender Street','Sender Street Number','Sender Box Number','Sender Postal Code','Sender City',
        'Weight','Customer Reference','Cost Center','Free Message','COD Amount','COD Account','Signature','Insurance',
        'Automatic Second Presentation','Info Reminder','Info Reminder Language','Info Reminder Type','Info Reminder Contact Data',
        'Info Next Day','Info Next Day Language','Info Next Day Type','Info Next Day Contact Data',
        'Info Distributed','Info Distributed Language','Info Distributed Type','Info Distributed Contact Data',
        'Saturday Delivery','Delivery point id','Delivery point message language','Delivery point mobile phone','Delivery point email',
        'Parcel locker reduced mobility zone'
    ]

    # leeg dataframe met headers uit model-csv — IDENTIEK
    out_csv = pd.DataFrame(columns=headers_out)

    # headers uit output-csv en input-csv samenvoegen — IDENTIEK
    headers_dict = dict(zip(headers_out, headers_in))
    column_mapping = {k: v for k, v in headers_dict.items() if pd.Series(v).notna().all()}

    # kolommen kopiëren — IDENTIEK
    for column_out_csv, column_in_csv in column_mapping.items():
        out_csv[column_out_csv] = in_csv[column_in_csv]

    # postbus-nummer als integer indien nodig — IDENTIEK aan originele streamlit-versie (met typecheck)
    if 'Box Number' in out_csv.columns and out_csv['Box Number'].dtype == 'float':
        out_csv['Box Number'] = out_csv['Box Number'].astype('Int64')

    # Ondersteun de huidige Nederlandse en de vroegere Engelse Formie-headers.
    out_csv["Contact Name"] = build_contact_names(in_csv)

    # standaardinfo verzending — IDENTIEK
    info_LP = {
        'ProductId': 'BPACK24h', 'Country': 'BE', 'Sender Name': 'Luisterpuntbibliotheek vzw',
        'Sender Street': 'Broekstraat', 'Sender Street Number': '49-53', 'Sender Postal Code': 1000,
        'Sender City': 'Brussel', 'Signature': 'N', 'Insurance': 'N',
        'Automatic Second Presentation': 'N', 'Info Reminder': 'N',
        'Info Next Day': 'N', 'Info Distributed': 'N', 'Saturday Delivery': 'N'
    }
    for kolom, waarde in info_LP.items():
        out_csv[kolom] = waarde

    # ========= ENIGE TOEVOEGING 1: e-mailadres naar Bpost-kolom =========
    # Verwacht Formie-kolomnaam: 'E-mailadres' (pas aan indien uw Formie anders labelt)
    if 'E-mailadres' in in_csv.columns:
        out_csv['Receiver email address'] = in_csv['E-mailadres'].fillna('').astype(str).str.strip()
    else:
        # Als de kolom anders heet, blijft deze leeg; zie kolomnamen bovenaan de pagina
        out_csv['Receiver email address'] = ""

    return out_csv

# voorvertoning output — IDENTIEK
if uploaded_file is not None:
    out_csv = convert_df(in_csv)
    st.write('Output-bestand:')
    st.write(out_csv.style.format())

# download-knop — IDENTIEK, alleen bestandsnaam anders (toevoeging “_email_”)
if uploaded_file is not None:
    csv_bytes = out_csv.to_csv(sep=';', index=False).encode("utf-8")  # UTF-8 zonder BOM
    # ========= ENIGE TOEVOEGING 2: onderscheidende bestandsnaam =========
    bestandsnaam_output = 'bpost_labels_email_' + time.strftime("%Y%m%d") + '.csv'
    st.download_button(
        label="Download data as CSV",
        data=csv_bytes,
        file_name=bestandsnaam_output,
        mime="text/csv",
    )
