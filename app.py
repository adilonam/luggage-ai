import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Valise IA - Recherche de Similarité d'Images",
    page_icon="🧳",
    layout="wide"
)

# Welcome message
st.markdown("""
<div style="text-align: center; padding: 4rem 2rem;">
    <h1 style="color: #1f77b4; font-size: 4rem; margin-bottom: 2rem;">🧳 Luggage AI</h1>
    <p style="font-size: 1.5rem; color: #666; margin-bottom: 3rem;">
        Application de recherche de similarité d'images pour articles de bagage
    </p>
</div>
""", unsafe_allow_html=True)

# Center the button
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    if st.button("🚀 Commencer", type="primary", use_container_width=True):
        st.switch_page("pages/1_🏠_Accueil.py")

# Footer
st.markdown("""
<div style="text-align: center; color: #888; padding: 2rem;">
    <p>Développé avec ❤️ en utilisant Streamlit et CLIP</p>
</div>
""", unsafe_allow_html=True)
