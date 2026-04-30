# Anime Match

Anime recommendation app with a FastAPI backend and React frontend.

## What it does

- Search anime by title (`/search`)
- Get recommendations from one anime (`/recommend/{anime_id}`)
- Build a watchlist and get combined recommendations (`/recommend/batch`)
- Explain each recommendation with method, score, shared genre signals, and rule-based filtering notes

## Tech

- Frontend: React + Vite
- Backend: FastAPI
- Recommenders: SVD collaborative filtering + TF-IDF content-based fallback
- Explainability: structured decision traces added to each recommendation

## Requirements

- Python 3.10+
- Node.js 18+
- `data/clean_ratings.csv`
- `data/myanilist.csv`

## Quick start

1. Clone and enter project

```bash
git clone https://github.com/Dawit-Bonga/Anime_Recommendation_System.git
cd ML_rec_system
```

2. Set up backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
python train_model.py
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

Python-only decision trace demo:

```bash
cd backend
python3 demo_decision_trace.py --query "Naruto"
python3 demo_decision_trace.py --ids 20 5114 11061
python3 demo_decision_trace.py --sample --query "Naruto"
```

Use `--sample` for a small Zoo-friendly run that does not depend on the large local dataset/model.

3. Set up frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend usually runs at `http://127.0.0.1:5173`.

Optional backend URL override:

```bash
# frontend/.env
VITE_API_URL=http://127.0.0.1:8000
```

## API (minimal)

### `GET /search?query=<name>&limit=5`

Returns:

```json
{
  "results": [{ "id": 20, "title": "Naruto", "img_url": null }]
}
```

### `GET /recommend/{anime_id}`

Returns top recommendations for one anime.

### `POST /recommend/batch?limit=20`

Body:

```json
[20, 5114, 11061]
```

Returns recommendations based on multiple anime IDs.

Recommendation objects include explanation fields:

```json
{
  "id": 21,
  "title": "One Piece",
  "score": 0.98,
  "method": "collaborative",
  "method_label": "Collaborative filtering (SVD)",
  "shared_genres": ["Action", "Adventure"],
  "filters_applied": ["removed the original title and same-franchise sequels"],
  "evidence": ["SVD item-vector cosine similarity score: 0.980"],
  "explanation": {
    "summary": "Recommended because users with similar taste patterns tended to rate related titles similarly."
  }
}
```

Interactive docs: `http://127.0.0.1:8000/docs`

## Project layout

```text
backend/
  main.py
  train_model.py
  demo_decision_trace.py
  services/
  utils/
frontend/
  src/
FINAL_WRITEUP.md
zoo_submission/  # ignored local upload bundle
requirements.txt
```

## Notes

- First-time model training can take a while depending on dataset size.
- Large dataset files are not committed to Git.
- `zoo_submission/` is intentionally ignored by Git and is used as a local upload bundle for the course submission.
