import csv, os
import pandas as pd
import numpy as np
import time

import streamlit as st

# titel op pagina en in menu instellen
st.markdown("# Bpost Etiketten ")
st.sidebar.markdown("# Bpost Etiketten ")

# uploadknop en uploaden csv instellen
uploaded_file = st.file_uploader("Kies hieronder de Formie-export uit je eigen bestanden:")
if uploaded_file is not None:
	# Can be used wherever a "file-like" object is accepted:
   st.write('Input-bestand:')
   in_csv = pd.read_csv(uploaded_file, sep=';') #sep checken voor huidige input
   in_csv.index += 1
   st.write(in_csv.style.format())

# binnen de functie convert_df wordt het csv-bestand aangepast naar de gewenste indeling
@st.cache_data
def convert_df(in_csv):
	# kolomnamen waarvan de input variabel is opgelijst naar format van output csv 
	headers_in = np.full(shape=44, fill_value=np.nan, dtype=object)

	# waarden aanpassen van kolommen
	headers_in[1] = 'Organisatie'
	headers_in[4] = 'Straat'
	headers_in[5] = 'Nummer'
	headers_in[6] = 'Bus'
	headers_in[7] = 'Postcode'
	headers_in[8] = 'Gemeente'

	# in plaats van een model-csv van bpost heb ik hier een lijst met de headers uit het model-csv
	# zo hoeft het model-csv niet in dezelfde map te staan als dit script
	headers_out = ['ProductId', 'Name', 'Contact Name', 'Contact Phone', 'Street', 'Street Number', 'Box Number', 'Postal Code', 'City', 'Country', 'Sender Name', 'Sender Contact Name', 'Sender Street', 'Sender Street Number', 'Sender Box Number', 'Sender Postal Code', 'Sender City', 'Weight', 'Customer Reference', 'Cost Center', 'Free Message', 'COD Amount', 'COD Account', 'Signature', 'Insurance', 'Automatic Second Presentation', 'Info Reminder', 'Info Reminder Language', 'Info Reminder Type', 'Info Reminder Contact Data', 'Info Next Day', 'Info Next Day Language', 'Info Next Day Type', 'Info Next Day Contact Data', 'Info Distributed', 'Info Distributed Language', 'Info Distributed Type', 'Info Distributed Contact Data', 'Saturday Delivery', 'Delivery point id', 'Delivery point message language', 'Delivery point mobile phone', 'Delivery point email', 'Parcel locker reduced mobility zone']

	# leeg dataframe met headers uit model-csv maken
	out_csv = pd.DataFrame(columns=headers_out)

	# headers uit output-csv en input-csv samenvoegen in dict
	headers_dict = dict(zip(headers_out, headers_in))
	# selecteer alleen de headers die zijn ingevuld in in_csv ('not na')
	column_mapping = {k: v for k, v in headers_dict.items() if pd.Series(v).notna().all()}

	# selectie van kolommen obv dictionary
	# kopieer vervolgens de waarden van geselecteerde kolommen van in_csv naar out_csv
	for column_out_csv, column_in_csv in column_mapping.items():
	    out_csv[column_out_csv] = in_csv[column_in_csv]

	# foutje voorkomen waarbij postbusnummers floats worden
	if out_csv['Box Number'].dtype == 'float':
		out_csv['Box Number'] = out_csv['Box Number'].astype('Int64')
	# kolommen voor- en achternaam in input-csv combineren in output-csv (fillna om lege velden te ondervangen)
	out_csv["Contact Name"] = in_csv["Naam: First Name"].fillna('') + ' ' + in_csv["Naam: Last Name"].fillna('')

	# dict met standaardinfo over LP en verzending (bv of van de ontvanger een handtekening wordt vereist)
	info_LP = {'ProductId': 'BPACK24h', 'Country': 'BE', 'Sender Name': 'Luisterpuntbibliotheek vzw',
	           'Sender Street': 'Broekstraat', 'Sender Street Number': '49-53', 'Sender Postal Code': 1000,
	           'Sender City': 'Brussel', 'Signature': 'N', 'Insurance': 'N', 'Automatic Second Presentation': 
	           'N', 'Info Reminder': 'N', 'Info Next Day': 'N', 'Info Distributed': 'N', 'Saturday Delivery': 'N'}

	# dict invoegen in out_csv
	for kolom, waarde in info_LP.items():
	    out_csv[kolom] = waarde
	    
	return out_csv

# voorvertoning output_csv weergeven
if uploaded_file is not None:
	out_csv = convert_df(in_csv)
	st.write('Output-bestand:')
	st.write(out_csv.style.format())

# download-knop voor aangepaste csv instellen
if uploaded_file is not None:
	out_csv = out_csv.to_csv(sep=';', index=False, encoding='utf-8')
	# Bestandsnaam voor output in een variabele vastleggen
	bestandsnaam_output = 'bpost_labels_' + time.strftime("%Y%m%d") + '.csv'
	# download-button-functie invullen
	st.download_button(
		label="Download data as CSV",
		data=out_csv,
	   file_name=bestandsnaam_output,
	   mime="text/csv",
	)
