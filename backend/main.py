from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data_loader import initialize_all
from services.recommendation_service import recommend_hybrid, recommend_batch
from services.search_service import search_anime
from typing import List

app = FastAPI(title="Anime Recommender API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
objects = {}

@app.on_event("startup")
def load_assets():
    global objects
    objects = initialize_all()

@app.get('/')
def home():
    return {"status": "alive"}

@app.get('/search')
def search_endpoint(query: str, limit: int = 5):
    return search_anime(query, objects, limit)

@app.get("/recommend/{anime_id}")
def recommend_endpoint(anime_id: int):
    return recommend_hybrid(anime_id, objects)


@app.post("/recommend/batch")
def recommend_batch_endpoint(anime_ids: List[int], limit: int = 20):
    """
    Get recommendations based on multiple anime IDs.
    """
    if not anime_ids:
        raise HTTPException(status_code=400, detail="At least one anime ID required")

    return recommend_batch(anime_ids, objects, limit)
    