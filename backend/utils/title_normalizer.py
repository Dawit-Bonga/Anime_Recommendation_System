import re

def normalize_title(title):
    """Remove season indicators and sequel markers to get base title."""
    if not title:
        return ""
    
    title_lower = title.lower()
    patterns = [
        r'\s*season\s+\d+',           # "Season 2"
        r'\s*\d+\s*season',           # "2 Season"
        r'\s*\d+nd\s*season',         # "2nd Season"
        r'\s*\d+rd\s*season',         # "3rd Season"
        r'\s*\d+th\s*season',         # "4th Season"
        r'\s*final\s*season',         # "Final Season"
        r'\s*part\s+\d+',             # "Part 2"
        r'\s*\d+$',                   # Trailing numbers "2", "3"
        r'\s*:\s*the\s+final\s+season', # ": The Final Season"
        # NEW: Handle sequel markers
        r'\s*:\s*shippuden',          # ": Shippuden"
        r'\s*:\s*brotherhood',        # ": Brotherhood"
        r'\s*:\s*next\s+generations', # ": Next Generations"
        r'\s*shippuden',              # "Shippuden" (standalone)
        r'\s*brotherhood',            # "Brotherhood" (standalone)
        r'\s*:\s*[^:]+$',            # ": Anything" at the end (catch-all for sequels)
    ]
    
    normalized = title_lower
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    # Remove colons and extra spaces
    normalized = normalized.replace(':', '')
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized