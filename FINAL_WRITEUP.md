# Explainable Hybrid Anime Recommendation System

## Project Overview

This project is an automated decision system for anime recommendation. Given one anime title or a small watchlist, the system chooses a ranked list of likely next watches and explains why each item was selected.

The project fits CS 4580/5580 because it combines machine learning with explicit decision logic and produces explanations for its recommendations instead of returning only black-box scores.

## Automated Decision

The decision task is:

1. Identify the user's input anime or watchlist.
2. Generate candidate anime using collaborative filtering or content-based similarity.
3. Remove poor candidates using rule-based filtering.
4. Rank the remaining candidates.
5. Explain the evidence behind each recommendation.

The system does not decide whether a person should watch an anime in an absolute sense. It decides which anime are most relevant relative to the user's stated preference.

## Data And Model Design

The full local project uses two data artifacts:

- `data/clean_ratings.csv`: user ratings used to train collaborative filtering.
- `data/myanilist.csv`: anime metadata, including titles and genres.

The trained model is stored as:

- `models/svd_model.pkl`

These files are intentionally not committed because they are large. For Zoo/Gradescope submission, the project includes a small sample-mode demo that exercises the same decision and explanation logic without requiring the full dataset.

## Recommendation Methods

### Collaborative Filtering

The primary recommender uses truncated SVD on a sparse user-anime ratings matrix. Each anime is represented as an item vector in the learned latent factor space. To recommend from one anime, the system computes cosine similarity between the selected anime vector and the other item vectors.

This captures patterns such as: users who liked one show often liked another, even when the two shows do not share obvious metadata.

### Content-Based Fallback

If an anime exists in the metadata but not in the SVD model, the system falls back to TF-IDF over genre metadata. It computes genre-vector similarity and recommends titles with similar content signals.

This helps with cold-start cases where a title has metadata but not enough ratings history.

### Watchlist Recommendations

For a watchlist, the system computes collaborative similarity from each valid input anime, averages candidate scores across the list, removes already-selected titles, and ranks the remaining candidates.

## Rule-Based Filtering

The recommender also applies explicit rules:

- remove the input title itself
- remove direct same-franchise sequels of the input
- deduplicate franchise seasons so one franchise does not dominate the list
- remove anime already in the user's watchlist

These rules make the output more useful as a decision system. Without them, a user who enters `Naruto` might receive mostly Naruto sequels instead of genuinely new recommendations.

## Explanation Design

Each recommendation includes a structured explanation:

- method used, such as SVD or TF-IDF
- numeric similarity score
- shared genre signals
- rule-based filters that affected the candidate set
- natural-language summary

Example explanation:

> You picked Naruto, which signals interest in Action and Adventure. This recommendation shares those signals and has a strong match strength of 98%.

The system also prints factor-level evidence, such as the input titles used for personalization, overlapping genres, the model score, and filtering rules that removed same-franchise sequels.

This makes the system interpretable at the level expected by the course: the user can see both the machine-learning signal and the symbolic decision logic.

## How To Run Locally

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
python train_model.py
uvicorn main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Python decision trace demo:

```bash
python3 backend/demo_decision_trace.py --query "Naruto"
python3 backend/demo_decision_trace.py --ids 20 5114 11061
python3 backend/demo_decision_trace.py --sample --query "Naruto"
```

The `--sample` option is the safest path for Zoo/Gradescope because it does not require the full local model or data files.

## How To Run The Zoo Bundle

Upload the contents of `zoo_submission/`, then run:

```bash
python3 demo_decision_trace.py --query "Naruto"
python3 demo_decision_trace.py --ids 20 5114 11061
```

The Zoo bundle uses compact sample data, so it demonstrates the automated decision system and explanation behavior without large files.

## Limitations

- The full collaborative model depends on large local data artifacts that are not suitable for normal GitHub upload.
- SVD factors are latent, so explanations describe similarity and shared metadata rather than exposing each hidden factor.
- Genre metadata can be sparse or noisy.
- Frontend images and descriptions come from the external Jikan API and are not required for grading.
- The sample Zoo bundle is intentionally small and demonstrates behavior rather than production-scale recommendation quality.

## Conclusion

The project is an explainable automated decision system because it does more than return ranked anime. It combines machine-learning scores, content signals, rule-based filtering, and natural-language reasoning so a user can understand why each recommendation was produced.
