import ast
import math


def parse_genres(raw_genres):
    """Return a clean list of genre labels from CSV/list/string metadata."""
    if raw_genres is None:
        return []

    if isinstance(raw_genres, float) and math.isnan(raw_genres):
        return []

    if isinstance(raw_genres, (list, tuple, set)):
        return [str(genre).strip() for genre in raw_genres if str(genre).strip()]

    genre_text = str(raw_genres).strip()
    if not genre_text or genre_text.lower() in {"unknown", "nan"}:
        return []

    try:
        parsed = ast.literal_eval(genre_text)
        if isinstance(parsed, (list, tuple, set)):
            return [str(genre).strip() for genre in parsed if str(genre).strip()]
    except (ValueError, SyntaxError):
        pass

    genre_text = genre_text.replace("[", "").replace("]", "").replace("'", "")
    return [genre.strip() for genre in genre_text.split(",") if genre.strip()]


def get_shared_genres(input_metas, rec_meta):
    input_genres = set()
    for meta in input_metas:
        input_genres.update(parse_genres(meta.get("genre")))

    rec_genres = set(parse_genres(rec_meta.get("genre")))
    return sorted(input_genres.intersection(rec_genres))


def format_title_list(titles):
    if not titles:
        return "your picks"
    if len(titles) == 1:
        return titles[0]
    if len(titles) == 2:
        return f"{titles[0]} and {titles[1]}"
    return f"{', '.join(titles[:-1])}, and {titles[-1]}"


def build_recommendation_record(
    rec_id,
    rec_meta,
    score,
    method,
    input_metas,
    filters_applied=None,
    source_titles=None,
):
    filters_applied = filters_applied or []
    source_titles = source_titles or [
        meta.get("title", "the selected anime") for meta in input_metas if meta
    ]
    shared_genres = get_shared_genres(input_metas, rec_meta)
    title = rec_meta.get("title", f"Anime #{rec_id}")
    score = float(score)

    method_labels = {
        "collaborative": "Collaborative filtering (SVD)",
        "content_based": "Content-based filtering (TF-IDF)",
        "batch_collaborative": "Watchlist collaborative filtering",
    }

    if method == "content_based":
        score_evidence = f"TF-IDF genre similarity score: {score:.3f}"
    elif method == "batch_collaborative":
        score_evidence = f"Average SVD similarity across watchlist items: {score:.3f}"
    else:
        score_evidence = f"SVD item-vector cosine similarity score: {score:.3f}"

    evidence = [score_evidence]
    if shared_genres:
        evidence.append(f"Shared genre signals: {', '.join(shared_genres[:5])}")
    else:
        evidence.append("No direct shared genre signal was required for this recommendation")

    for filter_name in filters_applied:
        evidence.append(f"Rule applied: {filter_name}")

    display_titles = source_titles[:2]
    source_text = format_title_list(display_titles)

    if shared_genres:
        summary = f"Fans of {source_text} also tend to enjoy this. Genres in common: {', '.join(shared_genres[:3])}."
    else:
        summary = f"Fans of {source_text} also tend to enjoy this."

    return {
        "id": int(rec_id),
        "title": title,
        "genre": rec_meta.get("genre", "Unknown"),
        "score": score,
        "img_url": None,
        "method": method,
        "method_label": method_labels.get(method, method),
        "shared_genres": shared_genres,
        "filters_applied": filters_applied,
        "evidence": evidence,
        "explanation": {
            "summary": summary,
            "source_titles": source_titles[:5],
        },
    }
