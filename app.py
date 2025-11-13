import streamlit as st
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com",
    page_icon="public/images/logo.ico",
    layout="wide"
)

# Add custom meta tags (SEO + OpenGraph)
components.html("""
<script>
(function() {
  var targetDoc = (window.parent && window.parent !== window) ? window.parent.document : document;
  
  function setOrUpdateMeta(name, content, isProperty) {
    var selector = isProperty ? 'meta[property="' + name + '"]' : 'meta[name="' + name + '"]';
    var meta = targetDoc.querySelector(selector);
    if (meta) {
      meta.setAttribute('content', content);
    } else {
      meta = targetDoc.createElement('meta');
      if (isProperty) {
        meta.setAttribute('property', name);
      } else {
        meta.setAttribute('name', name);
      }
      meta.setAttribute('content', content);
      targetDoc.head.appendChild(meta);
    }
  }
  
  // Set meta description
  setOrUpdateMeta('description', 'Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français.', false);
  
  // Set Open Graph tags
  setOrUpdateMeta('og:title', 'Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com', true);
  setOrUpdateMeta('og:description', 'Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français.', true);
  setOrUpdateMeta('og:url', 'https://www.roulettesdevalise.com', true);
  setOrUpdateMeta('og:image', 'https://www.roulettesdevalise.com/static/preview.jpg', true);
  
  // Set robots meta tag
  setOrUpdateMeta('robots', 'index, follow', false);
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
