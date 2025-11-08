import json
import os
import shutil
import time

import clip
import faiss
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import torch
from PIL import Image

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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .admin-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def get_dataset_structure():
    """Get the current dataset structure"""
    dataset_path = "dataset/"
    if not os.path.exists(dataset_path):
        return {}

    structure = {}
    for item in os.listdir(dataset_path):
        item_path = os.path.join(dataset_path, item)
        if os.path.isdir(item_path):
            images = [f for f in os.listdir(item_path)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
            structure[item] = images

    return structure


def delete_image(article_id, image_name):
    """Delete an image from the dataset"""
    image_path = os.path.join("dataset", article_id, image_name)
    if os.path.exists(image_path):
        os.remove(image_path)
        return True
    return False


def add_image_to_article(article_id, uploaded_file):
    """Add an uploaded image to an article directory"""
    article_path = os.path.join("dataset", article_id)
    if not os.path.exists(article_path):
        os.makedirs(article_path)

    # Save the uploaded file
    file_path = os.path.join(article_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return True


def delete_article_folder(article_id):
    """Delete an entire article folder and all its contents"""
    article_path = os.path.join("dataset", article_id)
    if os.path.exists(article_path):
        shutil.rmtree(article_path)
        return True
    return False


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


def save_metadata(metadata):
    """Save metadata to JSON file"""
    metadata_path = "dataset/metadata.json"
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du metadata: {str(e)}")
        return False


def add_metadata_entry(label, url_roulette, url_kit):
    """Add a new metadata entry"""
    metadata = load_metadata()
    new_entry = {
        "label": label,
        "url-roulette": url_roulette,
        "url-kit": url_kit
    }
    metadata.append(new_entry)
    return save_metadata(metadata)


def update_metadata_entry(old_label, new_label, url_roulette, url_kit):
    """Update an existing metadata entry"""
    metadata = load_metadata()
    for entry in metadata:
        if entry["label"] == old_label:
            entry["label"] = new_label
            entry["url-roulette"] = url_roulette
            entry["url-kit"] = url_kit
            break
    return save_metadata(metadata)


def delete_metadata_entry(label):
    """Delete a metadata entry by label (removes first occurrence)"""
    metadata = load_metadata()
    # Remove the first occurrence of the entry with this label
    for i, entry in enumerate(metadata):
        if entry["label"] == label:
            metadata.pop(i)
            break
    return save_metadata(metadata)


def delete_metadata_entry_by_index(index):
    """Delete a metadata entry by index"""
    metadata = load_metadata()
    if 0 <= index < len(metadata):
        metadata.pop(index)
        return save_metadata(metadata)
    return False


def load_app_config():
    """Load application configuration from JSON file"""
    config_path = "./dataset/app_config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(
                f"Erreur lors du chargement de la configuration: {str(e)}")
            return {"num_results": 3, "rebuild_index": False, "admin_password": ""}
    return {"num_results": 3, "rebuild_index": False, "admin_password": ""}


def save_app_config(config):
    """Save application configuration to JSON file"""
    config_path = "./dataset/app_config.json"
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
        return False


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

    # Get all article directories
    article_dirs = [f for f in os.listdir(dataset_path)
                    if os.path.isdir(os.path.join(dataset_path, f))]

    total_articles = len(article_dirs)
    processed_articles = 0

    for article_id in article_dirs:
        article_path = os.path.join(dataset_path, article_id)
        images = [f for f in os.listdir(article_path)
                  if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]

        for image_name in images:
            image_path = os.path.join(article_path, image_name)
            try:
                # Load and preprocess image
                image = Image.open(image_path).convert('RGB')
                image_tensor = preprocess(image).unsqueeze(0).to(device)

                # Encode image
                with torch.no_grad():
                    embedding = model.encode_image(image_tensor).cpu().numpy()
                    embeddings.append(embedding.flatten())
                    ids.append(f"{article_id}/{image_name}")

            except Exception as e:
                st.warning(
                    f"Erreur lors du traitement de {image_path}: {str(e)}")

        processed_articles += 1
        progress = processed_articles / total_articles
        progress_bar.progress(progress)
        status_text.text(
            f"Traitement de l'article {article_id} ({processed_articles}/{total_articles})")

    if not embeddings:
        st.error("Aucune image valide trouvée dans le dataset!")
        return None, None

    # Build FAISS index
    embeddings_array = np.array(embeddings).astype('float32')
    dimension = embeddings_array.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    progress_bar.empty()
    status_text.empty()

    return index, ids


def main():
    # Load configuration
    config = load_app_config()
    admin_password = config.get('admin_password', '')

    # Check if password is set
    if admin_password:
        # Password is set, require authentication
        if 'admin_authenticated' not in st.session_state:
            st.session_state.admin_authenticated = False

        if not st.session_state.admin_authenticated:
            # Show login form
            st.markdown('<h1 class="main-header">⚙️ Administration</h1>',
                        unsafe_allow_html=True)
            st.markdown("---")

            st.markdown("### 🔐 Authentification Requise")
            entered_password = st.text_input(
                "Mot de passe administrateur", type="password")

            if st.button("Se connecter", type="primary"):
                if entered_password == admin_password:
                    st.session_state.admin_authenticated = True
                    st.success("✅ Authentification réussie!")
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect!")

            st.markdown("---")
            st.info(
                "💡 Si vous avez oublié le mot de passe, supprimez le fichier `./dataset/app_config.json` et recréez-le.")
            return

    # Header (only shown when authenticated)
    st.markdown('<h1 class="main-header">⚙️ Administration</h1>',
                unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar for maintenance controls
    with st.sidebar:
        st.header("🔧 Paramètres")
        st.markdown("---")

        # Number of similar results slider
        # Load persistent config
        config = load_app_config()
        previous_value = config.get('num_results', 3)

        num_results = st.slider(
            "Nombre de résultats similaires", 1, 10, previous_value, key='num_results_slider')

        # Store the value in session state and persistent config if changed
        if num_results != previous_value:
            st.session_state.num_results = num_results
            config['num_results'] = num_results
            if save_app_config(config):
                st.success(f"✅ Nombre de résultats mis à jour: {num_results}")
            else:
                st.error("❌ Erreur lors de la sauvegarde de la configuration")
        else:
            st.session_state.num_results = num_results
        st.markdown("---")

        # Rebuild index button
        if st.button("🔄 Reconstruire l'Index", type="secondary", use_container_width=True):
            # Set rebuild flag in config to trigger rebuild on Accueil page
            config = load_app_config()
            config['rebuild_index'] = True
            if save_app_config(config):
                st.success(
                    "✅ L'index sera reconstruit automatiquement sur la page d'accueil.")
            else:
                st.error(
                    "❌ Erreur lors de la sauvegarde de la configuration de reconstruction.")
            st.rerun()

        st.markdown("---")

        # Logout button
        if st.button("🚪 Se déconnecter", type="secondary", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.rerun()

    # Dataset Management Section
    st.markdown("### 📁 Gestion du Dataset")

    # Get current dataset structure
    dataset_structure = get_dataset_structure()

    if not dataset_structure:
        st.warning(
            "📂 Aucun dataset trouvé. Le dossier 'dataset' est vide ou n'existe pas.")
        return

    st.markdown("---")

    # Create New Article Section
    st.markdown("#### 🆕 Créer un Nouvel Article")

    new_article_id = st.text_input(
        "Nouvel ID d'article",
        placeholder="Ex: R999",
        help="Entrez un nouvel ID d'article (ex: R999)"
    )

    if new_article_id:
        if st.button("📁 Créer l'Article", type="secondary"):
            article_path = os.path.join("dataset", new_article_id)
            try:
                if os.path.exists(article_path):
                    st.error(f"❌ L'article {new_article_id} existe déjà!")
                else:
                    os.makedirs(article_path)
                    st.success(f"✅ Article {new_article_id} créé avec succès!")
                    time.sleep(2)  # Wait 2 seconds to show the message
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la création: {str(e)}")
    st.markdown("---")

    # Add Images Section
    st.markdown("#### ➕ Ajouter des Images")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Select article ID
        article_ids = list(dataset_structure.keys())
        selected_article = st.selectbox(
            "Sélectionner un article ID",
            article_ids,
            help="Choisissez l'article auquel ajouter des images"
        )

    with col2:
        # Upload new images
        uploaded_files = st.file_uploader(
            "Télécharger des images",
            type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            accept_multiple_files=True,
            help="Sélectionnez une ou plusieurs images à ajouter"
        )

    if uploaded_files and selected_article:
        if st.button("📤 Ajouter les Images", type="primary"):
            success_count = 0
            for uploaded_file in uploaded_files:
                if add_image_to_article(selected_article, uploaded_file):
                    success_count += 1

            if success_count > 0:
                st.success(
                    f"✅ {success_count} image(s) ajoutée(s) avec succès à l'article {selected_article}!")
                time.sleep(2)  # Wait 2 seconds to show the message
                st.rerun()
            else:
                st.error("❌ Erreur lors de l'ajout des images.")

    st.markdown("---")

    # Add/Edit Metadata
    st.markdown("#### ➕ Ajouter/Modifier des Métadonnées")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Add new metadata
        st.markdown("**Ajouter une nouvelle entrée :**")
        new_label = st.text_input(
            "Label", placeholder="Ex: R999", key="new_label")
        new_url_roulette = st.text_input(
            "URL Roulette", placeholder="https://roulette.r999", key="new_roulette")
        new_url_kit = st.text_input(
            "URL Kit", placeholder="https://kit.r999", key="new_kit")

        if st.button("➕ Ajouter Métadonnée", key="add_metadata"):
            if new_label and new_url_roulette and new_url_kit:
                if add_metadata_entry(new_label, new_url_roulette, new_url_kit):
                    st.success(
                        f"✅ Métadonnée {new_label} ajoutée avec succès!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'ajout de la métadonnée.")
            else:
                st.error("❌ Veuillez remplir tous les champs.")

    with col2:
        # Edit existing metadata
        metadata = load_metadata()
        if metadata:
            st.markdown("**Modifier une entrée existante :**")
            edit_label = st.selectbox("Sélectionner à modifier", [
                                      entry['label'] for entry in metadata], key="edit_select")

            if edit_label:
                # Find the entry to edit
                edit_entry = next(
                    (entry for entry in metadata if entry['label'] == edit_label), None)
                if edit_entry:
                    edit_new_label = st.text_input(
                        "Nouveau Label", value=edit_entry['label'], key=f"edit_label_{edit_label}")
                    edit_new_roulette = st.text_input(
                        "Nouvelle URL Roulette", value=edit_entry['url-roulette'], key=f"edit_roulette_{edit_label}")
                    edit_new_kit = st.text_input(
                        "Nouvelle URL Kit", value=edit_entry['url-kit'], key=f"edit_kit_{edit_label}")

                    if st.button("✏️ Modifier Métadonnée", key="edit_metadata"):
                        if edit_new_label and edit_new_roulette and edit_new_kit:
                            if update_metadata_entry(edit_label, edit_new_label, edit_new_roulette, edit_new_kit):
                                st.success(
                                    f"✅ Métadonnée {edit_label} modifiée avec succès!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(
                                    "❌ Erreur lors de la modification de la métadonnée.")
                        else:
                            st.error("❌ Veuillez remplir tous les champs.")
        else:
            st.info("📭 Aucune métadonnée à modifier.")

    st.markdown("---")

    # Metadata Management Section
    st.markdown("#### 📋 Gestion des Métadonnées")

    metadata = load_metadata()

    # Display current metadata
    if metadata:
        st.markdown("**Métadonnées actuelles :**")

        # Add header row
        cols_header = st.columns([0.5, 2, 4, 4, 1])
        with cols_header[0]:
            st.markdown("**#**")
        with cols_header[1]:
            st.markdown("**Label**")
        with cols_header[2]:
            st.markdown("**URL Roulette**")
        with cols_header[3]:
            st.markdown("**URL Kit**")
        with cols_header[4]:
            st.markdown("**Action**")

        st.markdown("---")

        # Display table rows with delete buttons
        for i, entry in enumerate(metadata):
            cols = st.columns([0.5, 2, 4, 4, 1])
            with cols[0]:
                st.markdown(f"{i + 1}")
            with cols[1]:
                st.text(entry['label'])
            with cols[2]:
                st.text(entry['url-roulette'])
            with cols[3]:
                st.text(entry['url-kit'])
            with cols[4]:
                if st.button("🗑️", key=f"del_meta_{i}_{entry['label']}", help=f"Supprimer {entry['label']}"):
                    if delete_metadata_entry_by_index(i):
                        st.success(f"✅ Del {entry['label']}")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Erreur lors de la suppression de {entry['label']}")
    else:
        st.info("📭 Aucune métadonnée trouvée.")

    st.markdown("---")

    # Remove Images Section
    st.markdown("#### 🗑️ Supprimer des Images")

    # Select article for deletion
    article_ids = list(dataset_structure.keys())
    selected_article_del = st.selectbox(
        "Sélectionner un article pour supprimer des images",
        article_ids,
        key="delete_article",
        help="Choisissez l'article dont vous voulez supprimer des images"
    )

    if selected_article_del and selected_article_del in dataset_structure:
        images = dataset_structure[selected_article_del]

        if not images:
            st.info(f"📭 Aucune image dans l'article {selected_article_del}")
        else:
            st.markdown(f"**Images dans {selected_article_del} :**")

            # Display images in a grid
            cols = st.columns(3)
            for i, image_name in enumerate(images):
                with cols[i % 3]:
                    image_path = os.path.join(
                        "dataset", selected_article_del, image_name)
                    try:
                        # Display thumbnail
                        img = Image.open(image_path)
                        img.thumbnail((150, 150))
                        st.image(img, caption=image_name,
                                 use_container_width=True)

                        # Delete button
                        if st.button(f"🗑️ Supprimer", key=f"del_{image_name}"):
                            if delete_image(selected_article_del, image_name):
                                st.success(
                                    f"✅ Image {image_name} supprimée avec succès!")
                                # Wait 2 seconds to show the message
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ Erreur lors de la suppression de {image_name}")
                    except Exception as e:
                        st.error(
                            f"❌ Erreur lors du chargement de {image_name}: {str(e)}")

    st.markdown("---")

    # Delete Entire Article Section
    st.markdown("#### 🗂️ Supprimer un Article Complet")

    if dataset_structure:
        selected_article_delete = st.selectbox(
            "Sélectionner un article à supprimer complètement",
            list(dataset_structure.keys()),
            key="delete_entire_article",
            help="⚠️ ATTENTION: Cette action supprimera TOUTES les images de cet article!"
        )

        if selected_article_delete:
            article_images_count = len(
                dataset_structure[selected_article_delete])
            st.warning(
                f"⚠️ **Attention:** Cette action supprimera l'article **{selected_article_delete}** et ses **{article_images_count} image(s)** de façon définitive!")

            # Confirmation checkbox
            confirm_delete = st.checkbox(
                f"Je confirme vouloir supprimer l'article {selected_article_delete}",
                key=f"confirm_delete_{selected_article_delete}"
            )

            if confirm_delete:
                if st.button("🗑️ Supprimer l'Article Complet", type="primary", key=f"delete_article_{selected_article_delete}"):
                    if delete_article_folder(selected_article_delete):
                        st.success(
                            f"✅ Article {selected_article_delete} et toutes ses images supprimés avec succès!")
                        # Wait 2 seconds to show the message
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Erreur lors de la suppression de l'article {selected_article_delete}")
    else:
        st.info("📭 Aucun article disponible pour la suppression.")

    st.markdown("---")

    # Password Management Section
    st.markdown("### 🔐 Gestion du Mot de Passe")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Changer le mot de passe :**")
        new_password = st.text_input(
            "Nouveau mot de passe", type="password", key="new_pass")
        confirm_password = st.text_input(
            "Confirmer le nouveau mot de passe", type="password", key="confirm_pass")

        if st.button("🔑 Changer le Mot de Passe", key="change_password"):
            if not new_password or not confirm_password:
                st.error("❌ Veuillez remplir tous les champs.")
            elif new_password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas.")
            else:
                config['admin_password'] = new_password
                if save_app_config(config):
                    st.success("✅ Mot de passe modifié avec succès!")
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la sauvegarde du mot de passe.")

    with col2:
        st.markdown("**Supprimer le mot de passe :**")
        st.warning(
            "⚠️ Supprimer le mot de passe rendra la page d'administration accessible à tous.")

        if st.button("🗑️ Supprimer le Mot de Passe", key="remove_password"):
            config['admin_password'] = ""
            if save_app_config(config):
                st.success(
                    "✅ Mot de passe supprimé. La page est maintenant accessible sans authentification.")
                st.session_state.admin_authenticated = False
                st.rerun()
            else:
                st.error("❌ Erreur lors de la suppression du mot de passe.")

    st.markdown("---")

    # Display current structure at the very bottom
    st.markdown("#### 📊 Structure actuelle du dataset")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Articles disponibles :**")
        for article_id, images in dataset_structure.items():
            st.markdown(f"• **{article_id}** : {len(images)} image(s)")

    with col2:
        total_articles = len(dataset_structure)
        total_images = sum(len(images)
                           for images in dataset_structure.values())
        st.metric("Total Articles", total_articles)
        st.metric("Total Images", total_images)


if __name__ == "__main__":
    main()
