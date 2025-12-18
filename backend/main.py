# from numpy.matlib import rec
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
import re
from sklearn.metrics.pairwise import cosine_similarity

# --- PATH CONFIGURATION ---
# We need to find files relative to THIS script, no matter where we run it from
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "svd_model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "data", "myanilist.csv") 

app = FastAPI(title="Anime Recommender API")

# --- CORS (Security Handshake) ---
# This allows your React App (running on localhost:3000) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global dictionary to hold the loaded model in memory
objects = {}


def normalize_title(title):
    """Remove season indicators to get base title."""
    if not title:
        return ""
    
    title_lower = title.lower()
    patterns = [
        r'\s*season\s+\d+',
        r'\s*\d+\s*season',
        r'\s*\d+nd\s*season',
        r'\s*\d+rd\s*season',
        r'\s*\d+th\s*season',
        r'\s*final\s*season',
        r'\s*part\s+\d+',
        r'\s*\d+$',
        r'\s*:\s*the\s+final\s+season',
    ]
    
    normalized = title_lower
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


@app.on_event("startup")
def load_assets():
    print("Server startup")
    
    if os.path.exists(MODEL_PATH):
        model_data = joblib.load(MODEL_PATH)
        objects['model'] = model_data['model']
        objects['anime_id_to_idx'] = model_data['anime_id_to_idx']
        objects['idx_to_anime_id'] = model_data['idx_to_anime_id']
        objects['item_vectors'] = model_data['model'].components_.T
    else:
        print(f"Error: Model not found at {MODEL_PATH}")
    
    if os.path.exists(METADATA_PATH):
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
        # English titles get priority in search
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
    else:
        raise FileNotFoundError(f"Metadata not found at {METADATA_PATH}")
    
    required_keys = ['model', 'anime_id_to_idx', 'idx_to_anime_id', 'metadata']
    for key in required_keys:
        if key not in objects:
            raise ValueError(f"Failed to load required data: {key}")
        
    print("-----All assets loaded successfully-----")

@app.get('/')
def home():
    return {"status": "alive"}

@app.get('/search')
def search_anime(query: str, limit: int = 5):
    query = query.lower().strip()
    if not query:
        return {"results": []}
    
    results = []
    seen_ids = set()  # Track IDs to avoid duplicates
    
    # Step 1: Search English titles first (priority)
    # Exact matches first, then partial matches
    exact_matches = []
    partial_matches = []
    
    for title, uid in objects.get('search_index_english', {}).items():
        if uid in seen_ids:
            continue
        if title == query:
            exact_matches.append((title, uid))
        elif query in title:
            partial_matches.append((title, uid))
    
    # Add exact matches first
    for title, uid in exact_matches:
        meta = objects['metadata'][uid]
        if meta:
            results.append({
                "id": uid,
                "title": meta['title'],
                "img_url": None
            })
            seen_ids.add(uid)
        if len(results) >= limit:
            break
    
    # Then add partial matches
    if len(results) < limit:
        for title, uid in partial_matches:
            if uid not in seen_ids:
                meta = objects['metadata'][uid]
                if meta:
                    results.append({
                        "id": uid,
                        "title": meta['title'],
                        "img_url": None
                    })
                    seen_ids.add(uid)
                if len(results) >= limit:
                    break
    
    # Step 2: If we don't have enough results, search Japanese titles
    if len(results) < limit:
        japanese_exact = []
        japanese_partial = []
        
        for title, uid in objects.get('search_index_japanese', {}).items():
            if uid in seen_ids:
                continue
            if title == query:
                japanese_exact.append((title, uid))
            elif query in title:
                japanese_partial.append((title, uid))
        
        # Add exact Japanese matches
        for title, uid in japanese_exact:
            if uid not in seen_ids:
                meta = objects['metadata'][uid]
                if meta:
                    results.append({
                        "id": uid,
                        "title": meta['title'],
                        "img_url": None
                    })
                    seen_ids.add(uid)
                if len(results) >= limit:
                    break
        
        # Then partial Japanese matches
        if len(results) < limit:
            for title, uid in japanese_partial:
                if uid not in seen_ids:
                    meta = objects['metadata'][uid]
                    if meta:
                        results.append({
                            "id": uid,
                            "title": meta['title'],
                            "img_url": None
                        })
                        seen_ids.add(uid)
                    if len(results) >= limit:
                        break
    
    return {"results": results}

@app.get("/recommend/{anime_id}")
def recommend(anime_id: int):
    
    if 'anime_id_to_idx' not in objects:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if anime_id not in objects.get("anime_id_to_idx", {}):
        raise HTTPException(status_code=404, detail="Anime ID not found")
    
    # 1. Get the Input Title (so we can filter sequels)
    input_meta = objects['metadata'].get(anime_id, {})
    input_title = input_meta.get('title', "").lower()
    input_base_title = normalize_title(input_title)
    
    # 2. Get Vector & Similarity Scores
    idx = objects['anime_id_to_idx'][anime_id]
    target_vector = objects['item_vectors'][idx].reshape(1, -1)
    scores = cosine_similarity(target_vector, objects['item_vectors']).flatten()
    
    # 3. Get Top 50 candidates (We fetch more so we can throw away sequels)
    top_indices = scores.argsort()[::-1][:50]
    
    recommendations = []
    seen_base_titles = {}  # Track: base_title -> (best_score, best_rec)
    
    for i in top_indices:
        rec_id = objects['idx_to_anime_id'][i]
        
        # Skip the input anime itself
        if rec_id == anime_id:
            continue
            
        meta = objects['metadata'].get(rec_id, {})
        rec_title = meta.get('title', "").lower()
        rec_base_title = normalize_title(rec_title)
        
        # --- FILTER 1: Skip sequels of the INPUT anime ---
        # Check if it's a sequel of what the user searched for
        if (input_title in rec_title or rec_title in input_title or 
            input_base_title == rec_base_title):
            continue
        
        # --- FILTER 2: Deduplicate other franchises' seasons ---
        # If we've already seen this base title, keep only the best-scoring one
        score = float(scores[i])
        
        if rec_base_title in seen_base_titles:
            # Replace if this score is better
            if score > seen_base_titles[rec_base_title][0]:
                seen_base_titles[rec_base_title] = (score, {
                    "id": int(rec_id),
                    "title": meta.get('title', f"Anime #{rec_id}"),
                    "genre": meta.get('genre', 'Unknown'),
                    "score": score,
                    "img_url": None
                })
            # Otherwise skip this duplicate
            continue
        else:
            # New base title, add it
            rec_data = {
                "id": int(rec_id),
                "title": meta.get('title', f"Anime #{rec_id}"),
                "genre": meta.get('genre', 'Unknown'),
                "score": score,
                "img_url": None
            }
            seen_base_titles[rec_base_title] = (score, rec_data)
    
    # Convert to list and sort by score
    recommendations = [rec for _, rec in seen_base_titles.values()]
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top 10
    return {"recommendations": recommendations[:10]}
    