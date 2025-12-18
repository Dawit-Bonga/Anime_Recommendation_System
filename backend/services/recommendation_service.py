from fastapi import HTTPException
from sklearn.metrics.pairwise import cosine_similarity
from utils.title_normalizer import normalize_title
from services.content_based_service import recommend_content_based

def recommend_collaborative(anime_id: int, objects: dict, limit: int = 10):
    """
    Collaborative Filtering using SVD.
    """
    if 'anime_id_to_idx' not in objects:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if anime_id not in objects.get("anime_id_to_idx", {}):
        raise HTTPException(status_code=404, detail="Anime ID not found in SVD model")
    
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
    seen_base_titles = {}
    
    for i in top_indices:
        rec_id = objects['idx_to_anime_id'][i]
        
        # Skip the input anime itself
        if rec_id == anime_id:
            continue
            
        meta = objects['metadata'].get(rec_id, {})
        rec_title = meta.get('title', "").lower()
        rec_base_title = normalize_title(rec_title)
        
        # --- FILTER 1: Skip sequels of the INPUT anime ---
        if (input_title in rec_title or rec_title in input_title or 
            input_base_title == rec_base_title):
            continue
        
        # --- FILTER 2: Deduplicate other franchises' seasons ---
        score = float(scores[i])
        
        if rec_base_title in seen_base_titles:
            if score > seen_base_titles[rec_base_title][0]:
                seen_base_titles[rec_base_title] = (score, {
                    "id": int(rec_id),
                    "title": meta.get('title', f"Anime #{rec_id}"),
                    "genre": meta.get('genre', 'Unknown'),
                    "score": score,
                    "img_url": None
                })
            continue
        else:
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
    
    return {
        "recommendations": recommendations[:limit],
        "method": "collaborative",
        "message": "Using Collaborative Filtering (SVD)"
    }

def recommend_hybrid(anime_id: int, objects: dict, limit: int = 10):
    """
    Hybrid Recommendation System:
    1. Try Collaborative Filtering (SVD) first
    2. Fall back to Content-Based (TF-IDF) if anime not in training data
    """
    # Check if anime is in SVD model (Collaborative Filtering)
    if anime_id in objects.get("anime_id_to_idx", {}):
        # Use Collaborative Filtering (existing SVD approach)
        return recommend_collaborative(anime_id, objects, limit)
    else:
        # Cold Start: Use Content-Based Filtering (TF-IDF on genres)
        return recommend_content_based(anime_id, objects, limit)