## 🎌 Anime Recommendation Engine

A full-stack anime recommendation system that lets you:

- **Search** anime by English or Japanese title
- **Add shows to _My List_** (persistent watchlist)
- Get **“Because you watched X, Y, Z”**-style recommendations

Built with **FastAPI + React** on top of a **35M+ MyAnimeList ratings** dataset using **SVD collaborative filtering** and **TF‑IDF content-based filtering**.

### 🎥 Demo

- Add your demo link here: `https://your-demo-link.com`
- Or a short video: `https://your-demo-video.com`

---

## 🛠 Tech Stack

- **Frontend**: React (Vite), modern CSS, `react-hot-toast`
- **Backend**: FastAPI, Uvicorn, Pydantic
- **ML / Data**: Scikit-learn (TruncatedSVD, TF‑IDF), SciPy, Pandas, NumPy
- **Data Source**: 35M+ user ratings (MyAnimeList), anime metadata CSV

---

## 🚀 Key Features

1. **Hybrid Recommendation Engine**

   - **Collaborative Filtering (SVD)** over a large user–anime rating matrix
   - **Content-Based (TF‑IDF)** fallback for cold-start titles using genre metadata
   - Hybrid logic chooses SVD when possible and TF‑IDF otherwise

2. **“Because You Watched X, Y, Z” Watchlist**

   - Users maintain a **My List** (stored in `localStorage`)
   - Backend `/recommend/batch` endpoint aggregates similarity scores over multiple titles
   - Returns ranked recommendations **excluding** items already in the list
   - Explanation text: _“Because you watched X, Y, Z…”_ using the input titles

3. **Franchise Deduplication & Title Normalization**

   - Regex-based `normalize_title` removes season markers and sequel tags
   - Avoids “sequel spam” (e.g., hiding Season 2/3 if Season 1 is recommended)
   - Deduplicates across franchise entries while keeping the best-scoring title

4. **Dual-Language Search**

   - Precomputed search indices for **English** and **Japanese** titles
   - Prioritizes exact matches, then partial matches, English first then Japanese
   - Returns lightweight search results ready for UI display

5. **Fast, Warm-Started Inference**

   - Models, embeddings, and metadata are loaded into memory on FastAPI startup
   - SVD item vectors and TF‑IDF matrices are reused across requests
   - Enables low-latency recommendations suitable for interactive use

6. **Polished Frontend UX**
   - Skeleton loaders and progress bar during heavy operations
   - Toast notifications for success and error states
   - Keyboard shortcuts: **Enter** to search, **Esc** to clear
   - Responsive, dark-themed UI with anime-card layout

---

## ⚙️ Setup & Running Locally

### 1. Clone & Data

```bash
git clone https://github.com/your-username/ML_rec_system.git
cd ML_rec_system
```

Place the data files into the `data/` directory:

- `clean_ratings.csv` → `data/clean_ratings.csv`
- `myanilist.csv` → `data/myanilist.csv`

> These files are too large for Git; typically downloaded from Kaggle / MyAnimeList exports.

### 2. Backend (FastAPI)

Create and activate a virtual environment, then install dependencies:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
```

#### Train the SVD model (one-time)

```bash
python train_model.py
```

This:

- Loads `data/clean_ratings.csv`
- Builds a user–anime sparse matrix
- Trains `TruncatedSVD(n_components=50)`
- Saves `models/svd_model.pkl` with the model and ID mappings

#### Run the API

```bash
uvicorn main:app --reload
```

By default:

- API base URL: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

### 3. Frontend (React + Vite)

```bash
cd ../frontend
npm install
```

Optional: configure the backend URL:

```bash
cp .env.example .env
# Edit VITE_API_URL if your backend isn't on http://127.0.0.1:8000
```

Run the dev server:

```bash
npm run dev
```

Vite will print the local URL (usually `http://127.0.0.1:5173`).

---

## 🔌 API Overview

FastAPI automatically exposes docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

### `GET /search`

Search anime by English or Japanese title.

**Query params:**

- `query` (str, required) – search string
- `limit` (int, optional, default=5) – max results

**Example:**

`GET /search?query=naruto&limit=5`

**Response:**

```json
{
  "results": [{ "id": 20, "title": "Naruto", "img_url": null }]
}
```

---

### `GET /recommend/{anime_id}`

Recommendations based on a **single** anime ID.

**Example:**

`GET /recommend/20`

**Response:**

```json
{
  "recommendations": [
    {
      "id": 1735,
      "title": "Naruto: Shippuden",
      "genre": "Action",
      "score": 0.87,
      "img_url": null
    }
  ],
  "method": "collaborative",
  "message": "Using Collaborative Filtering (SVD)"
}
```

If the anime is missing in the SVD model, the backend falls back to **TF‑IDF content-based** recommendations.

---

### `POST /recommend/batch`

Get recommendations based on **multiple** anime IDs (the My List watchlist).

**Query params:**

- `limit` (int, optional, default=20) – max recommendations

**Body (JSON):**

```json
[20, 5114, 11061]
```

**Response:**

```json
{
  "recommendations": [
    {
      "id": 30276,
      "title": "One Punch Man",
      "genre": "Action, Comedy",
      "score": 0.91,
      "img_url": null
    }
  ],
  "method": "batch_collaborative",
  "message": "Based on 3 animes in your list",
  "input_titles": [
    "Naruto",
    "Fullmetal Alchemist: Brotherhood",
    "Hunter x Hunter (2011)"
  ]
}
```

---

## 💅 Frontend UX Details

- **My List (Watchlist)**

  - Add shows from search results with **“+ Add to My List”**
  - Stored in `localStorage` to persist across refreshes
  - Remove items inline; call `/recommend/batch` using all IDs in the list

- **Loading & Feedback**

  - Skeleton loaders while searching and loading recommendations
  - Progress bar while enriching recommendations with images and metadata
  - Toast notifications for:
    - Empty search / no results
    - Backend errors (server down, 404, etc.)
    - Adding/removing from My List

- **Keyboard Shortcuts**
  - **Enter** – trigger search
  - **Esc** – clear query and results

---

## 🧠 How the Recommendations Work

1. **Data Preparation**

   - Read `clean_ratings.csv` into a Pandas DataFrame
   - Map usernames and anime IDs to integer indices
   - Build a SciPy CSR sparse matrix: users × animes

2. **Collaborative Filtering (SVD)**

   - Train `TruncatedSVD(n_components=50)` on the sparse matrix
   - Use item-factor vectors (columns of the component matrix) as item embeddings
   - Recommend using cosine similarity between item embeddings

3. **Content-Based (TF‑IDF)**

   - Extract and clean genres from `myanilist.csv`
   - Build a TF‑IDF matrix over genres per anime ID
   - For cold-start titles (not in SVD), compute cosine similarity over TF‑IDF vectors

4. **Hybrid + Post-Processing**
   - Prefer SVD when the anime is in the model, otherwise use TF‑IDF
   - Normalize titles (remove “Season 2”, “Shippuden”, “Brotherhood”, etc.)
   - Filter out sequels of the input anime(s)
   - Deduplicate franchises by base title and keep the best-scoring entry

---

## 🔮 Possible Future Improvements

- Add user accounts and allow users to rate anime directly in the app
- Deploy backend (Railway/Render) and frontend (Vercel/Netlify) for a public demo
- Add offline evaluation (e.g., precision@k, recall@k) on a validation split
- Add additional signals (studios, tags, popularity) to the content-based side
- Experiment with neural recommenders (e.g., implicit MF, autoencoders, or transformers)

---

## 📄 License

Choose and state a license here (e.g., MIT, Apache 2.0) depending on how you want others to use this project.
