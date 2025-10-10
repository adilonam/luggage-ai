import json
import os
import shutil
import time

import streamlit as st
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Valise IA - Administration",
    page_icon="⚙️",
    layout="wide"
)

# Set sidebar title
st.sidebar.title("🧳 Luggage AI")

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


def main():
    # Header
    st.markdown('<h1 class="main-header">⚙️ Administration</h1>',
                unsafe_allow_html=True)
    st.markdown("---")

    # Dataset Management Section
    st.markdown("### 📁 Gestion du Dataset")

    # Get current dataset structure
    dataset_structure = get_dataset_structure()

    if not dataset_structure:
        st.warning(
            "📂 Aucun dataset trouvé. Le dossier 'dataset' est vide ou n'existe pas.")
        return

    # Display current structure
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

    # Remove Images Section
    st.markdown("#### 🗑️ Supprimer des Images")

    # Select article for deletion
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
    # Metadata Management Section
    st.markdown("#### 📋 Gestion des Métadonnées")

    metadata = load_metadata()

    # Display current metadata
    if metadata:
        st.markdown("**Métadonnées actuelles :**")
        for i, entry in enumerate(metadata):
            col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
            with col1:
                st.text(f"Label: {entry['label']}")
            with col2:
                st.text(f"Roulette: {entry['url-roulette']}")
            with col3:
                st.text(f"Kit: {entry['url-kit']}")
            with col4:
                if st.button("🗑️", key=f"del_meta_{i}_{entry['label']}", help="Supprimer cette entrée"):
                    if delete_metadata_entry_by_index(i):
                        st.success(f"✅ Métadonnée {entry['label']} supprimée!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Erreur lors de la suppression de {entry['label']}")
    else:
        st.info("📭 Aucune métadonnée trouvée.")

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
                        "Nouveau Label", value=edit_entry['label'], key="edit_label")
                    edit_new_roulette = st.text_input(
                        "Nouvelle URL Roulette", value=edit_entry['url-roulette'], key="edit_roulette")
                    edit_new_kit = st.text_input(
                        "Nouvelle URL Kit", value=edit_entry['url-kit'], key="edit_kit")

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

    # Footer
    st.markdown("---")
    st.markdown("### ⚠️ Avertissement")
    st.warning("Les modifications apportées au dataset affecteront les résultats de recherche. Assurez-vous de sauvegarder vos données importantes.")


if __name__ == "__main__":
    main()
