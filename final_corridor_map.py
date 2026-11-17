
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

business_file = DATA_DIR / "business_clusters.csv"
roads_file = DATA_DIR / "roads.geojson"

businesses = pd.read_csv(business_file)
roads = gpd.read_file(roads_file)

businesses = businesses.dropna(
    subset=["latitude", "longitude", "cluster"]
).copy()

businesses["cluster"] = businesses["cluster"].astype(int)

# Convert both datasets to the same projected coordinate system
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

# Calculate cluster sizes
cluster_sizes = (
    points[points["cluster"] != -1]
    .groupby("cluster")
    .size()
)

fig, ax = plt.subplots(figsize=(13, 10))

roads.plot(
    ax=ax,
    color="lightgray",
    linewidth=0.8,
    zorder=1
)

# Show unclustered businesses in grey
noise = points[points["cluster"] == -1]

if not noise.empty:
    noise.plot(
        ax=ax,
        color="gray",
        markersize=12,
        alpha=0.5,
        label="Unclustered businesses",
        zorder=2
    )

# Plot clusters, largest first
for cluster_id, count in cluster_sizes.sort_values(
    ascending=False
).items():
    group = points[points["cluster"] == cluster_id]

    group.plot(
        ax=ax,
        markersize=18 + min(count, 30),
        alpha=0.85,
        label=f"Cluster {cluster_id}: {count} businesses",
        zorder=3
    )

ax.set_title(
    "SoCo, Austin: Commercial Business Clusters",
    fontsize=15
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.legend(
    title="Business clusters",
    loc="upper left",
    bbox_to_anchor=(1.02, 1),
    fontsize=8
)

plt.tight_layout()

output_file = DATA_DIR / "final_corridor_map.png"
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()

print("Final map saved to:", output_file)
print("\nCluster sizes:")
print(cluster_sizes.sort_values(ascending=False))

