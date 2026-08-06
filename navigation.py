import streamlit as st
from time import sleep

def make_sidebar():
    st.markdown(
        """
        <style>
            @media (min-width: 769px) {
                section[data-testid="stSidebar"],
                section[data-testid="stSidebar"] > div {
                    width: 360px !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.title("Luisterpunt")

        if st.session_state.get("logged_in", False):
            # Links in de zijbalk:
            #st.sidebar.page_link("pages/01_inhoud.py", label="Inhoud", icon="🏠")
           # st.sidebar.page_link("pages/02_Bpost_Etiketten.py", label="Bpost Etiketten", icon="✉️")
            st.sidebar.page_link("pages/03_Bpost_Etiketten_Email.py", label="Bpost Etiketten (met e-mail)", icon="📧")
            #st.sidebar.page_link("pages/page_3.py", label="Pagina 3", icon="🧙")

            st.write("")
            if st.button("Log out"):
                logout()
        else:
            # Niet ingelogd: geen links tonen (login gebeurt via main_page.py)
            pass

def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("main_page.py")
