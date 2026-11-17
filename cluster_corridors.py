
from pathlib import Path

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BUSINESS_FILE = DATA_DIR / "business_locations.csv"
ROAD_FILE = DATA_DIR / "roads.geojson"

# Check that the required files exist
if not BUSINESS_FILE.exists():
    raise FileNotFoundError(
        "business_locations.csv not found in the data folder."
    )

if not ROAD_FILE.exists():
    raise FileNotFoundError(
        "roads.geojson not found in the data folder."
    )

# Load business data
businesses = pd.read_csv(BUSINESS_FILE)

# Remove records without coordinates
businesses = businesses.dropna(
    subset=["latitude", "longitude"]
).copy()

# Convert business locations into a geographic data frame
gdf = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"],
        businesses["latitude"]
    ),
    crs="EPSG:4326"
)

# Convert coordinates to metres for DBSCAN
gdf = gdf.to_crs(gdf.estimate_utm_crs())

# DBSCAN settings
EPS_METRES = 100
MIN_SAMPLES = 5

# Use projected coordinates
coordinates = pd.DataFrame({
    "x": gdf.geometry.x,
    "y": gdf.geometry.y
}).to_numpy()

# Identify dense groups of businesses
model = DBSCAN(
    eps=EPS_METRES,
    min_samples=MIN_SAMPLES
)

gdf["cluster"] = model.fit_predict(coordinates)

# -1 means the business is not part of a detected cluster
cluster_count = len(
    set(gdf["cluster"]) - {-1}
)

noise_count = int((gdf["cluster"] == -1).sum())

# Save results
results = gdf.drop(columns="geometry").copy()
results.to_csv(
    DATA_DIR / "business_clusters.csv",
    index=False
)

# Load road network and convert it to the same CRS
roads = gpd.read_file(ROAD_FILE)
roads = roads.to_crs(gdf.crs)

# Plot the corridor map
fig, ax = plt.subplots(figsize=(12, 10))

roads.plot(
    ax=ax,
    color="lightgray",
    linewidth=0.7
)

clustered = gdf[gdf["cluster"] != -1]
noise = gdf[gdf["cluster"] == -1]

if not clustered.empty:
    clustered.plot(
        ax=ax,
        column="cluster",
        categorical=True,
        legend=True,
        markersize=30,
        alpha=0.9
    )

if not noise.empty:
    noise.plot(
        ax=ax,
        color="black",
        markersize=12,
        alpha=0.5,
        label="Unclustered businesses"
    )

ax.set_title(
    "SoCo, Austin: Business Clusters Identified by DBSCAN"
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.legend(loc="best")

plt.tight_layout()

map_file = DATA_DIR / "soco_corridor_clusters.png"
plt.savefig(map_file, dpi=300, bbox_inches="tight")
plt.show()

print("\n===== SOCО CORRIDOR ANALYSIS =====")
print("Total businesses:", len(gdf))
print("Detected clusters:", cluster_count)
print("Unclustered businesses:", noise_count)
print("Clustered business records:", len(clustered))
print("Results saved to:", DATA_DIR / "business_clusters.csv")
print("Map saved to:", map_file)
