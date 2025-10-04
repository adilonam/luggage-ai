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
    page_title="Luggage AI - Image Similarity Search",
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
        st.error(f"Dataset path '{dataset_path}' not found!")
        return None, None

    progress_bar = st.progress(0)
    status_text = st.empty()

    folders = [f for f in os.listdir(dataset_path) if os.path.isdir(
        os.path.join(dataset_path, f))]
    total_folders = len(folders)

    for idx, id_article in enumerate(folders):
        folder = os.path.join(dataset_path, id_article)
        status_text.text(f"Processing folder: {id_article}")

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
                    st.warning(f"Error processing {image_path}: {str(e)}")

        progress_bar.progress((idx + 1) / total_folders)

    if not embeddings:
        st.error("No valid images found in dataset!")
        return None, None

    embeddings = np.vstack(embeddings).astype("float32")

    # Build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    status_text.text("Index built successfully!")
    progress_bar.empty()
    status_text.empty()

    return index, ids


def calculate_similarity_scores(distances):
    """Convert distances to similarity scores (0-1 scale)"""
    # Normalize distances to 0-1 scale where 1 is most similar
    max_distance = max(distances)
    min_distance = min(distances)

    if max_distance == min_distance:
        return [1.0] * len(distances)

    similarities = []
    for dist in distances:
        # Invert and normalize: closer to 0 distance = higher similarity
        similarity = 1 - (dist - min_distance) / (max_distance - min_distance)
        similarities.append(similarity)

    return similarities


def main():
    # Header
    st.markdown('<h1 class="main-header">🧳 Luggage AI - Image Similarity Search</h1>',
                unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar for controls
    with st.sidebar:
        st.header("Settings")
        num_results = st.slider("Number of similar results", 1, 10, 3)
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("1. Upload an image using the file uploader")
        st.markdown("2. The app will find the most similar luggage articles")
        st.markdown("3. Results are ranked by similarity score")

    # Initialize session state
    if 'index' not in st.session_state or 'ids' not in st.session_state:
        st.info("🔄 Building similarity index from dataset... This may take a moment.")
        with st.spinner("Loading model and building index..."):
            index, ids = build_faiss_index()
            if index is not None:
                st.session_state.index = index
                st.session_state.ids = ids
                st.success("✅ Index built successfully!")
            else:
                st.error("❌ Failed to build index. Please check your dataset.")
                return

    # Main content area
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📸 Upload Image")
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            help="Upload an image to find similar luggage articles"
        )

        if uploaded_file is not None:
            # Display uploaded image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)

    with col2:
        st.header("🔍 Search Results")

        if uploaded_file is not None:
            if st.button("🔍 Find Similar Articles", type="primary"):
                with st.spinner("Analyzing image and finding similar articles..."):
                    # Load model
                    model, preprocess, device = load_model()

                    # Process uploaded image
                    try:
                        # Convert uploaded file to PIL Image and preprocess
                        query_img = preprocess(image).unsqueeze(0).to(device)

                        # Encode image
                        with torch.no_grad():
                            q_emb = model.encode_image(query_img).cpu().numpy()

                        # Search for similar images
                        D, I = st.session_state.index.search(
                            q_emb, num_results)

                        # Calculate similarity scores
                        distances = D[0].tolist()
                        similarities = calculate_similarity_scores(distances)

                        # Display results
                        st.markdown("### 🎯 Most Similar Articles")
                        st.markdown("---")

                        for i in range(num_results):
                            article_id = st.session_state.ids[I[0][i]]
                            distance = distances[i]
                            similarity = similarities[i]

                            # Create result card
                            with st.container():
                                st.markdown(f"""
                                <div class="similarity-card">
                                    <div class="article-id">#{i+1} Article ID: {article_id}</div>
                                    <div class="similarity-score">Similarity: {similarity:.1%}</div>
                                    <div>Distance: {distance:.4f}</div>
                                </div>
                                """, unsafe_allow_html=True)

                        # Summary
                        st.markdown("---")
                        st.markdown(
                            f"**Best Match:** {st.session_state.ids[I[0][0]]} with {similarities[0]:.1%} similarity")

                    except Exception as e:
                        st.error(f"Error processing image: {str(e)}")
        else:
            st.info("👆 Please upload an image to get started")

    # Footer
    st.markdown("---")
    st.markdown("### 📊 Dataset Information")
    if 'ids' in st.session_state:
        unique_articles = len(set(st.session_state.ids))
        total_images = len(st.session_state.ids)
        st.metric("Total Articles", unique_articles)
        st.metric("Total Images", total_images)


if __name__ == "__main__":
    main()
