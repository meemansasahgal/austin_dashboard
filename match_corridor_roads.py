
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

businesses = pd.read_csv(DATA_DIR / "business_clusters.csv")
rankings = pd.read_csv(DATA_DIR / "ranked_corridors.csv")
roads = gpd.read_file(DATA_DIR / "roads.geojson")


# Convert unusual values, including arrays, into safe text
def safe_text(value):
    if value is None:
        return ""

    if isinstance(value, (list, tuple, np.ndarray)):
        items = np.asarray(value, dtype=object).ravel().tolist()
        return ", ".join(
            text for item in items
            if (text := safe_text(item))
        )

    if isinstance(value, dict):
        return str(value)

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


businesses = businesses.dropna(
    subset=["latitude", "longitude", "cluster"]
).copy()

businesses["cluster"] = businesses["cluster"].astype(int)

top_clusters = (
    rankings.sort_values("rank")
    .head(5)["cluster"]
    .astype(int)
    .tolist()
)

businesses = businesses[
    businesses["cluster"].isin(top_clusters)
].copy()

points = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"],
        businesses["latitude"]
    ),
    crs="EPSG:4326"
)

metric_crs = points.estimate_utm_crs()
points = points.to_crs(metric_crs)
roads = roads.to_crs(metric_crs)

if "name" not in roads.columns:
    roads["name"] = ""

# Make road names safe scalar strings before grouping
roads["road_name"] = roads["name"].map(safe_text)

named_roads = roads[
    roads["road_name"].ne("")
].copy()

if named_roads.empty:
    print("No named roads found in roads.geojson.")
    print("Check whether the road data contains a 'name' field.")
    raise SystemExit

matches = []

for cluster_id in top_clusters:
    cluster_points = points[
        points["cluster"] == cluster_id
    ]

    for _, business in cluster_points.iterrows():
        distances = named_roads.geometry.distance(
            business.geometry
        )

        nearest_index = distances.idxmin()
        road = named_roads.loc[nearest_index]

        matches.append({
            "cluster": cluster_id,
            "business_name": safe_text(
                business.get("name", "")
            ),
            "category": safe_text(
                business.get("category", "")
            ),
            "nearest_road": road["road_name"],
            "distance_to_road_m": round(
                float(distances.loc[nearest_index]), 2
            )
        })

matches_df = pd.DataFrame(matches)

summary = (
    matches_df.groupby(
        ["cluster", "nearest_road"],
        dropna=False
    )
    .size()
    .reset_index(name="businesses_near_road")
    .sort_values(
        ["cluster", "businesses_near_road"],
        ascending=[True, False]
    )
)

matches_df.to_csv(
    DATA_DIR / "business_road_matches.csv",
    index=False
)

summary.to_csv(
    DATA_DIR / "cluster_road_summary.csv",
    index=False
)

print("\n===== TOP ROAD NAMES BY CLUSTER =====")

for cluster_id in top_clusters:
    print(f"\nCluster {cluster_id}:")

    result = summary[
        summary["cluster"] == cluster_id
    ].head(5)

    if result.empty:
        print("No road matches found.")
    else:
        print(result.to_string(index=False))

print("\nSUCCESS!")
print("Detailed matches:", DATA_DIR / "business_road_matches.csv")
print("Road summary:", DATA_DIR / "cluster_road_summary.csv")

