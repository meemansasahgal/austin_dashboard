
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors

# Project paths
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "soco_corridor_businesses.csv"
OUTPUT_DIR = BASE_DIR / "data"
OUTPUT_DIR.mkdir(exist_ok=True)

# DBSCAN settings
EARTH_RADIUS_M = 6_371_000
EPS_METRES = 100
MIN_SAMPLES = 5

# 1. Load business data
df = pd.read_csv(DATA_FILE)
df = df.dropna(subset=["latitude", "longitude"]).copy()

# Convert latitude/longitude to radians for distance calculations
coords_rad = np.radians(df[["latitude", "longitude"]].to_numpy())

# 2. Run DBSCAN using actual geographical distances
model = DBSCAN(
    eps=EPS_METRES / EARTH_RADIUS_M,
    min_samples=MIN_SAMPLES,
    metric="haversine",
    algorithm="ball_tree"
)

df["cluster"] = model.fit_predict(coords_rad)

# 3. Calculate distance to the nearest other business
if len(df) > 1:
    neighbours = NearestNeighbors(
        n_neighbors=2,
        metric="haversine",
        algorithm="ball_tree"
    )
    neighbours.fit(coords_rad)
    distances, _ = neighbours.kneighbors(coords_rad)
    df["nearest_business_m"] = distances[:, 1] * EARTH_RADIUS_M
else:
    df["nearest_business_m"] = np.nan

# 4. Summarise clusters
cluster_rows = []

for cluster_id in sorted(df["cluster"].unique()):
    group = df[df["cluster"] == cluster_id]

    cluster_rows.append({
        "cluster": int(cluster_id),
        "type": "Noise / isolated" if cluster_id == -1 else "Cluster",
        "business_records": len(group),
        "average_nearest_business_m":
            round(group["nearest_business_m"].mean(), 2),
        "business_categories":
            ", ".join(sorted(group["category"].dropna().unique()))
    })

summary = pd.DataFrame(cluster_rows)

# 5. Save results
df.to_csv(OUTPUT_DIR / "soco_business_clusters.csv", index=False)
summary.to_csv(OUTPUT_DIR / "soco_cluster_summary.csv", index=False)

# 6. Print findings
number_of_clusters = df.loc[df["cluster"] != -1, "cluster"].nunique()
noise_count = int((df["cluster"] == -1).sum())

print("\n=== SOCO BUSINESS CLUSTER ANALYSIS ===")
print("Business records analysed:", len(df))
print("Clusters detected:", number_of_clusters)
print("Businesses labelled noise:", noise_count)
print("Mean nearest-business distance (m):",
      round(df["nearest_business_m"].mean(), 2))
print("Median nearest-business distance (m):",
      round(df["nearest_business_m"].median(), 2))

print("\nCluster summary:")
print(summary.to_string(index=False))

# 7. Draw cluster map
fig, ax = plt.subplots(figsize=(10, 8))

cluster_ids = sorted(df["cluster"].unique())
colors = plt.cm.tab10(np.linspace(0, 1, max(len(cluster_ids), 1)))

for color, cluster_id in zip(colors, cluster_ids):
    group = df[df["cluster"] == cluster_id]

    if cluster_id == -1:
        ax.scatter(
            group["longitude"], group["latitude"],
            color="gray", marker="x", s=65,
            label="Noise / isolated"
        )
    else:
        ax.scatter(
            group["longitude"], group["latitude"],
            color=color, s=65,
            label=f"Cluster {cluster_id}"
        )

ax.set_title("SoCo Business Clusters (DBSCAN)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()

map_file = OUTPUT_DIR / "soco_business_clusters.png"
plt.savefig(map_file, dpi=200)
plt.close()

print("\nFiles created:")
print(OUTPUT_DIR / "soco_business_clusters.csv")
print(OUTPUT_DIR / "soco_cluster_summary.csv")
print(map_file)
