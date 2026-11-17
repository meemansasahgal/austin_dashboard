
from pathlib import Path
import time

import osmnx as ox
import pandas as pd

# --------------------------------------------------
# 1. FOLDER SETTINGS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Approximate center of the SoCo area, Austin, Texas
CENTER = (30.2474, -97.7495)

# --------------------------------------------------
# 2. OPENSTREETMAP SETTINGS
# --------------------------------------------------

ox.settings.log_console = True
ox.settings.use_cache = True

# Shorter timeout prevents one request from hanging too long.
ox.settings.requests_timeout = 45

OVERPASS_ENDPOINTS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

TAGS = {
    "shop": True,
    "amenity": [
        "restaurant", "cafe", "fast_food", "bar", "pub",
        "ice_cream", "bank", "pharmacy", "hairdresser",
        "beauty_salon", "marketplace"
    ],
    "office": True,
    "tourism": ["hotel", "attraction", "gallery"],
    "leisure": ["fitness_centre"]
}


# --------------------------------------------------
# 3. TRY MULTIPLE OVERPASS SERVERS
# --------------------------------------------------

def fetch_with_fallback(description, operation):
    """
    Try each public Overpass endpoint.
    Stop when one endpoint successfully returns data.
    """

    errors = []

    for endpoint in OVERPASS_ENDPOINTS:
        print(f"\n{description}")
        print(f"Trying endpoint: {endpoint}")

        ox.settings.overpass_url = endpoint

        try:
            result = operation()

            if result is None or result.empty:
                raise RuntimeError("The endpoint returned no data.")

            print(f"Success using: {endpoint}")
            return result

        except Exception as error:
            message = f"{endpoint}: {error}"
            errors.append(message)
            print(f"Endpoint failed: {error}")

            # Brief pause before trying the next endpoint
            time.sleep(2)

    raise RuntimeError(
        f"\nAll Overpass endpoints failed for {description}.\n"
        + "\n".join(errors)
        + "\nPlease try again later or check your internet connection."
    )


# --------------------------------------------------
# 4. DOWNLOAD BUSINESS LOCATIONS
# --------------------------------------------------

business_file = DATA_DIR / "business_locations.csv"

if business_file.exists() and business_file.stat().st_size > 0:
    print(f"Existing business dataset found: {business_file}")
    businesses_df = pd.read_csv(business_file)

else:
    print("\nDownloading SoCo business locations...")

    businesses = fetch_with_fallback(
        "Downloading businesses",
        lambda: ox.features_from_point(
            CENTER,
            tags=TAGS,
            dist=900
        )
    )

    businesses = businesses[
        businesses.geometry.notna()
    ].copy()

    if businesses.empty:
        raise RuntimeError("No business geometries were found.")

    # Convert geometries to representative points
    projected = businesses.to_crs(
        businesses.estimate_utm_crs()
    )

    points = projected.geometry.representative_point().to_crs(
        "EPSG:4326"
    )

    businesses["latitude"] = points.y
    businesses["longitude"] = points.x

    def get_category(row):
        for field in [
            "shop", "amenity", "office", "tourism", "leisure"
        ]:
            value = row.get(field)

            if pd.notna(value) and value is not True:
                return str(value)

            if value is True:
                return field

        return "other"

    businesses["category"] = businesses.apply(
        get_category,
        axis=1
    )

    columns = [
        "name", "category", "shop", "amenity",
        "latitude", "longitude"
    ]

    for column in columns:
        if column not in businesses.columns:
            businesses[column] = ""

    businesses_df = businesses[columns].copy()

    businesses_df.to_csv(
        business_file,
        index=False
    )

    print(f"Saved {len(businesses_df)} business records.")
    print(f"File: {business_file}")


# --------------------------------------------------
# 5. DOWNLOAD ROAD NETWORK
# --------------------------------------------------

roads_file = DATA_DIR / "roads.geojson"
graph_file = DATA_DIR / "road_network.graphml"

if roads_file.exists() and roads_file.stat().st_size > 0:
    print(f"\nExisting road dataset found: {roads_file}")

else:
    print("\nDownloading SoCo road network...")

    graph = fetch_with_fallback(
        "Downloading road network",
        lambda: ox.graph_from_point(
            CENTER,
            dist=1000,
            network_type="drive"
        )
    )

    roads = ox.graph_to_gdfs(
        graph,
        nodes=False,
        edges=True
    )

    if roads.empty:
        raise RuntimeError("No road segments were found.")

    roads.to_file(
        roads_file,
        driver="GeoJSON"
    )

    ox.save_graphml(
        graph,
        graph_file
    )

    print(f"Saved {len(roads)} road segments.")
    print(f"Road file: {roads_file}")

# --------------------------------------------------
# 6. DOWNLOAD SUMMARY
# --------------------------------------------------

print("\n" + "=" * 45)
print("DOWNLOAD CHECK")
print("=" * 45)

print(f"Business records: {len(businesses_df)}")
print(f"Business CSV: {business_file}")
print(f"Road GeoJSON: {roads_file}")

if graph_file.exists():
    print(f"Road network: {graph_file}")
else:
    print(
        "Road network GraphML was not newly created "
        "because the road GeoJSON already existed."
    )

print("\nDOWNLOAD COMPLETE!")
