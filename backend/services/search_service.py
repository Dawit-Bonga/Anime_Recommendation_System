def search_anime(query: str, objects: dict, limit: int = 5):
    """Search anime by English/Japanese title."""
    query = query.lower().strip()
    if not query:
        return {"results": []}
    
    results = []
    seen_ids = set()
    
    # Step 1: Search English titles first (priority)
    exact_matches = []
    partial_matches = []
    
    for title, uid in objects.get('search_index_english', {}).items():
        if uid in seen_ids:
            continue
        if title == query:
            exact_matches.append((title, uid))
        elif query in title:
            partial_matches.append((title, uid))
    
    # Add exact matches first
    for title, uid in exact_matches:
        meta = objects['metadata'][uid]
        if meta:
            results.append({
                "id": uid,
                "title": meta['title'],
                "img_url": None
            })
            seen_ids.add(uid)
        if len(results) >= limit:
            break
    
    # Then add partial matches
    if len(results) < limit:
        for title, uid in partial_matches:
            if uid not in seen_ids:
                meta = objects['metadata'][uid]
                if meta:
                    results.append({
                        "id": uid,
                        "title": meta['title'],
                        "img_url": None
                    })
                    seen_ids.add(uid)
                if len(results) >= limit:
                    break
    
    # Step 2: If we don't have enough results, search Japanese titles
    if len(results) < limit:
        japanese_exact = []
        japanese_partial = []
        
        for title, uid in objects.get('search_index_japanese', {}).items():
            if uid in seen_ids:
                continue
            if title == query:
                japanese_exact.append((title, uid))
            elif query in title:
                japanese_partial.append((title, uid))
        
        # Add exact Japanese matches
        for title, uid in japanese_exact:
            if uid not in seen_ids:
                meta = objects['metadata'][uid]
                if meta:
                    results.append({
                        "id": uid,
                        "title": meta['title'],
                        "img_url": None
                    })
                    seen_ids.add(uid)
                if len(results) >= limit:
                    break
        
        # Then partial Japanese matches
        if len(results) < limit:
            for title, uid in japanese_partial:
                if uid not in seen_ids:
                    meta = objects['metadata'][uid]
                    if meta:
                        results.append({
                            "id": uid,
                            "title": meta['title'],
                            "img_url": None
                        })
                        seen_ids.add(uid)
                    if len(results) >= limit:
                        break
    
    return {"results": results}