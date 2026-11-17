
from pathlib import Path
import osmnx as ox

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CENTER = (30.2474, -97.7495)

# Try a different public OpenStreetMap server
ox.settings.log_console = True
ox.settings.use_cache = True
ox.settings.overpass_url = "https://overpass.kumi.systems/api"

print("Downloading SoCo road network...")

graph = ox.graph_from_point(
    CENTER,
    dist=1000,
    network_type="drive",
    simplify=True
)

roads = ox.graph_to_gdfs(
    graph,
    nodes=False,
    edges=True
)

roads.to_file(
    DATA_DIR / "roads.geojson",
    driver="GeoJSON"
)

ox.save_graphml(
    graph,
    DATA_DIR / "road_network.graphml"
)

print("SUCCESS! Road network downloaded.")
print("Road segments:", len(roads))
print("Saved to:", DATA_DIR)

