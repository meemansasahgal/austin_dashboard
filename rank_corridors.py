
from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

business_file = DATA_DIR / "business_clusters.csv"
roads_file = DATA_DIR / "roads.geojson"

df = pd.read_csv(business_file)
df = df.dropna(subset=["latitude", "longitude", "cluster"]).copy()
df["cluster"] = df["cluster"].astype(int)

# Ignore DBSCAN noise points
df = df[df["cluster"] != -1].copy()

if df.empty:
    raise ValueError("No clusters found. Check your DBSCAN results.")

# Business count and category diversity
summary = df.groupby("cluster").agg(
    business_count=("cluster", "size"),
    category_count=("category", "nunique"),
    latitude=("latitude", "mean"),
    longitude=("longitude", "mean")
).reset_index()

# Measure distance from each cluster centre to the nearest road
points = gpd.GeoDataFrame(
    summary,
    geometry=gpd.points_from_xy(
        summary["longitude"], summary["latitude"]
    ),
    crs="EPSG:4326"
)

roads = gpd.read_file(roads_file)

metric_crs = points.estimate_utm_crs()
points = points.to_crs(metric_crs)
roads = roads.to_crs(metric_crs)

road_union = roads.geometry.union_all()

points["nearest_road_distance_m"] = (
    points.geometry.distance(road_union)
)

# Normalize metrics so they can be combined
def normalize(series):
    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(1.0, index=series.index)

    return (series - minimum) / (maximum - minimum)

points["density_score"] = normalize(points["business_count"])
points["diversity_score"] = normalize(points["category_count"])

# Smaller road distance is better
points["road_score"] = 1 - normalize(
    points["nearest_road_distance_m"]
)

# Combined score out of 100
points["corridor_score"] = 100 * (
    0.50 * points["density_score"]
    + 0.30 * points["diversity_score"]
    + 0.20 * points["road_score"]
)

points["rank"] = (
    points["corridor_score"]
    .rank(method="min", ascending=False)
    .astype(int)
)

result = points.drop(columns="geometry").sort_values("rank")

result.to_csv(DATA_DIR / "ranked_corridors.csv", index=False)

print("\n===== RANKED SOCO BUSINESS CLUSTERS =====")
print(result[
    [
        "rank", "cluster", "business_count",
        "category_count", "nearest_road_distance_m",
        "corridor_score"
    ]
].round(2).to_string(index=False))

print("\nSaved to:", DATA_DIR / "ranked_corridors.csv")

