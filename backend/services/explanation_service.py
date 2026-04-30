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


def score_to_confidence(score):
    percent = round(max(0.0, min(float(score), 1.0)) * 100)
    if percent >= 80:
        label = "Strong"
    elif percent >= 60:
        label = "Moderate"
    else:
        label = "Exploratory"
    return percent, label


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
    confidence_percent, confidence_label = score_to_confidence(score)

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
    genre_text = ", ".join(shared_genres[:3]) if shared_genres else "latent taste patterns"
    full_source_text = format_title_list(source_titles[:3])

    if shared_genres:
        summary = (
            f"You picked {source_text}, which signals interest in {genre_text}. "
            f"This recommendation shares those signals and has a "
            f"{confidence_label.lower()} match strength of {confidence_percent}%."
        )
        similarity_detail = (
            f"This title overlaps with your input on {', '.join(shared_genres[:5])}, "
            "so it matches visible content signals as well as the model score."
        )
    else:
        summary = (
            f"You picked {source_text}. This recommendation is connected through similar "
            f"user taste patterns and has a {confidence_label.lower()} match "
            f"strength of {confidence_percent}%."
        )
        similarity_detail = (
            "The match is based mainly on collaborative-filtering patterns rather than direct genre overlap."
        )

    personalization_detail = (
        f"The recommendation is personalized from your input: {full_source_text}."
    )
    confidence_detail = (
        f"{confidence_label} match: {confidence_percent}% similarity signal from "
        f"{method_labels.get(method, method)}."
    )
    factor_bullets = [
        personalization_detail,
        similarity_detail,
        confidence_detail,
    ]
    if filters_applied:
        factor_bullets.append(f"Decision rules applied: {', '.join(filters_applied[:2])}.")

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
            "personalization": personalization_detail,
            "similarity": similarity_detail,
            "confidence": confidence_detail,
            "confidence_percent": confidence_percent,
            "confidence_label": confidence_label,
            "factors": factor_bullets,
            "source_titles": source_titles[:5],
        },
    }
