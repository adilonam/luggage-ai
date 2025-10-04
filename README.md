# 🧳 Luggage AI - Image Similarity Search

A Streamlit web application that uses CLIP and FAISS to find similar luggage articles from a dataset based on uploaded images.

## Features

- **Image Upload**: Upload any image to find similar luggage articles
- **Similarity Search**: Uses CLIP embeddings and FAISS for fast similarity search
- **Ranked Results**: Shows top N most similar articles with similarity scores
- **Interactive UI**: Clean, modern interface with real-time results
- **Configurable**: Adjustable number of results to display

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have a `dataset/` folder with your luggage images organized by article ID:
```
dataset/
├── R118/
│   ├── image1.jpg
│   └── image2.jpg
├── R124/
│   ├── image1.jpg
│   └── image2.jpg
└── ...
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your browser and go to `http://localhost:8501`

3. Upload an image using the file uploader

4. Click "Find Similar Articles" to get ranked results

## How it Works

1. **Model Loading**: Loads CLIP (ViT-B/32) model for image encoding
2. **Dataset Processing**: Processes all images in the dataset folder and creates embeddings
3. **Index Building**: Builds a FAISS index for fast similarity search
4. **Query Processing**: When you upload an image, it:
   - Encodes the image using CLIP
   - Searches the FAISS index for similar embeddings
   - Returns ranked results with similarity scores

## Similarity Scoring

- **Similarity Score**: Normalized score from 0% to 100% (higher is more similar)
- **Distance**: L2 distance in embedding space (lower is more similar)
- Results are ranked from most similar to least similar

## Requirements

- Python 3.8+
- CUDA support (optional, will use CPU if not available)
- Sufficient RAM for loading CLIP model and dataset embeddings

## File Structure

```
luggage-ai/
├── app.py                 # Main Streamlit application
├── main.ipynb            # Jupyter notebook with original logic
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── dataset/             # Your luggage images dataset
    ├── R118/
    ├── R124/
    └── ...
```