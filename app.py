import streamlit as st
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com",
    page_icon="public/images/logo.ico",
    layout="wide"
)

# Meta description
components.html("""
<script>
(function() {
  var targetDoc = (window.parent && window.parent !== window) ? window.parent.document : document;
  if (!targetDoc.querySelector('meta[name="description"]')) {
    var meta = targetDoc.createElement('meta');
    meta.name = 'description';
    meta.content = 'Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français.';
    targetDoc.head.appendChild(meta);
  }
})();
</script>
""", height=0)

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
