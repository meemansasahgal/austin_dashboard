
from pathlib import Path
import ast

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ==================================================
# SOCO CORRIDOR PROJECT - FINAL MAP
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

BUSINESS_FILE = DATA_DIR / "business_clusters.csv"
ROAD_FILE = DATA_DIR / "roads.geojson"
OUTPUT_FILE = DATA_DIR / "final_corridor_map.png"


# ==================================================
# 1. LOAD EXISTING DATA
# ==================================================

print("\nLoading SoCo project data...")

businesses = pd.read_csv(BUSINESS_FILE)
roads = gpd.read_file(ROAD_FILE)

required_columns = {"latitude", "longitude", "cluster"}
missing_columns = required_columns - set(businesses.columns)

if missing_columns:
    raise ValueError(
        f"Missing columns in business_clusters.csv: {missing_columns}"
    )

businesses = businesses.dropna(
    subset=["latitude", "longitude", "cluster"]
).copy()

businesses["cluster"] = businesses["cluster"].astype(int)

if "category" not in businesses.columns:
    businesses["category"] = "Other"

businesses["category"] = (
    businesses["category"].fillna("Other").astype(str)
)

if roads.crs is None:
    roads = roads.set_crs("EPSG:4326")


# ==================================================
# 2. CONVERT TO A METRIC COORDINATE SYSTEM
# ==================================================

points = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"],
        businesses["latitude"]
    ),
    crs="EPSG:4326"
)

metric_crs = points.estimate_utm_crs()

if metric_crs is None:
    raise ValueError("Could not determine the map coordinate system.")

points = points.to_crs(metric_crs)
roads = roads.to_crs(metric_crs)


# ==================================================
# 3. FIND SOUTH CONGRESS AVENUE
# ==================================================

def normalize_road_name(value):
    """Handle road names stored as text or list-like strings."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, (list, tuple)):
            text = " ".join(str(item) for item in parsed)
    except (ValueError, SyntaxError):
        pass

    return text.strip("[]'\" ").lower()


if "name" not in roads.columns:
    raise ValueError("The road file does not contain a 'name' column.")

roads["_normalized_name"] = roads["name"].apply(normalize_road_name)

soco_roads = roads[
    roads["_normalized_name"].str.contains(
        "south congress avenue",
        regex=False,
        na=False
    )
].copy()

print("Road segments found:", len(roads))
print("South Congress Avenue segments found:", len(soco_roads))


# ==================================================
# 4. CALCULATE CLUSTER SIZES
# ==================================================

clustered_points = points[points["cluster"] != -1]

cluster_sizes = (
    clustered_points.groupby("cluster")
    .size()
    .sort_values(ascending=False)
)

print("\nBusiness counts by cluster:")
print(cluster_sizes.to_string())


# ==================================================
# 5. SELECT BUSINESS CATEGORIES
# ==================================================

top_categories = (
    businesses["category"]
    .value_counts()
    .head(5)
    .index.tolist()
)

businesses["map_category"] = businesses["category"].where(
    businesses["category"].isin(top_categories),
    "Other"
)

points["map_category"] = businesses["map_category"].values

palette = plt.get_cmap("tab10")

category_color = {
    category: palette(i % 10)
    for i, category in enumerate(top_categories + ["Other"])
}


# ==================================================
# 6. CREATE THE MAP
# ==================================================

fig, ax = plt.subplots(figsize=(15, 10))

# Background road network
roads.plot(
    ax=ax,
    color="#D6DCE2",
    linewidth=0.7,
    alpha=0.9,
    zorder=1
)

# Highlight South Congress Avenue
if not soco_roads.empty:
    soco_roads.plot(
        ax=ax,
        color="#C0392B",
        linewidth=3.2,
        alpha=1,
        zorder=2
    )

# Plot businesses by category
for category in top_categories + ["Other"]:
    category_points = points[
        points["map_category"] == category
    ]

    if category_points.empty:
        continue

    category_points.plot(
        ax=ax,
        color=category_color[category],
        markersize=38 if category != "Other" else 23,
        alpha=0.85,
        edgecolor="white",
        linewidth=0.4,
        zorder=3
    )


# ==================================================
# 7. HIGHLIGHT CLUSTER 0 AS A CANDIDATE CORE AREA
# ==================================================

# This outlines Cluster 0's business points.
# It is NOT an official corridor boundary.

candidate = points[points["cluster"] == 0]

if not candidate.empty:
    candidate.plot(
        ax=ax,
        facecolor="none",
        edgecolor="black",
        linewidth=1.2,
        markersize=100,
        alpha=0.9,
        zorder=4
    )


# ==================================================
# 8. BUILD THE MAP LEGEND
# ==================================================

legend_items = []

if not soco_roads.empty:
    legend_items.append(
        Line2D(
            [0], [0],
            color="#C0392B",
            linewidth=3,
            label="South Congress Avenue"
        )
    )

for category in top_categories + ["Other"]:
    legend_items.append(
        Line2D(
            [0], [0],
            marker="o",
            color="white",
            markerfacecolor=category_color[category],
            markeredgecolor="white",
            markersize=8,
            label=category
        )
    )

if not candidate.empty:
    legend_items.append(
        Line2D(
            [0], [0],
            marker="o",
            color="black",
            markerfacecolor="none",
            markersize=9,
            label="Cluster 0: candidate core area"
        )
    )

ax.legend(
    handles=legend_items,
    title="Map Legend",
    loc="upper left",
    bbox_to_anchor=(1.01, 1),
    frameon=True,
    fontsize=9
)


# ==================================================
# 9. ADD TITLES AND FORMATTING
# ==================================================

ax.set_title(
    "SoCo, Austin, Texas\n"
    "Commercial Businesses and South Congress Avenue",
    fontsize=16,
    fontweight="bold",
    pad=18
)

ax.set_xlabel("Easting (metres)", fontsize=11)
ax.set_ylabel("Northing (metres)", fontsize=11)

ax.set_aspect("equal", adjustable="datalim")
ax.grid(alpha=0.15, linestyle="--")

plt.tight_layout()


# ==================================================
# 10. SAVE THE FINAL MAP
# ==================================================

fig.savefig(
    OUTPUT_FILE,
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

print("\n====================================")
print("SOCO MAP GENERATION COMPLETE")
print("====================================")
print("Map saved to:", OUTPUT_FILE)
print("Business records plotted:", len(points))
print("Businesses in candidate Cluster 0:", len(candidate))

if soco_roads.empty:
    print(
        "\nWARNING: South Congress Avenue was not found by name. "
        "Check the road names before finalizing the map."
    )

plt.show()
