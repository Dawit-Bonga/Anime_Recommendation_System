import pandas as pd
import joblib
import os
from config import MODEL_PATH, METADATA_PATH
from services.content_based_service import build_tfidf_index

def load_svd_model():
    """Load SVD model from disk."""
    objects = {}
    
    if os.path.exists(MODEL_PATH):
        model_data = joblib.load(MODEL_PATH)
        objects['model'] = model_data['model']
        objects['anime_id_to_idx'] = model_data['anime_id_to_idx']
        objects['idx_to_anime_id'] = model_data['idx_to_anime_id']
        objects['item_vectors'] = model_data['model'].components_.T
        print("SVD model loaded successfully")
    else:
        print(f"Error: Model not found at {MODEL_PATH}")
    
    return objects

def load_metadata():
    """Load and index metadata."""
    objects = {}
    
    if not os.path.exists(METADATA_PATH):
        raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}")
    
    meta_df = pd.read_csv(METADATA_PATH, usecols=['ID', 'Title_Romaji', 'Title_English', 'Genres'])
    
    # Use English title if available, otherwise fall back to Romaji (Japanese)
    meta_df['title'] = meta_df['Title_English'].fillna(meta_df['Title_Romaji'])
    meta_df['title_japanese'] = meta_df['Title_Romaji']
    
    meta_df = meta_df.rename(columns={
        "ID": 'id',
        'Genres': 'genre'
    })
    
    meta_df = meta_df.drop_duplicates(subset='id', keep='first')
    
    # Store metadata with both English and Japanese titles accessible
    objects['metadata'] = meta_df.set_index('id').to_dict(orient='index')
    
    # Create search index: prioritize English titles, then Japanese
    objects['search_index_english'] = {}
    objects['search_index_japanese'] = {}
    
    for uid, r in objects['metadata'].items():
        # Get English title (may be NaN, so handle it)
        english_title_raw = r.get('Title_English')
        english_title = str(english_title_raw).lower().strip() if pd.notna(english_title_raw) else ''
        
        # Get Japanese title
        japanese_title_raw = r.get('title_japanese')
        japanese_title = str(japanese_title_raw).lower().strip() if pd.notna(japanese_title_raw) else ''
        
        # Add to search indices if valid
        if english_title and english_title != 'nan' and english_title:
            objects['search_index_english'][english_title] = uid
        if japanese_title and japanese_title != 'nan' and japanese_title:
            objects['search_index_japanese'][japanese_title] = uid
    
    print("Metadata loaded with English and Japanese search indices")
    return objects

def initialize_all():
    """Load all assets on startup."""
    print("Server startup")
    
    # Load SVD model
    objects = load_svd_model()
    
    # Load metadata
    metadata_objects = load_metadata()
    objects.update(metadata_objects)
    
    # Build TF-IDF index
    vectorizer, tfidf_matrix, anime_ids = build_tfidf_index(objects['metadata'])
    objects['tfidf_vectorizer'] = vectorizer
    objects['tfidf_matrix'] = tfidf_matrix
    objects['tfidf_anime_ids'] = anime_ids
    
    # Validate required keys
    required_keys = ['model', 'anime_id_to_idx', 'idx_to_anime_id', 'metadata']
    for key in required_keys:
        if key not in objects:
            raise ValueError(f"Failed to load required data: {key}")
    
    print("-----All assets loaded successfully-----")
    return objects