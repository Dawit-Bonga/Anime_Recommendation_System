from fastapi import HTTPException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as tfidf_cosine_similarity
from utils.title_normalizer import normalize_title

def build_tfidf_index(metadata):
    """
    Build TF-IDF vectors for all anime genres.
    Returns: (vectorizer, tfidf_matrix, anime_ids)
    """
    anime_genres = []
    anime_ids = []
    
    for anime_id, meta in metadata.items():
        genre_str = str(meta.get('genre', 'Unknown')).lower()
        genre_str = genre_str.replace('[', '').replace(']', '').replace("'", "")
        anime_genres.append(genre_str)
        anime_ids.append(anime_id)
    
    vectorizer = TfidfVectorizer(
        tokenizer=lambda x: [g.strip() for g in x.split(',')],
        lowercase=True,
        token_pattern=None  # We're doing custom tokenization
    )
    
    tfidf_matrix = vectorizer.fit_transform(anime_genres)
    
    print(f"TF-IDF index built for {len(anime_ids)} animes")
    return vectorizer, tfidf_matrix, anime_ids

def recommend_content_based(anime_id: int, objects: dict, limit: int = 10):
    """
    Content-Based Filtering using TF-IDF on genres.
    Fallback when anime is not in SVD model (cold start problem).
    """
    if 'tfidf_matrix' not in objects:
        raise HTTPException(status_code=503, detail="TF-IDF index not loaded")

    input_meta = objects['metadata'].get(anime_id, {})
    if not input_meta:
        raise HTTPException(status_code=404, detail="Anime not found in metadata")
    
    input_title = input_meta.get('title', "").lower()
    input_base_title = normalize_title(input_title)
    
    # Find the index of this anime in TF-IDF matrix
    try:
        anime_idx = objects['tfidf_anime_ids'].index(anime_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Anime not found in TF-IDF index")
    
    # Get the TF-IDF vector for this anime
    anime_vector = objects['tfidf_matrix'][anime_idx:anime_idx+1]
    
    # Calculate similarity with all other anime
    similarities = tfidf_cosine_similarity(anime_vector, objects['tfidf_matrix']).flatten()
    
    # Get top candidates
    top_indices = similarities.argsort()[::-1][:50]
    
    recommendations = []
    seen_base_titles = {}
    
    for i in top_indices:
        rec_id = objects['tfidf_anime_ids'][i]
        
        # Skip the input anime itself
        if rec_id == anime_id:
            continue
        
        meta = objects['metadata'].get(rec_id, {})
        rec_title = meta.get('title', "").lower()
        rec_base_title = normalize_title(rec_title)
        
        # Filter sequels of input anime
        if (input_title in rec_title or rec_title in input_title or 
            input_base_title == rec_base_title):
            continue
        
        # Deduplicate other franchises' seasons
        score = float(similarities[i])
        
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
        "method": "content_based",
        "message": "Using Content-Based Filtering (TF-IDF)"
    }