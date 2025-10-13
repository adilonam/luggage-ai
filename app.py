import streamlit as st

# Page configuration to hide from sidebar
st.set_page_config(
    page_title="🔧 Vous ne savez pas quelle roulette, cadenas, poignée correspond à votre valise ?",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Redirect directly to Accueil page
st.switch_page("pages/1_🏠_Accueil.py")
