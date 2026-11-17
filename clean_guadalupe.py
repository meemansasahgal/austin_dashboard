#!/usr/bin/env python3
"""Screen a Guadalupe Street (The Drag) business CSV against an approximate geographic window.
Usage: python clean_guadalupe.py guadalupe_raw.csv
Creates guadalupe_businesses_cleaned.csv and guadalupe_businesses_review.csv.
This is a screening pass, not exact road-geometry verification.
"""
import sys
from pathlib import Path
from math import radians, sin, cos, asin, sqrt
import pandas as pd

LAT_MIN, LAT_MAX = 30.2815, 30.2945
LON_MIN, LON_MAX = -97.7442, -97.7395
if len(sys.argv) < 2:
    raise SystemExit("Usage: python clean_guadalupe.py guadalupe_raw.csv")
source = Path(sys.argv[1])
df = pd.read_csv(source)
required = {"name", "category", "latitude", "longitude"}
missing = required - set(df.columns)
if missing:
    raise SystemExit(f"Missing required columns: {', '.join(sorted(missing))}")
df["name"] = df["name"].fillna("").astype(str).str.strip()
df["category"] = df["category"].fillna("").astype(str).str.strip().str.lower()
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
valid_coords = df["latitude"].between(-90, 90) & df["longitude"].between(-180, 180) & df["latitude"].notna() & df["longitude"].notna()
inside = df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
has_name = df["name"].ne("")
keep = valid_coords & inside & has_name
review = df.loc[~keep].copy()
def reason(row):
    if not row["name"]: return "missing business name"
    if pd.isna(row["latitude"]) or pd.isna(row["longitude"]): return "missing/invalid coordinates"
    if not (LAT_MIN <= row["latitude"] <= LAT_MAX and LON_MIN <= row["longitude"] <= LON_MAX): return "outside approximate The Drag screening window"
    return "needs manual review"
review["review_reason"] = review.apply(reason, axis=1)
clean = df.loc[keep].copy()
clean["_name_key"] = clean["name"].str.casefold().str.replace(r"[^a-z0-9]+", "", regex=True)
clean = clean.drop_duplicates(subset=["_name_key", "category", "latitude", "longitude"])
kept = []
possible_dupes = []
for _, row in clean.iterrows():
    dup = False
    for prior in kept:
        if row["_name_key"] != prior["_name_key"]: continue
        lat1, lon1, lat2, lon2 = map(radians, [row["latitude"], row["longitude"], prior["latitude"], prior["longitude"]])
        a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
        metres = 6371000 * 2 * asin(sqrt(a))
        if metres <= 25:
            item = row.to_dict(); item["review_reason"] = f"possible same-name duplicate within {metres:.1f} m"
            possible_dupes.append(item); dup = True; break
    if not dup: kept.append(row)
clean = pd.DataFrame(kept).drop(columns=["_name_key"], errors="ignore")
clean["corridor"] = "Guadalupe Street (The Drag)"
clean = clean.drop(columns=["cluster", "nearest_business_m"], errors="ignore")
if possible_dupes: review = pd.concat([review, pd.DataFrame(possible_dupes)], ignore_index=True)
out = source.with_name("guadalupe_businesses_cleaned.csv")
rev = source.with_name("guadalupe_businesses_review.csv")
clean.to_csv(out, index=False); review.to_csv(rev, index=False)
print(f"Input rows: {len(df)} | retained: {len(clean)} | review/excluded: {len(review)}")
print("\nRetained category counts:\n" + clean["category"].value_counts().to_string())
print(f"\nCreated: {out}\nCreated: {rev}")
print("NOTE: this approximate coordinate screen must be checked against actual Guadalupe Street road geometry before calling the result fully verified.")
