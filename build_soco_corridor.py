
from pathlib import Path
import ast
import re

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from shapely.geometry import LineString, MultiLineString, GeometryCollection
from shapely.ops import unary_union, linemerge


# --------------------------------------------------
# 1. FILE PATHS AND SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

ROADS_FILE = DATA_DIR / "roads.geojson"
BUSINESSES_FILE = DATA_DIR / "business_locations.csv"

CORRIDOR_NAME = "South Congress Avenue"
BUFFER_METERS = 100

DATA_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. CLEAN ROAD NAMES SAFELY
# --------------------------------------------------

def normalize_road_name(value):
    """
    Handles road names stored as:
    - normal strings
    - missing values
    - Python lists or tuples
    - NumPy arrays
    - strings that look like lists
    """

    if value is None:
        return ""

    # Handle strings separately so pd.isna()
    # is never applied to a list or array.
    if isinstance(value, str):
        text = value.strip()

        if not text:
            return ""

        # Convert strings such as:
        # "['South Congress Avenue']"
        # into an actual Python list.
        if text.startswith("[") or text.startswith("("):
            try:
                parsed = ast.literal_eval(text)
                return normalize_road_name(parsed)
            except (ValueError, SyntaxError):
                pass

        return re.sub(r"\s+", " ", text).strip().lower()

    # Handle lists, tuples, and arrays.
    if isinstance(value, (list, tuple)):
        parts = [normalize_road_name(item) for item in value]
        return " ".join(part for part in parts if part)

    # Handle NumPy arrays without importing NumPy.
    if hasattr(value, "tolist"):
        try:
            return normalize_road_name(value.tolist())
        except (ValueError, TypeError):
            return ""

    # Handle ordinary missing values.
    try:
        if pd.isna(value):
            return ""
    except (ValueError, TypeError):
        pass

    return str(value).strip().lower()


# --------------------------------------------------
# 3. LOAD THE DATA
# --------------------------------------------------

print("\n=== BUILDING THE SOCO CORRIDOR ===")

if not ROADS_FILE.exists():
    raise FileNotFoundError(
        f"Road file not found: {ROADS_FILE}"
    )

if not BUSINESSES_FILE.exists():
    raise FileNotFoundError(
        f"Business file not found: {BUSINESSES_FILE}"
    )

roads = gpd.read_file(ROADS_FILE)
businesses = pd.read_csv(BUSINESSES_FILE)

print(f"Road records loaded: {len(roads)}")
print(f"Business records loaded: {len(businesses)}")

if roads.empty:
    raise ValueError("The roads file contains no records.")

if businesses.empty:
    raise ValueError("The business file contains no records.")

if "name" not in roads.columns:
    raise ValueError("The roads file has no 'name' column.")

required_business_columns = {"latitude", "longitude"}
missing_columns = required_business_columns - set(businesses.columns)

if missing_columns:
    raise ValueError(
        f"Missing business columns: {sorted(missing_columns)}"
    )

if roads.crs is None:
    raise ValueError(
        "The roads file has no CRS. Please check roads.geojson."
    )


# --------------------------------------------------
# 4. FIND SOUTH CONGRESS AVENUE ROAD SEGMENTS
# --------------------------------------------------

roads["_normalized_name"] = roads["name"].apply(
    normalize_road_name
)

target_name = CORRIDOR_NAME.lower()

soco_roads = roads[
    roads["_normalized_name"].apply(
        lambda name: target_name in name
    )
].copy()

if soco_roads.empty:
    print("\nRoad names found in the dataset:")
    print(
        roads["name"]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(30)
        .to_list()
    )

    raise ValueError(
        "No South Congress Avenue segments were found. "
        "Check the road names printed above."
    )

print(
    f"\nSouth Congress Avenue road records: "
    f"{len(soco_roads)}"
)


# --------------------------------------------------
# 5. PROJECT THE DATA INTO METERS
# --------------------------------------------------

metric_crs = roads.estimate_utm_crs()

if metric_crs is None:
    raise ValueError(
        "Could not determine a suitable metric CRS."
    )

roads_metric = roads.to_crs(metric_crs)
soco_roads_metric = soco_roads.to_crs(metric_crs)

print(f"Metric CRS: {metric_crs}")


# --------------------------------------------------
# 6. BUILD THE CORRIDOR CENTERLINE
# --------------------------------------------------

# Merge touching road segments where possible.
merged_roads = unary_union(
    list(soco_roads_metric.geometry)
)

if merged_roads.is_empty:
    raise ValueError(
        "The selected road geometries are empty."
    )

if isinstance(merged_roads, LineString):
    centerline = merged_roads

elif isinstance(merged_roads, MultiLineString):
    centerline = linemerge(merged_roads)

elif isinstance(merged_roads, GeometryCollection):
    line_parts = [
        geom
        for geom in merged_roads.geoms
        if geom.geom_type in ("LineString", "MultiLineString")
    ]

    if not line_parts:
        raise ValueError(
            "No usable line geometries were found."
        )

    line_union = unary_union(line_parts)

    if isinstance(line_union, LineString):
        centerline = line_union
    else:
        centerline = linemerge(line_union)

else:
    raise ValueError(
        f"Unexpected road geometry: {merged_roads.geom_type}"
    )


# Count separate line components to check continuity.
if centerline.geom_type == "LineString":
    component_count = 1

elif centerline.geom_type == "MultiLineString":
    component_count = len(centerline.geoms)

else:
    component_count = len(
        [
            geom for geom in centerline.geoms
            if geom.geom_type in ("LineString", "MultiLineString")
        ]
    )

print(f"Connected road components: {component_count}")

if component_count > 1:
    print(
        "NOTE: The road contains multiple separate sections. "
        "The corridor will include all selected sections."
    )


# --------------------------------------------------
# 7. CREATE THE CORRIDOR AREA
# --------------------------------------------------

# Create a 100-metre buffer on each side of the road.
corridor_area = centerline.buffer(BUFFER_METERS)

if corridor_area.is_empty:
    raise ValueError(
        "The corridor buffer could not be created."
    )

print(f"Buffer width on each side: {BUFFER_METERS} metres")


# --------------------------------------------------
# 8. CREATE BUSINESS LOCATION POINTS
# --------------------------------------------------

businesses["latitude"] = pd.to_numeric(
    businesses["latitude"], errors="coerce"
)

businesses["longitude"] = pd.to_numeric(
    businesses["longitude"], errors="coerce"
)

businesses = businesses.dropna(
    subset=["latitude", "longitude"]
).copy()

business_points = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"],
        businesses["latitude"]
    ),
    crs="EPSG:4326"
)

businesses_metric = business_points.to_crs(metric_crs)


# --------------------------------------------------
# 9. SELECT BUSINESSES INSIDE THE CORRIDOR
# --------------------------------------------------

inside_mask = businesses_metric.geometry.apply(
    corridor_area.covers
)

corridor_businesses = businesses_metric.loc[
    inside_mask
].copy()

outside_businesses = businesses_metric.loc[
    ~inside_mask
].copy()

print(f"\nBusinesses inside corridor: {len(corridor_businesses)}")
print(f"Businesses outside corridor: {len(outside_businesses)}")


# --------------------------------------------------
# 10. CALCULATE SUMMARY METRICS
# --------------------------------------------------

corridor_length_km = centerline.length / 1000
corridor_area_sq_km = corridor_area.area / 1_000_000

if "category" in corridor_businesses.columns:
    category_count = corridor_businesses["category"].nunique()
else:
    category_count = 0

if corridor_length_km > 0:
    business_density = (
        len(corridor_businesses) / corridor_length_km
    )
else:
    business_density = 0

summary = pd.DataFrame([{
    "corridor_name": CORRIDOR_NAME,
    "road_records": len(soco_roads),
    "connected_road_components": component_count,
    "corridor_length_km": round(corridor_length_km, 3),
    "buffer_each_side_m": BUFFER_METERS,
    "corridor_area_sq_km": round(corridor_area_sq_km, 4),
    "businesses_inside": len(corridor_businesses),
    "businesses_outside": len(outside_businesses),
    "unique_business_categories": category_count,
    "businesses_per_km": round(business_density, 2),
}])

print("\n=== CORRIDOR SUMMARY ===")
print(summary.to_string(index=False))


# --------------------------------------------------
# 11. SAVE THE CORRIDOR FILES
# --------------------------------------------------

# Save selected road records.
soco_roads.drop(
    columns=["_normalized_name"],
    errors="ignore"
).to_file(
    DATA_DIR / "soco_corridor_roads.geojson",
    driver="GeoJSON"
)

# Save the buffered corridor polygon.
gpd.GeoDataFrame(
    {"corridor_name": [CORRIDOR_NAME]},
    geometry=[corridor_area],
    crs=metric_crs
).to_crs("EPSG:4326").to_file(
    DATA_DIR / "soco_corridor_area.geojson",
    driver="GeoJSON"
)

# Save the merged centerline.
gpd.GeoDataFrame(
    {"corridor_name": [CORRIDOR_NAME]},
    geometry=[centerline],
    crs=metric_crs
).to_crs("EPSG:4326").to_file(
    DATA_DIR / "soco_corridor_centerline.geojson",
    driver="GeoJSON"
)

# Save business results as CSV without geometry.
corridor_businesses.drop(
    columns=["geometry"],
    errors="ignore"
).to_csv(
    DATA_DIR / "soco_corridor_businesses.csv",
    index=False
)

summary.to_csv(
    DATA_DIR / "soco_corridor_summary.csv",
    index=False
)


# --------------------------------------------------
# 12. DRAW THE CORRIDOR MAP
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 12))

# All nearby roads in light grey.
roads_metric.plot(
    ax=ax,
    color="lightgrey",
    linewidth=0.7,
    label="Other roads"
)

# Buffered corridor area.
gpd.GeoSeries(
    [corridor_area],
    crs=metric_crs
).plot(
    ax=ax,
    color="orange",
    alpha=0.30,
    edgecolor="darkorange",
    linewidth=1.2,
    label="100 m corridor area"
)

# South Congress Avenue centerline.
gpd.GeoSeries(
    [centerline],
    crs=metric_crs
).plot(
    ax=ax,
    color="red",
    linewidth=2.5,
    label="South Congress Avenue"
)

# Businesses within the corridor.
if not corridor_businesses.empty:
    corridor_businesses.plot(
        ax=ax,
        color="green",
        markersize=22,
        alpha=0.85,
        label="Businesses inside corridor"
    )

# Businesses outside the corridor.
if not outside_businesses.empty:
    outside_businesses.plot(
        ax=ax,
        color="steelblue",
        markersize=10,
        alpha=0.45,
        label="Businesses outside corridor"
    )

ax.set_title(
    "SoCo Corridor — South Congress Avenue, Austin",
    fontsize=15
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.legend(loc="best")
ax.set_aspect("equal")
ax.grid(alpha=0.2)

plt.tight_layout()

map_path = DATA_DIR / "soco_corridor_map.png"
plt.savefig(map_path, dpi=200, bbox_inches="tight")
plt.close(fig)


# --------------------------------------------------
# 13. FINISH
# --------------------------------------------------

print("\n=== CORRIDOR BUILD COMPLETED ===")
print(f"Map: {map_path}")
print(f"Summary: {DATA_DIR / 'soco_corridor_summary.csv'}")
print(
    f"Businesses: "
    f"{DATA_DIR / 'soco_corridor_businesses.csv'}"
)
print(
    f"Corridor polygon: "
    f"{DATA_DIR / 'soco_corridor_area.geojson'}"
)
print(
    f"Centerline: "
    f"{DATA_DIR / 'soco_corridor_centerline.geojson'}"
)
