# streamlit run .\main_page.py

import streamlit as st
from time import sleep
from navigation import make_sidebar

make_sidebar()

st.title("Luisterpunt")

st.write("Log in om de scripts van Luisterpunt te gebruiken.")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == st.secrets["username"] and password == st.secrets["password"]:
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/01_inhoud.py")
    else:
        st.error("Incorrect username or password")
