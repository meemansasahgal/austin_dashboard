
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

businesses = pd.read_csv(DATA_DIR / "business_clusters.csv")
rankings = pd.read_csv(DATA_DIR / "ranked_corridors.csv")
roads = gpd.read_file(DATA_DIR / "roads.geojson")
road_summary = pd.read_csv(DATA_DIR / "cluster_road_summary.csv")

# Select the top five clusters
top = rankings.sort_values("rank").head(5).copy()
top_ids = top["cluster"].astype(int).tolist()

businesses = businesses.dropna(
    subset=["latitude", "longitude", "cluster"]
).copy()
businesses["cluster"] = businesses["cluster"].astype(int)

points = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"], businesses["latitude"]
    ),
    crs="EPSG:4326"
)

metric_crs = points.estimate_utm_crs()
points = points.to_crs(metric_crs)
roads = roads.to_crs(metric_crs)

fig, ax = plt.subplots(figsize=(14, 10))

# Draw roads in the background
roads.plot(
    ax=ax,
    color="lightgray",
    linewidth=0.7,
    zorder=1
)

# Plot the top five clusters
for _, row in top.iterrows():
    cluster_id = int(row["cluster"])
    group = points[points["cluster"] == cluster_id]

    group.plot(
        ax=ax,
        markersize=24,
        alpha=0.85,
        label=(
            f"Cluster {cluster_id} "
            f"({int(row['business_count'])} businesses)"
        ),
        zorder=3
    )

    # Mark the approximate cluster centre
    cx = group.geometry.x.mean()
    cy = group.geometry.y.mean()

    ax.annotate(
        f"C{cluster_id}",
        (cx, cy),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold"
    )

ax.set_title(
    "SoCo, Austin: Top Candidate Commercial Clusters",
    fontsize=15
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.legend(
    title="Ranked clusters",
    loc="upper left",
    bbox_to_anchor=(1.02, 1)
)

plt.tight_layout()

map_path = DATA_DIR / "top_corridors_map.png"
plt.savefig(map_path, dpi=300, bbox_inches="tight")
plt.show()

# Print road-name evidence separately
print("\n===== ROAD NAME EVIDENCE =====")

for cluster_id in top_ids:
    print(f"\nCluster {cluster_id}:")

    rows = road_summary[
        road_summary["cluster"] == cluster_id
    ].head(3)

    if rows.empty:
        print("No named-road matches.")
    else:
        print(rows[
            ["nearest_road", "businesses_near_road"]
        ].to_string(index=False))

print("\nMap saved to:", map_path)

