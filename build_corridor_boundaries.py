
from pathlib import Path
import geopandas as gpd
from shapely.ops import unary_union

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Austin, Texas: projected CRS uses metres
PROJECTED_CRS = "EPSG:32614"
OUTPUT_CRS = "EPSG:4326"

# Input road file -> output boundary file
CORRIDORS = {
    "East Riverside": (
        "roads_east_riverside.geojson",
        "boundary_east_riverside.geojson",
    ),
    "Burnet Road": (
        "roads_burnet_road.geojson",
        "boundary_burnet_road.geojson",
    ),
    "North Lamar": (
        "roads_north_lamar.geojson",
        "boundary_north_lamar.geojson",
    ),
    "South Lamar": (
        "roads_south_lamar.geojson",
        "boundary_south_lamar.geojson",
    ),
    "Guadalupe Street (The Drag)": (
        "roads_guadalupe___the_drag.geojson",
        "boundary_guadalupe___the_drag.geojson",
    ),
}

BUFFER_METERS = 100


def main():
    print("\n=== BUILDING AUSTIN CORRIDOR BOUNDARIES ===\n")

    for corridor, (input_name, output_name) in CORRIDORS.items():
        input_path = DATA_DIR / input_name
        output_path = DATA_DIR / output_name

        print(f"\nProcessing: {corridor}")

        if not input_path.exists():
            print(f"  ERROR: Road file not found: {input_name}")
            continue

        # Preserve existing results rather than overwrite them.
        if output_path.exists():
            print(f"  SKIPPED: Boundary already exists: {output_name}")
            continue

        try:
            roads = gpd.read_file(input_path)

            if roads.empty:
                print("  ERROR: Road file contains no features.")
                continue

            if roads.crs is None:
                roads = roads.set_crs(OUTPUT_CRS)
            else:
                roads = roads.to_crs(OUTPUT_CRS)

            roads = roads[
                roads.geometry.notna() & ~roads.geometry.is_empty
            ]

            if roads.empty:
                print("  ERROR: No usable road geometries.")
                continue

            # Reproject to metres before buffering.
            roads_m = roads.to_crs(PROJECTED_CRS)
            merged_roads = unary_union(list(roads_m.geometry))

            if merged_roads.is_empty:
                print("  ERROR: Combined road geometry is empty.")
                continue

            # Approximate corridor area: 100 metres around road segments.
            boundary = merged_roads.buffer(BUFFER_METERS)

            result = gpd.GeoDataFrame(
                {
                    "corridor": [corridor],
                    "buffer_m": [BUFFER_METERS],
                    "boundary_type": ["approximate_road_buffer"],
                },
                geometry=[boundary],
                crs=PROJECTED_CRS,
            ).to_crs(OUTPUT_CRS)

            result.to_file(output_path, driver="GeoJSON")

            print(f"  SUCCESS: Created {output_name}")
            print(f"  Road features used: {len(roads)}")
            print(f"  Buffer distance: {BUFFER_METERS} metres")

        except Exception as exc:
            print(f"  ERROR: {type(exc).__name__}: {exc}")

    print("\n=== FINISHED ===")
    print("Check the messages above for SUCCESS, SKIPPED, or ERROR.")


if __name__ == "__main__":
    main()
