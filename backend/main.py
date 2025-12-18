from numpy.matlib import rec
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
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
        meta_df = pd.read_csv(METADATA_PATH, usecols=['ID', 'Title_Romaji', 'Genres'])
        
        #we are using the real japanese titles since a good amount of animes don't have translated names ,esp for this data base
        meta_df = meta_df.rename(columns={
            "ID": 'id',
            'Title_Romaji': 'title', 
            'Genres': 'genre'
        })
        
        meta_df = meta_df.drop_duplicates(subset='id', keep='first')
        
        objects['metadata'] = meta_df.set_index('id').to_dict(orient='index')
        
        objects['search_index'] = {str(r['title']).lower(): uid for uid, r in objects['metadata'].items()}
        print("Metadata loaded")
    else:
        print(f"Error: MetaData not found at {METADATA_PATH}")
        

@app.get('/')
def home():
    return {"status": "alive"}

@app.get('/search')
def search_anime(query:str):
    query = query.lower().strip()
    results = []
    
    for title, uid in objects.get('search_index', {}).items():
        if query in title:
            meta = objects['metadata'][uid]
            results.append({
                "id": uid,
                "title": meta['title'],
                "img_url": None
            })
            if len(results) >=5:
                break
    
    return {"results": results}

@app.get("/recommend/{anime_id}")
def recommend(anime_id: int):
    if anime_id not in objects.get("anime_id_to_idx", {}):
        raise HTTPException(status_code=404, detail="Anime ID not found")
    
    idx = objects['anime_id_to_idx'][anime_id]
    target_vector = objects['item_vectors'][idx].reshape(1, -1)
    
    scores = cosine_similarity(target_vector, objects['item_vectors']).flatten()
    
    top_indices = scores.argsort()[::-1][:11]
    
    recommenddations = []
    
    for i in top_indices:
        rec_id = objects['idx_to_anime_id'][i]
        if rec_id == anime_id:
            continue
        
        meta = objects['metadata'].get(rec_id, {})
        
        recommenddations.append({
            "id": int(rec_id),
            "title": meta.get('title', f"Anime #{rec_id}"),
            "genre": meta.get('genre', 'Unknown'),
            "score": float(scores[i]),
            "img_url": None #we will sort this out later
        })
    
    return {"recommendations": recommenddations}
    