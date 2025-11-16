#!/usr/bin/env python3
"""
Script to patch Streamlit index.html with SEO optimizations
"""
import os
import re

STREAMLIT_HTML = "/usr/local/lib/python3.12/site-packages/streamlit/static/index.html"

if not os.path.exists(STREAMLIT_HTML):
    print(f"File not found: {STREAMLIT_HTML}")
    exit(1)

# Read the file
with open(STREAMLIT_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

# Change lang attribute to French
content = re.sub(r'<html lang="en">', '<html lang="fr">', content)

# Update favicon link
content = re.sub(
    r'<link rel="shortcut icon" href="[^"]*" />',
    '<link rel="shortcut icon" href="public/images/logo.ico" />',
    content
)

# Replace title
content = re.sub(
    r'<title>Streamlit</title>',
    '<title>Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com</title>',
    content
)

# Add SEO meta tags after the title
seo_meta_tags = '''  <meta name="description" content="Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français." />
  <meta name="keywords" content="roulettes valise, pièces valise, reconnaissance IA, intelligence artificielle, identification valise, roulettesdevalise" />
  <meta name="author" content="Roulettesdevalise.com" />
  <meta name="robots" content="index, follow" />
  
  <!-- Open Graph / Facebook -->
  <meta property="og:type" content="website" />
  <meta property="og:title" content="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com" />
  <meta property="og:description" content="Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français." />
  <meta property="og:url" content="https://www.roulettesdevalise.com" />
  <meta property="og:site_name" content="Roulettesdevalise.com" />
  
  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="Reconnaissance IA de Roulettes & Pièces Valises – Roulettesdevalise.com" />
  <meta name="twitter:description" content="Trouvez la bonne roulette, poignée ou serrure pour votre valise grâce à notre IA. Service rapide, gratuit et 100 % français." />
  
  <!-- Canonical URL -->
  <link rel="canonical" href="https://www.roulettesdevalise.com" />'''

# Insert SEO tags after title
content = re.sub(
    r'(<title>.*?</title>)',
    r'\1\n' + seo_meta_tags,
    content,
    flags=re.DOTALL
)

# Remove noscript tag
content = re.sub(
    r'<noscript>You need to enable JavaScript to run this app\.</noscript>\s*',
    '',
    content
)

# Add Google Tag Manager before closing </head>
google_analytics = '''  <!-- Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-CMC9LG22K4"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-CMC9LG22K4');
  </script>'''

# Insert Google Analytics before closing </head> tag
content = re.sub(
    r'(</head>)',
    google_analytics + r'\n\1',
    content,
    flags=re.DOTALL
)

# Write the file back
with open(STREAMLIT_HTML, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Successfully patched {STREAMLIT_HTML}")

