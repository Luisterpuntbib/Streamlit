import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages


def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")

    return pages[ctx.page_script_hash]["page_name"]

def make_sidebar():
    with st.sidebar:
        st.title("Luisterpunt")
        st.write("")
        st.write("")

        if st.session_state.get("logged_in", False):
            st.page_link("pages/01_inhoud.py", label="Inhoud", icon="🏠")
            st.page_link("pages/02_Bpost_Etiketten.py", label="Bpost Etiketten", icon="✉️")
            st.page_link("pages/page_3.py", label="Pagina 3", icon="🧙")

            st.write("")
            st.write("")

            if st.button("Log out"):
                logout()

        elif get_current_page_name() != "main_page":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("main_page.py")


def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("main_page.py")