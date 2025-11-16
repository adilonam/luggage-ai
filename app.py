import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com",
    page_icon="public/images/favicon.ico",
    layout="wide"
)

# Redirect directly to Accueil page
st.switch_page("pages/1_Accueil.py")
