import os
import time

import clip
import faiss
import numpy as np
import streamlit as st
import torch
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Luggage AI - Recherche de Similarité d'Images",
    page_icon="🧳",
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
    .similarity-score {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2e8b57;
    }
    .article-id {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model():
    """Load CLIP model and return model, preprocess function, and device"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    return model, preprocess, device


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

    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(
        os.path.join(dataset_path, f))]
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
    index.add(embeddings)

    status_text.text("Index construit avec succès!")
    progress_bar.empty()
    status_text.empty()

    return index, ids


def main():
    # Header
    st.markdown('<h1 class="main-header">🧳 Luggage AI - Recherche de Similarité d&apos;Images </h1>',
                unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar for controls
    with st.sidebar:
        st.header("Paramètres")
        num_results = st.slider("Nombre de résultats similaires", 1, 10, 3)
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("1. Téléchargez une image en utilisant le sélecteur de fichiers")
        st.markdown("2. L'application trouvera les articles de bagage les plus similaires")
        st.markdown("3. Les résultats sont classés par score de similarité")

    # Initialize session state
    if 'index' not in st.session_state or 'ids' not in st.session_state:
        st.info("🔄 Construction de l'index de similarité à partir du dataset... Cela peut prendre un moment.")
        with st.spinner("Chargement du modèle et construction de l'index..."):
            index, ids = build_faiss_index()
            if index is not None:
                st.session_state.index = index
                st.session_state.ids = ids
                st.success("✅ Index construit avec succès!")
            else:
                st.error("❌ Échec de la construction de l'index. Veuillez vérifier votre dataset.")
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
            st.image(image, caption="Image téléchargée", use_container_width=True)

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
                        D, I = st.session_state.index.search(q_emb, search_k)

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
                            # Convert L2 distance to similarity score (lower distance = higher similarity)
                            # Using negative distance as similarity score (higher is better)
                            similarity_score = -distance

                            # Create result card
                            with st.container():
                                st.markdown(f"""
                                <div class="similarity-card">
                                    <div class="article-id">#{i+1} ID Article: {article_id}</div>
                                    <div class="similarity-score">Score de similarité: {similarity_score:.4f}</div>
                                    <div>Distance: {distance:.4f}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Summary
                        st.markdown("---")
                        if sorted_results:
                            best_article_id = sorted_results[0][0]
                            best_distance = sorted_results[0][1]['distance']
                            best_similarity = -best_distance
                            st.markdown(
                                f"**Meilleur match:** {best_article_id} avec un score de similarité de {best_similarity:.4f}")

                    except Exception as e:
                        st.error(f"Erreur lors du traitement de l'image: {str(e)}")
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


if __name__ == "__main__":
    main()
