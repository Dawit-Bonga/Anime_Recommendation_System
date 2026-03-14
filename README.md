# Anime Match

Anime recommendation app with a FastAPI backend and React frontend.

## What it does

- Search anime by title (`/search`)
- Get recommendations from one anime (`/recommend/{anime_id}`)
- Build a watchlist and get combined recommendations (`/recommend/batch`)

## Tech

- Frontend: React + Vite
- Backend: FastAPI
- Recommenders: SVD collaborative filtering + TF-IDF content-based fallback

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

Interactive docs: `http://127.0.0.1:8000/docs`

## Project layout

```text
backend/
  main.py
  train_model.py
  services/
  utils/
frontend/
  src/
requirements.txt
```

## Notes

- First-time model training can take a while depending on dataset size.
- Large dataset files are not committed to Git.
