from navigation import make_sidebar
import streamlit as st

make_sidebar()
st.markdown("# 🏠 Inhoud")

if st.session_state.get("logged_in", False):
    # st.page_link("pages/01_inhoud.py", label="Inhoud", icon="🏠")
    st.write("")
    st.page_link("pages/02_Bpost_Etiketten.py", label="Bpost Etiketten", icon="✉️")
    # st.write("")
    st.page_link("pages/page_3.py", label="Pagina 3", icon="🧙")
    st.write("")