import streamlit as st
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com",
    page_icon="public/images/logo.ico",
    layout="wide"
)

# Add custom meta tags (SEO + OpenGraph)
st.markdown("""
<head>
    <meta name="description" content="Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français.">
    <meta property="og:title" content="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com">
    <meta property="og:description" content="Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français.">
    <meta property="og:url" content="https://www.roulettesdevalise.com">
    <meta property="og:image" content="https://www.roulettesdevalise.com/static/preview.jpg">
    <meta name="robots" content="index, follow">
</head>
""", unsafe_allow_html=True)

# Google Analytics
components.html("""
<script async src="https://www.googletagmanager.com/gtag/js?id=G-CMC9LG22K4"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-CMC9LG22K4');
</script>
""", height=0)

# Redirect directly to Accueil page
st.switch_page("pages/1_🏠_Accueil.py")
