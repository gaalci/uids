#!/usr/bin/env python3
import os, json, string
from collections import Counter

SNOW_DIR  = "snow"    # snow/ is at repo root level
OUT_DIR   = "indexes" # indexes/ should be created at repo root level

# We'll index by A-Z and 0-9. Digit files will be named '0.json' .. '9.json'.
DIGITS = [str(d) for d in range(10)]

# Popular tags output configuration
POPULAR_DIR = "popular"
POPULAR_TAG_FILE = "tag.json"
# Easy to change if you want more/less entries
POPULAR_TAG_LIMIT = 200

def load_users(path):
    """Return a list of (name, uid) tuples from snow/*.json."""
    pairs = []
    if not os.path.exists(path):
        print(f"Directory {path} does not exist!")
        return pairs
    
    files = os.listdir(path)
    print(f"Found {len(files)} files in {path}")
    
    for fname in files:
        if not fname.lower().endswith(".json"):
            continue
        uid = fname[:-5]  # strip ".json"
        full = os.path.join(path, fname)
        try:
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", "").strip()
            if name:
                pairs.append((name, uid))
        except Exception as e:
            print(f"Error processing {fname}: {e}")
            continue
    
    print(f"Loaded {len(pairs)} name-uid pairs")
    return pairs

def bucket_by_letter(pairs):
    """Return dict containing A-Z and 0-9 keys, e.g. { 'A': {...}, '0': {...} }.

    Names whose first character is a letter (A-Z) go to the corresponding
    uppercase bucket. Names starting with a digit 0-9 go to the corresponding
    digit bucket. Other leading characters are ignored.
    """
    buckets = {L: {} for L in string.ascii_uppercase}
    # add digit buckets
    for d in DIGITS:
        buckets[d] = {}

    for name, uid in pairs:
        if not name:
            continue
        first = name[0].upper()
        # if first is a digit (0-9) it will be in buckets as a string
        if first in buckets:
            buckets[first][name] = uid
    return buckets

def write_indexes(buckets):
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # Always write A-Z and 0-9 files, even if empty
    for letter in list(string.ascii_uppercase) + DIGITS:
        mapping = buckets.get(letter, {})  # Use empty dict if no names for this letter/digit
        out_path = os.path.join(OUT_DIR, f"{letter}.json")
        # Always overwrite so indexes stay in sync with source data
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    print(f"Wrote index files A-Z and 0-9 into '{OUT_DIR}/'")

def compute_popular_tags(path, limit=POPULAR_TAG_LIMIT):
    """Scan snow/*.json and return a list of up to `limit` most common tags.

    Tag extraction rules (supports both styles):
      - Aggregated field "tags":
          * If it's a list, counts each non-empty string item.
          * If it's a string, splits by comma and counts non-empty pieces.
      - Individual fields "tag1", "tag2", ... (case-insensitive key match):
          * Any key whose name starts with 'tag' and the suffix is digits is treated as a tag.
      - Tags are normalized to lowercase for counting (case-insensitive).
    Ordering: most frequent first; ties broken alphabetically.
    Returns: list[str]
    """
    counter = Counter()
    if not os.path.exists(path):
        print(f"Directory {path} does not exist! Skipping popular tags.")
        return []

    files = [f for f in os.listdir(path) if f.lower().endswith('.json')]
    for fname in files:
        full = os.path.join(path, fname)
        try:
            with open(full, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {fname} for tags: {e}")
            continue

        # Collect tags from 'tags' field (list or comma-separated string)
        tags_field = data.get("tags", [])
        items = []
        if isinstance(tags_field, list):
            items.extend(t for t in tags_field if isinstance(t, str))
        elif isinstance(tags_field, str):
            items.extend(p.strip() for p in tags_field.split(','))

        # Also collect tags from keys like tag1, tag2, ... (case-insensitive)
        for k, v in data.items():
            if not isinstance(v, str):
                continue
            kl = str(k).lower()
            if kl.startswith('tag') and kl[3:].isdigit():
                items.append(v)

        for t in items:
            t_norm = t.strip().lower()
            if t_norm:
                counter[t_norm] += 1

    if not counter:
        return []

    # Sort by frequency desc, then tag name asc for stable order across runs
    items_sorted = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    top = [tag for tag, _cnt in items_sorted[: max(0, int(limit))]]
    return top

def write_popular_tags(tags):
    """Write the provided tag list to popular/tag.json as a JSON array."""
    os.makedirs(POPULAR_DIR, exist_ok=True)
    out_path = os.path.join(POPULAR_DIR, POPULAR_TAG_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tags, f, ensure_ascii=False, indent=2)
    print(f"Wrote top {len(tags)} tags into '{out_path}'")

if __name__ == "__main__":
    pairs   = load_users(SNOW_DIR)
    buckets = bucket_by_letter(pairs)
    write_indexes(buckets)
    # Also compute and write popular tags
    popular_tags = compute_popular_tags(SNOW_DIR, POPULAR_TAG_LIMIT)
    write_popular_tags(popular_tags)
