#!/usr/bin/env python3
import os, json, string

SNOW_DIR  = "../snow"  # Go up one level from scripts/ to find snow/
OUT_DIR   = "../indexes"  # Go up one level from scripts/ to put indexes/ in root

def load_users(path):
    """Return a list of (name, uid) tuples from snow/*.json."""
    pairs = []
    for fname in os.listdir(path):
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
        except Exception:
            # skip invalid or non-JSON files
            continue
    return pairs

def bucket_by_letter(pairs):
    """Return dict: { 'A': {name:uid,...}, ..., 'Z': {...} }"""
    buckets = {L: {} for L in string.ascii_uppercase}
    for name, uid in pairs:
        first = name[0].upper()
        if first in buckets:
            buckets[first][name] = uid
    return buckets

def write_indexes(buckets):
    os.makedirs(OUT_DIR, exist_ok=True)
    for letter, mapping in buckets.items():
        out_path = os.path.join(OUT_DIR, f"{letter}.json")
        # Always overwrite so indexes stay in sync with source data
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(buckets)} index files into ‘{OUT_DIR}/’")

if __name__ == "__main__":
    pairs   = load_users(SNOW_DIR)
    buckets = bucket_by_letter(pairs)
    write_indexes(buckets)
