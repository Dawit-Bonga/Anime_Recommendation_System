import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from data_loader import initialize_all
from services.content_based_service import build_tfidf_index
from services.recommendation_service import recommend_batch, recommend_hybrid
from services.search_service import search_anime


SAMPLE_METADATA = {
    20: {
        "title": "Naruto",
        "title_japanese": "Naruto",
        "genre": "Action, Adventure, Comedy, Super Power",
    },
    21: {
        "title": "One Piece",
        "title_japanese": "One Piece",
        "genre": "Action, Adventure, Comedy, Fantasy",
    },
    1535: {
        "title": "Death Note",
        "title_japanese": "Death Note",
        "genre": "Mystery, Psychological, Supernatural, Thriller",
    },
    16498: {
        "title": "Attack on Titan",
        "title_japanese": "Shingeki no Kyojin",
        "genre": "Action, Drama, Fantasy, Mystery",
    },
    5114: {
        "title": "Fullmetal Alchemist: Brotherhood",
        "title_japanese": "Hagane no Renkinjutsushi: Fullmetal Alchemist",
        "genre": "Action, Adventure, Drama, Fantasy",
    },
    11061: {
        "title": "Hunter x Hunter (2011)",
        "title_japanese": "Hunter x Hunter (2011)",
        "genre": "Action, Adventure, Fantasy, Shounen",
    },
    9253: {
        "title": "Steins;Gate",
        "title_japanese": "Steins;Gate",
        "genre": "Drama, Sci-Fi, Suspense",
    },
    1575: {
        "title": "Code Geass: Lelouch of the Rebellion",
        "title_japanese": "Code Geass: Hangyaku no Lelouch",
        "genre": "Action, Drama, Mecha, Sci-Fi",
    },
}


SAMPLE_VECTORS = np.array(
    [
        [0.95, 0.92, 0.16, 0.32, 0.72],
        [0.91, 0.94, 0.18, 0.27, 0.76],
        [0.08, 0.12, 0.97, 0.86, 0.24],
        [0.64, 0.46, 0.58, 0.74, 0.42],
        [0.79, 0.73, 0.31, 0.55, 0.86],
        [0.88, 0.9, 0.22, 0.35, 0.82],
        [0.14, 0.18, 0.82, 0.92, 0.36],
        [0.48, 0.34, 0.62, 0.89, 0.41],
    ],
    dtype=float,
)


def build_sample_objects():
    anime_ids = list(SAMPLE_METADATA.keys())
    vectorizer, tfidf_matrix, tfidf_anime_ids = build_tfidf_index(SAMPLE_METADATA)
    return {
        "metadata": SAMPLE_METADATA,
        "search_index_english": {
            meta["title"].lower(): anime_id for anime_id, meta in SAMPLE_METADATA.items()
        },
        "search_index_japanese": {
            meta["title_japanese"].lower(): anime_id
            for anime_id, meta in SAMPLE_METADATA.items()
        },
        "anime_id_to_idx": {anime_id: idx for idx, anime_id in enumerate(anime_ids)},
        "idx_to_anime_id": {idx: anime_id for idx, anime_id in enumerate(anime_ids)},
        "item_vectors": SAMPLE_VECTORS,
        "tfidf_vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "tfidf_anime_ids": tfidf_anime_ids,
    }


def load_objects(use_sample):
    if use_sample:
        print("Using bundled sample data for a Zoo-friendly demo.\n")
        return build_sample_objects()

    try:
        return initialize_all()
    except Exception as exc:
        print(f"Could not load full local assets: {exc}")
        print("Falling back to bundled sample data for the demo.\n")
        return build_sample_objects()


def resolve_query(query, objects):
    results = search_anime(query, objects, limit=1).get("results", [])
    if not results:
        raise ValueError(f'No anime found for query "{query}"')
    return results[0]


def print_trace(title, response):
    print(title)
    print("=" * len(title))
    print(response.get("message", "Recommendation trace"))
    print()

    for rank, rec in enumerate(response.get("recommendations", []), start=1):
        explanation = rec.get("explanation", {})
        shared_genres = rec.get("shared_genres") or []
        filters = rec.get("filters_applied") or []

        print(f"{rank}. {rec.get('title')} ({rec.get('method_label', rec.get('method'))})")
        print(f"   Score: {rec.get('score', 0):.3f}")
        print(f"   Why: {explanation.get('summary', 'No explanation available.')}")
        for factor in explanation.get("factors", [])[:4]:
            print(f"   - {factor}")
        print(f"   Shared genres: {', '.join(shared_genres) if shared_genres else 'None'}")
        print(f"   Rules: {', '.join(filters) if filters else 'None'}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Print explainable anime recommendation decision traces."
    )
    parser.add_argument("--query", help='Anime title query, such as "Naruto"')
    parser.add_argument("--ids", nargs="+", type=int, help="Anime IDs for watchlist mode")
    parser.add_argument("--limit", type=int, default=5, help="Number of recommendations")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use the small bundled sample data instead of full local assets",
    )
    args = parser.parse_args()

    if not args.query and not args.ids:
        parser.error("Provide either --query or --ids")

    objects = load_objects(args.sample)

    if args.query:
        selected = resolve_query(args.query, objects)
        response = recommend_hybrid(selected["id"], objects, limit=args.limit)
        print_trace(f"Recommendations for {selected['title']}", response)
        return

    response = recommend_batch(args.ids, objects, limit=args.limit)
    print_trace(f"Recommendations for watchlist IDs: {', '.join(map(str, args.ids))}", response)


if __name__ == "__main__":
    main()
