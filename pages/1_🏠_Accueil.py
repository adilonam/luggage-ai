import json
import os

import clip
import faiss
import numpy as np
import streamlit as st
import torch
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="🔧 Vous ne savez pas quelle roulette, cadenas, poignée correspond à votre valise ?",
    page_icon="🔧",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .similarity-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #1f77b4;
    }
    .metadata {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2e8b57;
    }
    .article-id {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
    /* Responsive design for mobile devices */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem !important;
            margin-bottom: 1rem !important;
        }
    }
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem !important;
            margin-bottom: 0.8rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load CLIP model and return model, preprocess function, and device"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device


def load_metadata():
    """Load metadata from JSON file"""
    metadata_path = "dataset/metadata.json"
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erreur lors du chargement du metadata: {str(e)}")
            return []
    return []


def get_article_urls(article_id):
    """Get URLs for a specific article from metadata"""
    metadata = load_metadata()
    for entry in metadata:
        if entry["label"] == article_id:
            return entry.get("url-roulette", "Non trouvé"), entry.get("url-kit", "Non trouvé")
    return "Non trouvé", "Non trouvé"


def get_dataset_folders():
    """Get list of folders in dataset directory"""
    dataset_path = "dataset/"
    if not os.path.exists(dataset_path):
        return []
    return [f for f in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, f))]


@st.cache_data
def build_faiss_index():
    """Build FAISS index from dataset images"""
    model, preprocess, device = load_model()

    embeddings = []
    ids = []

    dataset_path = "dataset/"
    if not os.path.exists(dataset_path):
        st.error(f"Chemin du dataset '{dataset_path}' introuvable!")
        return None, None

    progress_bar = st.progress(0)
    status_text = st.empty()

    folders = get_dataset_folders()
    total_folders = len(folders)

    for idx, id_article in enumerate(folders):
        folder = os.path.join(dataset_path, id_article)
        status_text.text(f"Traitement du dossier: {id_article}")

        for file in os.listdir(folder):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                try:
                    image_path = os.path.join(folder, file)
                    image = preprocess(Image.open(image_path)
                                       ).unsqueeze(0).to(device)
                    with torch.no_grad():
                        emb = model.encode_image(image).cpu().numpy()
                    embeddings.append(emb)
                    ids.append(id_article)
                except Exception as e:
                    st.warning(
                        f"Erreur lors du traitement de {image_path}: {str(e)}")

        progress_bar.progress((idx + 1) / total_folders)

    if not embeddings:
        st.error("Aucune image valide trouvée dans le dataset!")
        return None, None

    embeddings = np.vstack(embeddings).astype("float32")

    # Build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)  # type: ignore

    status_text.text("Index construit avec succès!")
    progress_bar.empty()
    status_text.empty()

    return index, ids


def main():
    # Header
    st.markdown('<h1 class="main-header">🔧 Vous ne savez pas quelle roulette, cadenas, poignée correspond à votre valise ?</h1>',
                unsafe_allow_html=True)

    # Description
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .description-box {
            font-size: 1rem !important;
            padding: 1rem !important;
            margin: 1rem 0 !important;
        }
    }
    @media (max-width: 480px) {
        .description-box {
            font-size: 0.9rem !important;
            padding: 0.8rem !important;
        }
    }
    </style>
    <div class="description-box" style="text-align: center; font-size: 1.2rem; color: #2e8b57; margin: 2rem 0; padding: 1.5rem; background-color: #f0f8f0; border-radius: 10px; border-left: 5px solid #2e8b57;">
        <strong>Télécharger une photo : notre IA s'occupe du reste !</strong><br><br>
        En quelques secondes, vous obtiendrez les modèles compatibles ou les kits de Réparations à commander sur notre site <strong><a href="https://jereparemonbagage.com" target="_blank" style="color: #1f77b4; text-decoration: none;">Jereparemonbagage.com</a></strong><br><br>
        <em>Réparer sa valise au lieu de la jeter, c'est possible !</em>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Sidebar for controls
    with st.sidebar:
        st.header("Paramètres")
        num_results = st.slider("Nombre de résultats similaires", 1, 10, 3)
        st.markdown("---")

        # Rebuild index button
        st.markdown("### 🔧 Maintenance")
        if st.button("🔄 Reconstruire l'Index", type="secondary", use_container_width=True):
            # Clear all cached data
            if 'index' in st.session_state:
                del st.session_state.index
            if 'ids' in st.session_state:
                del st.session_state.ids

            # Clear the cached build_faiss_index function
            build_faiss_index.clear()

            st.success(
                "✅ Cache vidé. L'index sera reconstruit automatiquement.")
            st.rerun()

        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown(
            "1. Téléchargez une image en utilisant le sélecteur de fichiers")
        st.markdown(
            "2. L'application trouvera les articles de bagage les plus similaires")
        st.markdown("3. Les résultats sont classés par score de similarité")
        st.markdown(
            "4. Utilisez 'Reconstruire l'Index' après avoir modifié le dataset")

    # Initialize session state - only build index if not already cached
    if 'index' not in st.session_state or 'ids' not in st.session_state:
        st.info(
            "🔄 Construction de l'index de similarité à partir du dataset... Cela peut prendre un moment.")
        with st.spinner("Chargement du modèle et construction de l'index..."):
            index, ids = build_faiss_index()
            if index is not None:
                st.session_state.index = index
                st.session_state.ids = ids
                st.success("✅ Index construit avec succès!")
            else:
                st.error(
                    "❌ Échec de la construction de l'index. Veuillez vérifier votre dataset.")
                return

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📸 Télécharger une Image")

        uploaded_file = st.file_uploader(
            "Choisir un fichier image",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            help="Téléchargez une image pour trouver des articles de bagage similaires"
        )

        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Image téléchargée",
                     use_container_width=True)
        # Instructions for taking good photos
        st.warning("""
        **📷 Comment prendre une bonne photo :**
        
        • Placez l'article sur un **fond uni** (blanc, gris ou coloré)
        • Assurez-vous que l'article est **bien éclairé**
        • Prenez la photo de **face** et de **profil**
        • L'article doit être **net et visible** dans l'image
        • Évitez les reflets et les ombres importantes
        """)

        # Button to show/hide example
        if st.button("📋 Voir un exemple de bonne photo", type="secondary", use_container_width=True):
            st.session_state.show_example = not st.session_state.get(
                'show_example', False)

        # Show example image if button was clicked
        if st.session_state.get('show_example', False):
            try:
                example_image = Image.open("sample/good.jpg")
                st.image(
                    example_image, caption="Exemple de bonne photo - Article sur fond uni", use_container_width=True)
                st.info(
                    "💡 Cette photo montre un bon exemple : article bien visible sur fond uni, éclairage correct.")
            except FileNotFoundError:
                st.warning("⚠️ Fichier d'exemple non trouvé.")

    with col2:
        st.header("🔍 Résultats de Recherche")

        if uploaded_file is not None:
            if st.button("🔍 Trouver des Articles Similaires", type="primary"):
                with st.spinner("Analyse de l'image et recherche d'articles similaires..."):
                    # Load model
                    model, preprocess, device = load_model()

                    # Process uploaded image
                    try:
                        # Convert uploaded file to PIL Image and preprocess
                        query_img = preprocess(image).unsqueeze(0).to(device)

                        # Encode image
                        with torch.no_grad():
                            q_emb = model.encode_image(query_img).cpu().numpy()

                        # Search for similar images - Get more results to ensure we get unique article IDs
                        # Search more results
                        search_k = min(50, len(st.session_state.ids))
                        # FAISS search returns distances and indices
                        D, I = st.session_state.index.search(
                            q_emb.astype('float32'), search_k)  # type: ignore

                        # Get unique article IDs with their best scores
                        unique_results = {}
                        for i in range(search_k):
                            article_id = st.session_state.ids[I[0][i]]
                            distance = D[0][i]

                            # Keep only the best (lowest distance) for each article ID
                            if article_id not in unique_results or distance < unique_results[article_id]['distance']:
                                unique_results[article_id] = {
                                    'distance': distance,
                                    'index': i
                                }

                        # Sort by distance (lower is better) and take top results
                        sorted_results = sorted(unique_results.items(
                        ), key=lambda x: x[1]['distance'])[:num_results]

                        # Display results
                        st.markdown("### 🎯 Articles les plus similaires")
                        st.markdown("---")

                        for i, (article_id, result_info) in enumerate(sorted_results):
                            distance = result_info['distance']

                            # Get URLs from metadata
                            url_roulette, url_kit = get_article_urls(
                                article_id)

                            # Create result card
                            with st.container():
                                # Create clickable URLs with truncated display
                                roulette_display = url_roulette[:40] + "..." if len(
                                    url_roulette) > 30 and url_roulette != "Non trouvé" else url_roulette
                                kit_display = url_kit[:30] + "..." if len(
                                    url_kit) > 30 and url_kit != "Non trouvé" else url_kit

                                roulette_link = f'<a href="{url_roulette}" target="_blank" style="color: #1f77b4; text-decoration: none;" title="{url_roulette}">{roulette_display}</a>' if url_roulette != "Non trouvé" else "Non trouvé"
                                kit_link = f'<a href="{url_kit}" target="_blank" style="color: #1f77b4; text-decoration: none;" title="{url_kit}">{kit_display}</a>' if url_kit != "Non trouvé" else "Non trouvé"

                                st.markdown(f"""
                                <div class="similarity-card">
                                    <div class="article-id">#{i+1} ID Article: {article_id}</div>
                                    <div class="metadata">Distance: {distance:.4f}</div>
                                    <div class="metadata">Lien Roulette: {roulette_link}</div>
                                    <div class="metadata">Lien Kit: {kit_link}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Summary
                        st.markdown("---")
                        if sorted_results:
                            best_article_id = sorted_results[0][0]
                            best_distance = sorted_results[0][1]['distance']
                            st.markdown(
                                f"**Meilleur match:** {best_article_id} avec une distance de {best_distance:.4f}")

                    except Exception as e:
                        st.error(
                            f"Erreur lors du traitement de l'image: {str(e)}")
        else:
            st.info("👆 Veuillez télécharger une image pour commencer")

    # Footer
    st.markdown("---")
    st.markdown("### 📊 Informations sur le Dataset")
    if 'ids' in st.session_state:
        unique_articles = len(set(st.session_state.ids))
        total_images = len(st.session_state.ids)
        st.metric("Total des Articles", unique_articles)
        st.metric("Total des Images", total_images)

        # Show current dataset folders for debugging
        with st.expander("🔍 Dossiers actuels du dataset"):
            current_folders = get_dataset_folders()
            st.write("**Dossiers détectés:**", sorted(current_folders))
            st.write(
                "**Note:** Cliquez sur 'Reconstruire l'Index' après avoir modifié le dataset")


if __name__ == "__main__":
    main()
