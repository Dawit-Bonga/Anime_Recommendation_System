# 🎌 Anime Recommendation Engine (SVD + Hybrid Filtering)

A Full-Stack Machine Learning application that suggests anime based on user taste vectors. It uses **Singular Value Decomposition (SVD)** to reduce high-dimensional user-rating matrices and a **Hybrid Filtering** system to handle metadata enrichment.

### 🎥 [Watch the Demo Video Here](LINK_TO_YOUR_VIDEO)

## 🛠 Tech Stack

- **ML:** Scikit-learn (TruncatedSVD), Pandas, Numpy
- **Backend:** FastAPI (Python), Regex Filtering, Cold-Start Handling
- **Frontend:** React (Vite), CSS Modules
- **Data:** 35 Million User Ratings (MyAnimeList Snapshot)

## 🚀 Key Engineering Features

1.  **Latent Feature Extraction:** Compressed 6,000+ anime titles into 50 latent features using Matrix Factorization.
2.  **Franchise Deduplication:** Implemented custom Regex logic to normalize titles and prevent "Sequel Spam" (e.g., hiding Season 2/3 if Season 1 is recommended).
3.  **Warm-Start Architecture:** Pre-loads interaction matrices and metadata hash maps into RAM for <50ms inference latency.
4.  **Hybrid Search:** Dual-index search engine supports both English ("Attack on Titan") and Japanese ("Shingeki no Kyojin") queries.

## ⚡ How to Run

1.  Clone the repo
2.  Download the dataset (Link to Kaggle) and place in `data/`
3.  `cd backend && uvicorn main:app --reload`
4.  `cd frontend && npm run dev`
