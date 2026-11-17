from pathlib import Path
import math
import warnings

import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CORRIDORS = {
    "South Congress Avenue (SoCo)": {"short": "SoCo", "center": (30.2474, -97.7495), "search_radius_m": 1800, "buffer_m": 120, "match": ["south congress avenue", "south congress"], "color": "#E76F51", "description": "Real-world profile: boutique and specialty retail, apparel and gifts, galleries, hotels, live music and visitor-oriented dining. Food is one part of a wider shopping and entertainment district."},
    "South Lamar Boulevard": {"short": "South Lamar", "center": (30.2500, -97.7810), "search_radius_m": 2200, "buffer_m": 150, "match": ["south lamar boulevard", "south lamar blvd", "south lamar"], "color": "#2A9D8F", "description": "Real-world profile: a mixed commercial strip with restaurants and bars, entertainment, retail, auto-oriented services, offices and mixed-use developments; the mix varies by section."},
    "East Riverside Drive": {"short": "East Riverside", "center": (30.2370, -97.7220), "search_radius_m": 2200, "buffer_m": 150, "match": ["east riverside drive", "e riverside drive", "riverside drive", "east riverside"], "color": "#457B9D", "description": "Real-world profile: mixed-use redevelopment alongside everyday retail and services, grocery/convenience uses, apartments, and a substantial food offering. The exact mix varies along the corridor."},
    "Burnet Road": {"short": "Burnet Road", "center": (30.3450, -97.7390), "search_radius_m": 2200, "buffer_m": 125, "match": ["burnet road", "burnet rd"], "color": "#D6A72C", "description": "Real-world profile: neighborhood-serving retail and shopping centers, auto sales/repair, personal and professional services, offices and restaurants—not just dining."},
    "North Lamar Boulevard": {"short": "North Lamar", "center": (30.3350, -97.7270), "search_radius_m": 2500, "buffer_m": 150, "match": ["north lamar boulevard", "n lamar boulevard", "north lamar blvd", "north lamar"], "color": "#8E6CBA", "description": "Real-world profile: a broad, culturally diverse commercial corridor with international groceries and markets, specialty retail, beauty and financial services, travel agencies and restaurants."},
    "Guadalupe Street (The Drag)": {"short": "Guadalupe / The Drag", "center": (30.2860, -97.7420), "search_radius_m": 1400, "buffer_m": 100, "match": ["guadalupe street", "guadalupe st"], "color": "#D45087", "description": "Real-world profile: a student-facing university strip with bookstores/campus retail, convenience and apparel shops, services, music/culture and restaurants. Dining is visible but not the only defining use."},
    "Congress Avenue (Downtown)": {"short": "Congress Ave", "center": (30.2672, -97.7428), "search_radius_m": 1800, "buffer_m": 150, "match": ["south congress avenue", "congress avenue", "congress ave"], "color": "#3A86FF", "description": "Downtown Congress Avenue commercial corridor; road-name matching should be checked against the saved OSM road geometry."},
    "Manor Road": {"short": "Manor Road", "center": (30.2868, -97.7150), "search_radius_m": 2200, "buffer_m": 150, "match": ["manor road", "manor rd"], "color": "#8338EC", "description": "East Austin neighborhood commercial corridor with local retail, food, services and community destinations."},
    "Airport Boulevard": {"short": "Airport Blvd", "center": (30.3070, -97.7070), "search_radius_m": 2500, "buffer_m": 150, "match": ["airport boulevard", "airport blvd"], "color": "#FB5607", "description": "North-central Austin commercial corridor with retail, services, food and transport-oriented businesses."},
    "Research Boulevard (US 183)": {"short": "Research Blvd", "center": (30.3900, -97.7400), "search_radius_m": 3000, "buffer_m": 150, "match": ["research boulevard", "research blvd", "us 183", "us highway 183"], "color": "#06A77D", "description": "US 183 / Research Boulevard commercial section; exact road-name matching and corridor extent should be validated after OSM collection."},
    "Cameron Road": {"short": "Cameron Road", "center": (30.3270, -97.7040), "search_radius_m": 2400, "buffer_m": 150, "match": ["cameron road", "cameron rd"], "color": "#BC6C25", "description": "Cameron Road commercial corridor with neighborhood services, retail, food and health-related destinations."},
}


# Research-backed corridor identity themes (relative emphasis, not business counts).
# These scores describe the corridor's recognizable commercial role and are kept
# separate from the live OSM inventory so the app never presents them as census data.
CORRIDOR_LEADERS = {
    "South Congress Avenue (SoCo)": {
        "Leading activity": "Retail & shopping",
        "Other strong activities": "Accommodation & tourism",
    },
    "South Lamar Boulevard": {
        "Leading activity": "Food & drink and Recreation & fitness (tie)",
        "Other strong activities": "Retail & shopping, Professional & financial services",
    },
    "East Riverside Drive": {
        "Leading activity": "Food & drink",
        "Other strong activities": "Retail & shopping",
    },
    "Burnet Road": {
        "Leading activity": "Retail & shopping",
        "Other strong activities": "Transport & automotive, Professional & financial services",
    },
    "North Lamar Boulevard": {
        "Leading activity": "Retail & shopping",
        "Other strong activities": "Community & public services, Professional & financial services",
    },
    "Guadalupe Street (The Drag)": {
        "Leading activity": "Food & drink",
        "Other strong activities": "Education & culture, Retail & shopping",
    },
}


CORRIDOR_PROFILE = {
    "South Congress Avenue (SoCo)": {
        "Retail & shopping": 5, "Accommodation & tourism": 4,
        "Recreation & fitness": 3, "Food & drink": 3,
        "Education & culture": 3, "Professional & financial services": 1,
    },
    "South Lamar Boulevard": {
        "Recreation & fitness": 4, "Food & drink": 4,
        "Retail & shopping": 3, "Professional & financial services": 3,
        "Transport & automotive": 2, "Education & culture": 2,
    },
    "East Riverside Drive": {
        "Food & drink": 5, "Retail & shopping": 4,
        "Professional & financial services": 4, "Transport & automotive": 3,
        "Recreation & fitness": 3, "Education & culture": 3,
    },
    "Burnet Road": {
        "Retail & shopping": 5, "Transport & automotive": 4,
        "Professional & financial services": 4, "Health & care": 3,
        "Food & drink": 3, "Recreation & fitness": 2,
    },
    "North Lamar Boulevard": {
        "Retail & shopping": 5, "Food & drink": 3, "Recreation & fitness": 3,
        "Community & public services": 4, "Professional & financial services": 4,
        "Health & care": 3, "Education & culture": 3,
    },
    "Guadalupe Street (The Drag)": {
        "Food & drink": 5, "Education & culture": 4,
        "Retail & shopping": 4, "Recreation & fitness": 3,
        "Professional & financial services": 2, "Accommodation & tourism": 1,
    },
}

st.set_page_config(page_title="Austin Corridor Intelligence", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
:root { --ink:#17352f; --muted:#687b76; --accent:#1f6a56; }
/* Soft, polished canvas: styling only; all app logic and map layers remain unchanged. */
.stApp {background:linear-gradient(145deg,#f3f7f5 0%,#f7f5ef 52%,#eef5f4 100%); color:#203a35;}
.block-container {padding-top:1.35rem; padding-bottom:2rem; max-width:1500px;}
[data-testid="stHeader"] {background:rgba(243,247,245,.88);}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#173c34 0%,#102d28 100%);border-right:1px solid #28594e;}
[data-testid="stSidebar"] * {color:#f4f8f5 !important;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#d7e7e0 !important;}
.hero {padding:1.45rem 1.6rem;border-radius:18px;background:linear-gradient(120deg,#173c34 0%,#286a58 65%,#438c76 100%);color:white;margin-bottom:1.15rem;box-shadow:0 8px 24px rgba(23,60,52,.13);border:1px solid rgba(255,255,255,.16);}
.hero h1 {color:white;font-size:2rem;margin:0 0 .3rem 0;}
.hero p {color:#dcebe4;margin:0;}
.metric-note {color:#6b7d77;font-size:.8rem;}
.section-title {font-size:1.2rem;font-weight:750;color:#173c34;margin:.65rem 0 .8rem 0;}
.small-card,[data-testid="stMetric"] {padding:1rem;border:1px solid #dce8e2;border-radius:14px;background:rgba(255,255,255,.88);box-shadow:0 3px 12px rgba(27,67,57,.045);}
[data-testid="stMetricLabel"] {color:#58766c !important;}
[data-testid="stMetricValue"] {color:#173c34 !important;}
[data-testid="stTabs"] [role="tab"] {border-radius:10px 10px 0 0;color:#42675b;}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {color:#145c49;border-bottom-color:#23866a;font-weight:700;}
.stButton > button, .stDownloadButton > button {border-radius:10px;border:1px solid #b8d2c7;background:linear-gradient(180deg,#ffffff,#f1f8f4);color:#174b3e;font-weight:650;transition:all .15s ease;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color:#32876d;background:#e4f4ec;color:#123f33;}
[data-testid="stDataFrame"], [data-testid="stTable"] {border:1px solid #dce8e2;border-radius:12px;overflow:hidden;}
[data-testid="stExpander"] {border:1px solid #dce8e2;border-radius:12px;background:rgba(255,255,255,.68);}
[data-testid="stTextInput"] input, [data-testid="stSelectbox"] > div, [data-testid="stMultiSelect"] > div {border-radius:10px;}
hr {border-color:#dbe7e1;}
</style>
""", unsafe_allow_html=True)

TAGS = {
    "shop": True,
    "amenity": True,
    "office": True,
    "tourism": True,
    "leisure": True,
    "craft": True,
    "healthcare": True,
    "club": True,
    "public_transport": ["station", "stop_position"],
    "healthcare": True,
    "craft": True,
    "building": ["commercial", "retail", "office", "university", "school"],
}

EARTH_RADIUS_M = 6_371_000


def category_for(row):
    """Keep the most specific OSM tag available; do not let a generic tag mask a specific one."""
    priority = ["shop", "amenity", "healthcare", "office", "craft", "tourism", "leisure", "club", "public_transport"]
    for field in priority:
        value = row.get(field)
        if pd.notna(value) and str(value).strip() and str(value).lower() not in {"nan", "none", "false"}:
            if value is True or str(value).lower() in {"yes", "true"}:
                continue
            return str(value).replace("_", " ").strip().lower()
    return "other"


def major_activity(category, row=None):
    """Classify from raw OSM tags first; use category/name only as fallbacks.

    OSM stores a business' type in different keys (shop, amenity, office,
    healthcare, leisure, etc.). Looking only at the single `category` value
    can overstate food businesses and hide the corridor's broader mix.
    """
    row = row if row is not None else {}

    def clean(value):
        if value is None or pd.isna(value):
            return ""
        value = str(value).strip().lower().replace("_", " ")
        return "" if value in {"", "nan", "none", "false", "no", "unknown"} else value

    # Newly collected files store raw tags with an osm_ prefix; older files
    # may contain the original unprefixed OSM columns.
    tags = {}
    for key in ["shop", "amenity", "healthcare", "office", "craft", "tourism",
                "leisure", "club", "public_transport", "building"]:
        value = clean(row.get("osm_" + key, row.get(key, "")))
        if value:
            tags[key] = value

    food = {"restaurant", "fast food", "cafe", "coffee shop", "bar", "pub",
            "biergarten", "ice cream", "food court", "food", "bakery",
            "confectionery", "deli", "tea", "juice bar", "food truck", "marketplace"}
    retail = {"clothes", "shoes", "jewelry", "gift", "books", "bookshop",
              "department store", "supermarket", "convenience", "greengrocer",
              "butcher", "mall", "general", "fashion", "electronics",
              "mobile phone", "bicycle", "car", "florist", "chemist",
              "cosmetics", "hardware", "furniture", "sports", "stationery",
              "toys", "art", "video", "second hand", "variety store", "pet",
              "optician", "tobacco", "e-cigarette", "alcohol", "diy", "trade",
              "department store", "outdoor", "musical instrument", "fabric",
              "bag", "beauty", "hairdresser", "bookmaker", "copy shop"}
    health = {"hospital", "clinic", "doctors", "dentist", "veterinary", "pharmacy",
              "nursing home", "social facility", "physiotherapist", "optometrist",
              "medical supply", "blood donation", "health centre"}
    professional = {"bank", "atm", "bureau de change", "insurance", "lawyer",
                    "estate agent", "accountant", "coworking", "financial",
                    "government", "post office", "employment agency", "consulting",
                    "advertising agency", "it", "company", "research", "educational institution"}
    education = {"school", "university", "college", "kindergarten", "library",
                 "arts centre", "community centre", "museum", "gallery", "theatre",
                 "cinema", "music school", "language school", "training", "driving school"}
    recreation = {"fitness centre", "sports centre", "gym", "park", "playground",
                  "stadium", "pitch", "swimming pool", "dance", "nightclub",
                  "bowling alley", "escape game", "sports", "adult gaming centre"}
    transport = {"fuel", "charging station", "parking", "car wash", "car repair",
                 "bicycle repair station", "bus station", "taxi", "vehicle inspection",
                 "motorcycle", "car rental", "bicycle rental", "bus stop", "station"}
    public = {"place of worship", "police", "fire station", "courthouse", "public building",
              "shelter", "toilets", "recycling", "waste disposal", "community centre"}

    # Use the semantic OSM key first. A tagged shop remains retail even if its
    # name happens to contain a food-related word; explicit amenity=restaurant
    # is food only when no more specific shop tag exists.
    shop = tags.get("shop", "")
    if shop:
        if shop in {"car repair", "tyres", "car parts", "motorcycle", "fuel"}:
            return "Transport & automotive"
        if shop in {"beauty", "hairdresser", "massage", "tattoo", "optician", "hearing aids"}:
            return "Health & care"
        if shop in food:
            return "Food & drink"
        return "Retail & shopping"

    amenity = tags.get("amenity", "")
    if amenity in food:
        return "Food & drink"
    if amenity in health:
        return "Health & care"
    if amenity in professional:
        return "Professional & financial services"
    if amenity in education:
        return "Education & culture"
    if amenity in recreation:
        return "Recreation & fitness"
    if amenity in transport:
        return "Transport & automotive"
    if amenity in public:
        return "Community & public services"
    if tags.get("healthcare"):
        return "Health & care"
    if tags.get("office"):
        return "Professional & financial services"
    if tags.get("craft"):
        return "Retail & shopping"
    if tags.get("tourism"):
        return "Accommodation & tourism"
    if tags.get("leisure") or tags.get("club"):
        leisure = tags.get("leisure", tags.get("club", ""))
        if leisure in {"park", "playground", "sports centre", "fitness centre", "pitch", "swimming pool", "stadium"}:
            return "Recreation & fitness"
        return "Recreation & fitness"
    if tags.get("public_transport"):
        return "Transport & automotive"

    # Legacy CSVs may lack raw OSM tags. Use conservative business-name signals
    # before falling back to their single old category field; never infer a whole
    # corridor's leading activity from its profile description.
    name = clean(row.get("name", ""))
    name_rules = [
        (["bookstore", "book shop", "bookshop", "university co-op", "clothing", "boutique", "outfitters", "vintage", "shoe store", "gift shop", "record store", "comic shop", "grocery", "market", "supermarket", "convenience store", "liquor store", "hardware", "furniture", "electronics", "mobile", "florist", "pet store", "thrift", "consignment", "jewelry", "salon", "barber", "beauty supply"], "Retail & shopping"),
        (["fitness", "gym", "yoga", "pilates", "climbing", "dance studio", "sports club"], "Recreation & fitness"),
        (["pharmacy", "medical", "dental", "dentist", "clinic", "urgent care", "health center", "optometry", "veterinary"], "Health & care"),
        (["bank", "credit union", "insurance", "law office", "attorney", "accounting", "realty", "real estate", "travel agency", "staffing", "coworking"], "Professional & financial services"),
        (["university", "college", "library", "museum", "gallery", "theatre", "theater", "cinema", "arts center", "arts centre", "music school"], "Education & culture"),
        (["hotel", "motel", "hostel", "inn ", "guest house", "visitor center", "tour"], "Accommodation & tourism"),
        (["auto repair", "car repair", "tire shop", "tyre shop", "gas station", "car wash", "car dealership", "auto sales", "parking", "bike repair"], "Transport & automotive"),
    ]
    for phrases, activity in name_rules:
        if any(x in name for x in phrases):
            return activity

    c = clean(category)
    if c in food:
        return "Food & drink"
    if c in retail:
        return "Retail & shopping"
    if c in health:
        return "Health & care"
    if c in professional or c in {"office", "laundry", "dry cleaning", "tailor", "repair", "storage", "shipping", "travel agency"}:
        return "Professional & financial services"
    if c in education:
        return "Education & culture"
    if c in {"hotel", "motel", "hostel", "guest house", "attraction", "information", "viewpoint", "artwork"}:
        return "Accommodation & tourism"
    if c in recreation or c in {"leisure", "club"}:
        return "Recreation & fitness"
    if c in transport:
        return "Transport & automotive"
    if c in public:
        return "Community & public services"
    return "Miscellaneous Retail & Services"


def enrich_categories(df):
    """Add major_activity without overwriting the source category or raw OSM tags."""
    if df.empty:
        return df
    if "category" not in df.columns:
        df["category"] = "other"
    df["category"] = df["category"].fillna("other").astype(str)
    df["major_activity"] = [major_activity(cat, row) for cat, (_, row) in zip(df["category"], df.iterrows())]
    return df


def load_soco():
    # Load the same canonical CSV path as every other corridor. Do not attach old cluster labels
    # by row position: that can silently mismatch rows when the source CSV has changed.
    path = DATA_DIR / "soco_corridor_businesses.csv"
    if not path.exists():
        return pd.DataFrame(columns=["name", "category", "latitude", "longitude", "corridor"])
    df = pd.read_csv(path)
    for col in ["name", "category", "latitude", "longitude"]:
        if col not in df.columns:
            df[col] = "" if col in ["name", "category"] else np.nan
    df["corridor"] = "South Congress Avenue (SoCo)"
    df["name"] = df["name"].fillna("")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()
    return enrich_categories(df)

def corridor_csv(name):
    safe = {"South Congress Avenue (SoCo)": "soco_corridor_businesses.csv"}.get(name, "corridor_" + CORRIDORS[name]["short"].lower().replace(" ", "_").replace("/", "_") + ".csv")
    return DATA_DIR / safe


def fetch_corridor(name, radius_m=3000, buffer_m=100, eps_m=100, min_samples=5):
    """Download OSM road/business data, select named road segments and filter points to a 100m buffer."""
    try:
        import osmnx as ox
        import geopandas as gpd
        from shapely.geometry import Point
        from sklearn.cluster import DBSCAN
        from sklearn.neighbors import NearestNeighbors
    except ImportError as e:
        raise RuntimeError("Missing packages. Install requirements.txt first.") from e

    info = CORRIDORS[name]
    center = info["center"]
    # Use a smaller query area for Guadalupe to reduce server load.
    query_radius = radius_m
    ox.settings.use_cache = True
    ox.settings.log_console = False
    ox.settings.requests_timeout = 60

    # Try alternative Overpass servers if one is unavailable.
    endpoints = [
        "https://overpass.kumi.systems/api",
        "https://maps.mail.ru/osm/tools/overpass/api",
        "https://overpass.private.coffee/api",
        "https://overpass-api.de/api",
    ]

    graph = None
    errors = []

    for endpoint in endpoints:
        try:
            ox.settings.overpass_url = endpoint
            print(f"Trying Overpass endpoint: {endpoint}")

            graph = ox.graph_from_point(
                center,
                dist=query_radius,
                network_type="drive",
                simplify=True
            )

            if graph.number_of_edges() > 0:
                break

        except Exception as exc:
            errors.append(f"{endpoint}: {exc}")
            print(f"Endpoint failed: {exc}")
            graph = None

    if graph is None or graph.number_of_edges() == 0:
        detail = "\n".join(errors[-4:])
        raise RuntimeError(
            "OpenStreetMap road data could not be reached from the available Overpass servers. "
            "This is a network/server availability issue, not a corridor-name setting. "
            "Please retry when the public API is responding.\n\n" + detail
        )

    edges = ox.graph_to_gdfs(graph, nodes=False, edges=True).reset_index(drop=True)
    if "name" not in edges.columns:
        raise RuntimeError(f"OSM did not return road names for {name}. Try again or adjust the corridor section.")
    needles = [s.lower() for s in info["match"]]
    def matches(value):
        vals = value if isinstance(value, list) else [value]
        return any(n in str(v).lower() for v in vals for n in needles if v is not None)
    selected = edges[edges["name"].apply(matches)].copy()
    if selected.empty:
        raise RuntimeError(f"No road segments matching {name!r} were found in the {radius_m}m search area. Try increasing the search radius or check OSM road naming.")
    selected = selected[selected.geometry.notna()]
    if selected.empty:
        raise RuntimeError("Matched road segments did not have usable geometry.")
    crs_projected = selected.estimate_utm_crs()
    selected_m = selected.to_crs(crs_projected)
    # Keep the selected connected section nearest the configured center to avoid unrelated road fragments.
    center_pt = gpd.GeoSeries([Point(center[1], center[0])], crs="EPSG:4326").to_crs(crs_projected).iloc[0]
    selected_m["_distance"] = selected_m.geometry.distance(center_pt)
    selected_m = selected_m[selected_m["_distance"] <= radius_m * 0.8].copy()
    if selected_m.empty:
        raise RuntimeError("Road-name matches were found, but none were close enough to the configured corridor center.")
    corridor_union = selected_m.geometry.union_all() if hasattr(selected_m.geometry, "union_all") else selected_m.geometry.unary_union
    buffer = corridor_union.buffer(buffer_m)


    businesses = None
    business_errors = []

    for endpoint in endpoints:
        try:
            ox.settings.overpass_url = endpoint
            print(f"Downloading business data from: {endpoint}")

            businesses = ox.features_from_point(
                center,
                tags=TAGS,
                dist=query_radius
            )

            if not businesses.empty:
                break

        except Exception as exc:
            business_errors.append(f"{endpoint}: {exc}")
            print(f"Business request failed: {exc}")
            businesses = None

    if businesses is None or businesses.empty:
        raise RuntimeError(
            f"Could not download business data for {name}. "
            "All Overpass endpoints failed or returned no results.\n"
            + "\n".join(business_errors)
        )

    businesses = businesses[businesses.geometry.notna()].copy()
    if businesses.empty:
        raise RuntimeError("OSM returned no business features for this search area.")
    business_m = businesses.to_crs(crs_projected)
    business_m = business_m[business_m.geometry.intersects(buffer)].copy()
    if business_m.empty:
        raise RuntimeError("No business records were found inside the selected road buffer.")
    points = business_m.geometry.representative_point()
    points_ll = gpd.GeoSeries(points, crs=crs_projected).to_crs("EPSG:4326")
    result = pd.DataFrame({
        "name": business_m["name"].fillna("").astype(str).values if "name" in business_m.columns else [""] * len(business_m),
        "category": [category_for(row) for _, row in business_m.iterrows()],
        "latitude": points_ll.y.values,
        "longitude": points_ll.x.values,
    })
    # Retain raw OSM tags so later classification can be audited and improved.
    for tag in ["shop", "amenity", "office", "tourism", "leisure", "craft", "healthcare", "club", "public_transport", "building", "brand", "operator", "website", "name", "official_name", "short_name", "alt_name", "loc_name", "old_name"]:
        if tag in business_m.columns:
            result["osm_" + tag] = business_m[tag].fillna("").astype(str).values
    # Preserve language-specific name tags when OSMnx returns them as columns.
    for tag in ["name:en", "official_name:en", "short_name:en", "alt_name:en", "brand:en", "operator:en"]:
        if tag in business_m.columns:
            result["osm_" + tag] = business_m[tag].fillna("").astype(str).values
    result = recover_names(result)
    result["corridor"] = name
    result = result.dropna(subset=["latitude", "longitude"]).drop_duplicates(subset=["name", "category", "latitude", "longitude"])
    result = enrich_categories(result)
    result["data_source"] = "OpenStreetMap via OSMnx"
    result["retrieved_utc"] = pd.Timestamp.now(tz="UTC").isoformat()
    if len(result) > 1:
        coords = np.radians(result[["latitude", "longitude"]].to_numpy())
        model = DBSCAN(eps=eps_m / EARTH_RADIUS_M, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
        result["cluster"] = model.fit_predict(coords)
        nn = NearestNeighbors(n_neighbors=2, metric="haversine", algorithm="ball_tree").fit(coords)
        distances, _ = nn.kneighbors(coords)
        result["nearest_business_m"] = distances[:, 1] * EARTH_RADIUS_M
    elif len(result) == 1:
        result["cluster"] = -1
        result["nearest_business_m"] = np.nan
    else:
        result["cluster"] = pd.Series(dtype=int)
        result["nearest_business_m"] = pd.Series(dtype=float)
    out = corridor_csv(name)
    result.to_csv(out, index=False)
    # Persist matching roads for the combined map.
    selected_ll = selected_m.to_crs("EPSG:4326")
    file_key = CORRIDORS[name]["short"].lower().replace(" ", "_").replace("/", "_")
    selected_ll[["geometry", "name"]].to_file(DATA_DIR / ("roads_" + file_key + ".geojson"), driver="GeoJSON")
    # Save the actual corridor boundary polygon, created by buffering the matched road
    # centerline in a projected CRS so the width is measured in metres.
    boundary_m = gpd.GeoDataFrame(
        {"corridor": [name], "buffer_m": [buffer_m]},
        geometry=[buffer], crs=crs_projected
    )
    boundary_m.to_crs("EPSG:4326").to_file(
        DATA_DIR / ("boundary_" + file_key + ".geojson"), driver="GeoJSON"
    )
    return result


NAME_FIELDS = [
    "name", "osm_name", "name:en", "osm_name:en", "name_en", "osm_name_en",
    "official_name", "osm_official_name", "official_name:en", "osm_official_name:en",
    "short_name", "osm_short_name", "short_name:en", "osm_short_name:en",
    "alt_name", "osm_alt_name", "alt_name:en", "osm_alt_name:en",
    "loc_name", "osm_loc_name", "old_name", "osm_old_name",
    "brand", "osm_brand", "brand:en", "osm_brand:en",
    "operator", "osm_operator", "operator:en", "osm_operator:en",
]
INVALID_NAMES = {"", "nan", "none", "null", "false", "no", "yes", "unnamed", "unnamed business", "unknown"}


def recover_names(df):
    """Fill blank primary names only from actual name/brand/operator OSM fields."""
    if df is None or df.empty:
        return df
    result = df.copy()
    if "name" not in result.columns:
        result["name"] = ""
    result["name"] = result["name"].fillna("").astype(str).str.strip()
    sources = []
    for _, row in result.iterrows():
        current = str(row.get("name", "") or "").strip()
        if current.lower() not in INVALID_NAMES:
            sources.append("name" if current else "")
            continue
        recovered = ""
        recovered_from = ""
        # Prefer explicit names over brand/operator fallbacks.
        for field in NAME_FIELDS[1:20]:
            value = row.get(field, "")
            if pd.isna(value):
                continue
            value = str(value).strip()
            if value and value.lower() not in INVALID_NAMES:
                recovered, recovered_from = value, field
                break
        if not recovered:
            for field in NAME_FIELDS[20:]:
                value = row.get(field, "")
                if pd.isna(value):
                    continue
                value = str(value).strip()
                if value and value.lower() not in INVALID_NAMES:
                    recovered, recovered_from = value, field
                    break
        result.at[_, "name"] = recovered
        sources.append(recovered_from)
    result["name_source"] = sources
    return result


def make_point_labels(df):
    """Expose genuine recovered names only; never invent business/place names."""
    if df is None or df.empty:
        return df
    df = recover_names(df)
    df["display_name"] = df["name"].fillna("").astype(str).str.strip()
    return df


def remove_unnamed_nonbusiness_features(df):
    """Remove unnamed public-realm/infrastructure map objects, retaining named places and business candidates."""
    if df is None or df.empty:
        return df
    result = df.copy()

    def clean(value):
        if value is None or pd.isna(value):
            return ""
        return str(value).strip().lower().replace("_", " ").replace("-", " ")

    # These are map/infrastructure objects rather than identifiable business listings.
    # Match both the normalized category column and the underlying OSM tags because
    # the corridor CSVs do not all contain the same set of OSM columns.
    nonbusiness_categories = {
        "parking", "parking space", "parking entrance", "stop position",
        "bench", "waste basket", "waste disposal", "recycling",
        "bicycle parking", "shelter", "picnic table", "street lamp",
        "traffic signals", "crossing", "bus stop", "platform",
        "post box", "letter box", "telephone", "drinking water",
        "fountain", "artwork", "information", "garden", "bleachers",
        "slipway", "wastewater plant", "fire hydrant", "firepit",
    }
    infrastructure_tags = {
        ("amenity", "bench"), ("amenity", "waste basket"),
        ("amenity", "waste disposal"), ("amenity", "recycling"),
        ("amenity", "drinking water"), ("amenity", "fountain"),
        ("amenity", "bicycle parking"), ("amenity", "shelter"),
        ("amenity", "bus stop"), ("amenity", "toilets"),
        ("amenity", "shower"), ("amenity", "telephone"),
        ("public transport", "stop position"), ("public transport", "platform"),
        ("highway", "bus stop"), ("highway", "street lamp"),
        ("highway", "crossing"), ("highway", "traffic signals"),
        ("highway", "stop"), ("leisure", "picnic table"),
        ("leisure", "slipway"), ("man made", "wastewater plant"),
    }

    keep = []
    for _, row in result.iterrows():
        # A genuine name always wins: never remove a named place.
        name = clean(row.get("name", ""))
        if name and name not in INVALID_NAMES:
            keep.append(True)
            continue

        category = clean(row.get("category", ""))
        if category in nonbusiness_categories:
            keep.append(False)
            continue

        tags = set()
        for key in ["amenity", "public_transport", "highway", "leisure", "man_made"]:
            value = clean(row.get("osm_" + key, row.get(key, "")))
            if value:
                tag_key = "public transport" if key == "public_transport" else key.replace("_", " ")
                tags.add((tag_key, value))
        keep.append(not any(tag in infrastructure_tags for tag in tags))

    return result.loc[keep].copy()


def load_corridor(name):
    path = corridor_csv(name)
    if not path.exists():
        return pd.DataFrame(columns=["name", "category", "major_activity", "latitude", "longitude", "corridor"])
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=["name", "category", "major_activity", "latitude", "longitude", "corridor"])
    required = ["name", "category", "latitude", "longitude"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame(columns=required + ["corridor"])
    df["corridor"] = name
    df = recover_names(df)
    df = remove_unnamed_nonbusiness_features(df)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = enrich_categories(df)
    # Recompute spatial metrics with a consistent implementation when coordinates exist.
    if len(df) >= 2:
        try:
            from sklearn.cluster import DBSCAN
            from sklearn.neighbors import NearestNeighbors
            coords = np.radians(df[["latitude", "longitude"]].to_numpy())
            df["cluster"] = DBSCAN(eps=100 / EARTH_RADIUS_M, min_samples=5, metric="haversine", algorithm="ball_tree").fit_predict(coords)
            dist, _ = NearestNeighbors(n_neighbors=2, metric="haversine", algorithm="ball_tree").fit(coords).kneighbors(coords)
            df["nearest_business_m"] = dist[:, 1] * EARTH_RADIUS_M
        except Exception:
            pass
    elif len(df) == 1:
        df["cluster"] = -1
        df["nearest_business_m"] = np.nan
    return df

def activity_leaders_for(df):
    """Return observed activity leaders for corridors without a researched profile."""
    if df is None or df.empty:
        return "—", "—"
    col = "major_activity" if "major_activity" in df.columns else ("category" if "category" in df.columns else None)
    if not col:
        return "—", "—"
    values = df[col].fillna("Miscellaneous Retail & Services").astype(str).str.strip()
    values = values.replace("", "Miscellaneous Retail & Services")
    counts = values.value_counts()
    if counts.empty:
        return "—", "—"
    top_count = counts.iloc[0]
    leaders = [str(k) for k, v in counts.items() if v == top_count]
    others = [str(k) for k in counts.index if str(k) not in leaders][:4]
    return " and ".join(leaders), (", ".join(others) if others else "No other mapped activity groups")

def stats_for(df):
    n = len(df)
    named = df["name"].fillna("").astype(str).str.strip().str.lower().ne("").sum() if n and "name" in df else 0
    cats = df["major_activity"].fillna("Miscellaneous Retail & Services").astype(str) if n and "major_activity" in df else (df["category"].fillna("other").astype(str) if n and "category" in df else pd.Series(dtype=str))
    top = cats.value_counts().index[0] if len(cats) else "—"
    cluster_count = int(df.loc[pd.to_numeric(df.get("cluster", pd.Series(index=df.index, dtype=float)), errors="coerce") != -1, "cluster"].nunique()) if n and "cluster" in df else None
    noise = int((pd.to_numeric(df["cluster"], errors="coerce") == -1).sum()) if n and "cluster" in df else None
    avg_near = float(pd.to_numeric(df["nearest_business_m"], errors="coerce").mean()) if n and "nearest_business_m" in df else None
    return {"records": n, "named": int(named), "categories": int(cats.nunique()) if len(cats) else 0, "top": top, "clusters": cluster_count, "noise": noise, "avg_near": avg_near}

# Sidebar
with st.sidebar:
    st.markdown("## 🗺️ Austin Corridor Intelligence")
    st.caption("Commercial geography · OpenStreetMap · DBSCAN")
    pages = ["Overview", "Housing Affordability", "Corridor Explorer", "Business Analytics", "Corridor Comparison", "Combined Insights", "Data & Methodology", "Austin Corridor Map"]
    desired_page = st.session_state.get("page_override", "Overview")
    page = st.radio("NAVIGATION", pages, index=pages.index(desired_page) if desired_page in pages else 0, label_visibility="collapsed")
    st.divider()
    st.markdown("**Corridor data status**")
    for cname, info in CORRIDORS.items():
        exists = corridor_csv(cname).exists()
        st.markdown(f"<span style='color:{info['color']};font-size:1.1rem'>●</span> {info['short']} {'✓' if exists else '○'}", unsafe_allow_html=True)
    st.caption("✓ data available · ○ data not collected yet")

st.markdown('<div class="hero"><h1>Austin Corridor Intelligence</h1><p>Explore, analyse and compare eleven commercial corridors across Austin, Texas.</p></div>', unsafe_allow_html=True)

all_data = {name: load_corridor(name) for name in CORRIDORS}
ready_names = [name for name, df in all_data.items() if not df.empty]

if page == "Overview":
    total_records = sum(len(df) for df in all_data.values())
    ready_count = len(ready_names)
    unique_categories = len(set().union(*[set(df.get("major_activity", df["category"]).dropna().astype(str).unique()) for df in all_data.values() if not df.empty])) if ready_names else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Corridors planned", "11")
    c2.metric("Corridors with data", f"{ready_count}/11")
    c3.metric("Business records loaded", f"{total_records:,}")
    c4.metric("Categories observed", unique_categories)
    st.caption("The dashboard combines a 255-tract Austin-area housing export with mapped business records for the 11 study corridors. Business counts reflect the supplied OpenStreetMap-derived datasets.")
    st.markdown('<div class="section-title">Explore the eleven corridors</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, (name, info) in enumerate(CORRIDORS.items()):
        df = all_data[name]; s = stats_for(df)
        with cols[i % 3]:
            st.markdown(f"<div class='small-card' style='border-top:4px solid {info['color']};min-height:180px'><h3 style='margin:.1rem 0;color:#173c34'>{info['short']}</h3><p style='color:#687b76;font-size:.9rem'>{info['description']}</p><p><b>{s['records']:,}</b> business records {'· '+str(s['categories'])+' categories' if s['records'] else '· data not collected'}</p></div>", unsafe_allow_html=True)
            if st.button("Open corridor", key=f"open_{i}", width="stretch"):
                st.session_state["selected_corridor"] = name
                st.session_state["page_override"] = "Corridor Explorer"
                st.rerun()
            if st.button("Collect / refresh OSM data", key=f"collect_{i}", width="stretch"):
                with st.spinner(f"Collecting road and business data for {name}. This may take a few minutes..."):
                    try:
                        fetch_corridor(
                            name,
                            radius_m=info["search_radius_m"],
                            buffer_m=150,
                            eps_m=100,
                            min_samples=5,
                        )
                        st.success(f"Saved OSM data for {name}.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not collect {name}: {exc}")

elif page == "Corridor Explorer":
    default = st.session_state.get("selected_corridor", "South Congress Avenue (SoCo)")
    selected = st.selectbox("Select a corridor", list(CORRIDORS), index=list(CORRIDORS).index(default) if default in CORRIDORS else 0)
    st.session_state["selected_corridor"] = selected
    df = all_data[selected]
    info = CORRIDORS[selected]
    st.markdown(f"### <span style='color:{info['color']}'>●</span> {selected}", unsafe_allow_html=True)
    st.write(info["description"])
    if df.empty:
        st.warning("No dataset has been collected for this corridor yet.")
        st.write("Use **Overview → Collect missing corridor data** to download its OSM road and business records.")
    else:
        s = stats_for(df)
        a,b,c,d,e = st.columns(5)
        a.metric("Business records", f"{s['records']:,}")
        b.metric("Named records", f"{s['named']:,}")
        c.metric("Categories", s["categories"])
        d.metric("DBSCAN clusters", s["clusters"] if s["clusters"] is not None else "Not run")
        e.metric("Noise points", s["noise"] if s["noise"] is not None else "Not run")
        left,right = st.columns([1.6,1])
        with left:
            st.markdown("#### Business locations")
            try:
                import folium
                from streamlit_folium import st_folium
                valid_coords = df.dropna(subset=["latitude", "longitude"]).copy()
                if valid_coords.empty:
                    st.warning("No valid business coordinates are available for this corridor.")
                else:
                    center = [valid_coords["latitude"].mean(), valid_coords["longitude"].mean()]
                    # Disable all default basemaps, then add OpenStreetMap explicitly.
                    # This removes the Carto API-key watermark seen in the previous map.
                    m = folium.Map(
                        location=center, zoom_start=14, tiles=None, control_scale=True,
                        prefer_canvas=True, fade_animation=False, zoom_animation=False,
                        marker_zoom_animation=False,
                    )
                    folium.TileLayer(
                        tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
                        name="OpenStreetMap", overlay=False, control=True,
                        max_zoom=19, update_when_idle=True, keep_buffer=4,
                    ).add_to(m)
                    file_key = info["short"].lower().replace(" ", "_").replace("/", "_")
                    road_path = DATA_DIR / ("roads_" + file_key + ".geojson")
                    boundary_path = DATA_DIR / ("boundary_" + file_key + ".geojson")
                    # SoCo's reviewed study polygon is the preferred boundary. Always
                    # prefer it over a possibly stale boundary_soco.geojson generated by
                    # an earlier refresh; use the generated boundary only as a fallback.
                    if selected == "South Congress Avenue (SoCo)":
                        soco_boundary = DATA_DIR / "soco_corridor_area.geojson"
                        soco_roads = DATA_DIR / "soco_corridor_roads.geojson"
                        if soco_boundary.exists():
                            boundary_path = soco_boundary
                        if soco_roads.exists():
                            road_path = soco_roads
                    # Load the boundary geometry once, draw it once, and use the same
                    # geometry to keep displayed business markers inside the study area.
                    boundary_geom = None
                    boundary_gdf = None
                    boundary_source = None

                    if boundary_path.exists():
                        try:
                            import geopandas as gpd
                            boundary_gdf = gpd.read_file(boundary_path).to_crs("EPSG:4326")
                            boundary_gdf = boundary_gdf[
                                boundary_gdf.geometry.notna() & ~boundary_gdf.geometry.is_empty
                            ].copy()
                            if not boundary_gdf.empty:
                                boundary_geom = boundary_gdf.geometry.union_all()
                                boundary_source = boundary_path.name
                        except Exception as exc:
                            st.caption(f"Saved boundary could not be read; trying the road buffer instead. Details: {exc}")
                            boundary_gdf = None
                            boundary_geom = None

                    # If no valid polygon exists, create one from the saved corridor road
                    # centerline. Buffer in a projected CRS so metres are measured correctly.
                    if boundary_geom is None and road_path.exists():
                        try:
                            import geopandas as gpd
                            roads_gdf = gpd.read_file(road_path)
                            roads_gdf = roads_gdf[
                                roads_gdf.geometry.notna() & ~roads_gdf.geometry.is_empty
                            ].copy()
                            if not roads_gdf.empty:
                                projected = roads_gdf.to_crs(roads_gdf.estimate_utm_crs())
                                polygon = projected.geometry.union_all().buffer(int(info["buffer_m"]))
                                boundary_gdf = gpd.GeoDataFrame(
                                    {"corridor": [selected]},
                                    geometry=[polygon],
                                    crs=projected.crs
                                ).to_crs("EPSG:4326")
                                boundary_geom = boundary_gdf.geometry.union_all()
                                boundary_source = f"buffered from {road_path.name}"
                        except Exception as exc:
                            st.warning(f"Could not create a boundary from the saved roads: {exc}")

                    # Draw the polygon before points so the markers remain visible on top.
                    if boundary_gdf is not None and boundary_geom is not None:
                        try:
                            folium.GeoJson(
                                boundary_gdf.to_json(),
                                name="Corridor study boundary",
                                style_function=lambda feature: {
                                    "color": info["color"],
                                    "weight": 5,
                                    "fillColor": info["color"],
                                    "fillOpacity": 0.08,
                                    "opacity": 1.0,
                                    "dashArray": "8, 5",
                                },
                                tooltip=f"{selected} study boundary"
                            ).add_to(m)
                            minx, miny, maxx, maxy = boundary_gdf.total_bounds
                            m.fit_bounds(
                                [[miny, minx], [maxy, maxx]],
                                padding=(25, 25),
                                max_zoom=16
                            )
                        except Exception as exc:
                            st.caption(f"Boundary could not be drawn: {exc}")

                    # Filter markers against the exact polygon displayed on the map.
                    map_businesses = valid_coords.copy()
                    if boundary_geom is not None:
                        try:
                            from shapely.geometry import Point
                            inside = map_businesses.apply(
                                lambda row: boundary_geom.covers(
                                    Point(float(row["longitude"]), float(row["latitude"]))
                                ),
                                axis=1
                            )
                            map_businesses = map_businesses.loc[inside].copy()
                            st.caption(
                                f"Boundary: {boundary_source}. Showing {len(map_businesses)} "
                                f"businesses inside the study area out of {len(valid_coords)} "
                                "records with valid coordinates."
                            )
                        except Exception as exc:
                            st.warning(f"Could not filter markers to the boundary: {exc}")
                    else:
                        st.warning(
                            "No valid corridor polygon or road file was found. "
                            "All records with valid coordinates are shown, so the boundary cannot be verified."
                        )

                    # Draw plain points only: no names, tooltips, or popups.
                    for _, row in map_businesses.iterrows():
                        folium.CircleMarker(
                            location=[float(row["latitude"]), float(row["longitude"])],
                            radius=5,
                            color="#ffffff",
                            fill=True,
                            fill_color=info["color"],
                            fill_opacity=0.95,
                            weight=1.5,
                        ).add_to(m)
                    map_key = "corridor_map_" + info["short"].lower().replace(" ", "_").replace("/", "_")
                    st_folium(m, height=500, use_container_width=True, key=map_key)
            except ImportError:
                st.warning("Install folium and streamlit-folium to display the interactive map.")
                st.dataframe(df[[c for c in ["name","category","latitude","longitude"] if c in df]], width="stretch")
        with right:
            # Both charts are derived from the same loaded records and same activity classification.
            if "major_activity" not in df.columns:
                df = enrich_categories(df.copy())
            if "major_activity" in df.columns:
                activity_series = (
                    df["major_activity"]
                    .fillna("Miscellaneous Retail & Services")
                    .astype(str)
                    .str.strip()
                    .replace("", "Miscellaneous Retail & Services")
                    .value_counts()
                )
            else:
                activity_series = pd.Series(dtype="int64")
            counts = activity_series.sort_values(ascending=False)

            st.markdown("#### Signature activity profile")
            st.caption("Qualitative 1–5 profile informed by City of Austin corridor-planning documents and documented local business character. This is a researched corridor profile, not a count of businesses.")
            researched_profile = CORRIDOR_PROFILE.get(selected, {})
            if researched_profile:
                profile_series = pd.Series(researched_profile, dtype="float64").sort_values(ascending=True)
                profile_series.name = "Research-informed strength (1–5)"
                st.bar_chart(profile_series, horizontal=True)

                # Display the requested corridor leaders explicitly beneath the profile chart.
                leader_summary = CORRIDOR_LEADERS.get(selected)
                if leader_summary:
                    st.markdown("##### Corridor activity leaders")
                    st.dataframe(
                        pd.DataFrame([leader_summary], columns=["Leading activity", "Other strong activities"]),
                        hide_index=True,
                        width="stretch",
                    )
            else:
                st.markdown("##### Observed activity profile")
                st.caption("No separate planning-informed profile is configured for this corridor yet. This profile is calculated from its currently loaded OSM records.")
                if not counts.empty:
                    observed_profile = counts.sort_values(ascending=True).copy()
                    observed_profile.name = "Mapped records"
                    st.bar_chart(observed_profile, horizontal=True)
                else:
                    st.info("No mapped activity categories are available for this corridor.")
                observed_leader, observed_support = activity_leaders_for(df)
                st.markdown("##### Activity leaders from loaded records")
                st.dataframe(pd.DataFrame([{"Leading observed activity": observed_leader, "Other observed activities": observed_support}]), hide_index=True, width="stretch")

            st.markdown("#### Actual mapped business mix")
            st.caption("Observed counts in the currently loaded OpenStreetMap/sample CSV, classified from each record. This sample may be incomplete and is not a full business census.")
            if not counts.empty:
                count_chart = counts.copy()
                count_chart.name = "Mapped businesses"
                st.bar_chart(count_chart.sort_values(ascending=True), horizontal=True)
            else:
                st.info("No mapped business records are available for this corridor.")

        st.markdown("#### Quick findings")

        # Corridor-specific profile summary plus facts calculated from the selected corridor's records.
        leader_summary = CORRIDOR_LEADERS.get(selected, {})
        observed_leader, observed_support = activity_leaders_for(df)
        profile_leader = leader_summary.get("Leading activity", observed_leader)
        profile_support = leader_summary.get("Other strong activities", observed_support)

        if not counts.empty:
            mapped_top = str(counts.index[0])
            mapped_top_count = int(counts.iloc[0])
            tied_top = [str(cat) for cat, count in counts.items() if int(count) == mapped_top_count]
            mapped_leader_text = " and ".join(tied_top)
            st.write(f"**Signature profile leader:** {profile_leader}")
            st.write(f"**Other strong profile activities:** {profile_support}")
            st.write(
                f"**Most common activity in this corridor's loaded OSM sample:** "
                f"{mapped_leader_text} ({mapped_top_count} records)"
            )
        else:
            st.write(f"**Signature profile leader:** {profile_leader}")
            st.write(f"**Other strong profile activities:** {profile_support}")
            st.info("No mapped business records are available for this corridor, so a sample leader cannot be calculated.")

        category_col = "major_activity" if "major_activity" in df.columns else None
        distinct_categories = (
            int(df[category_col].fillna("Miscellaneous Retail & Services").astype(str).nunique())
            if category_col and not df.empty else 0
        )
        st.write(f"**Mapped business records:** {len(df):,}")
        st.write(f"**Distinct mapped activity categories:** {distinct_categories}")

        st.caption(
            "The signature profile describes the corridor's broader commercial character using planning sources. "
            "The mapped leader is calculated from the records currently loaded for this corridor, which may be an "
            "incomplete sample rather than a full business census. A difference between these two leaders is possible."
        )

        if s["avg_near"] is not None and not math.isnan(s["avg_near"]):
            st.write(f"**Mean nearest-business distance:** {s['avg_near']:.1f} m")

        st.markdown("#### Places along this corridor")
        st.caption("Names are taken from OSM name fields, with official/alternate names and brand/operator tags used only when the primary name is missing. Unnamed records are left unnamed rather than given invented labels.")

        labelled_df = make_point_labels(df)
        display = pd.DataFrame(index=labelled_df.index)
        display["Name"] = labelled_df["display_name"].replace("", "—")

        if "major_activity" in labelled_df.columns:
            activity = labelled_df["major_activity"].fillna("").astype(str).str.replace("_", " ").str.strip()
        elif "category" in labelled_df.columns:
            activity = labelled_df["category"].fillna("").astype(str).str.replace("_", " ").str.strip()
        else:
            activity = pd.Series(["Mapped place"] * len(labelled_df), index=labelled_df.index)
        display["Activity"] = activity.replace({"": "Other mapped place", "nan": "Other mapped place", "None": "Other mapped place"}).str.title()

        # Keep the public-facing directory tidy; hide raw OSM tag columns and null-heavy fields.
        for col, label in [("latitude", "Latitude"), ("longitude", "Longitude")]:
            if col in labelled_df.columns:
                display[label] = pd.to_numeric(labelled_df[col], errors="coerce").round(5)

        tag_candidates = ["shop", "amenity", "tourism", "office", "leisure", "craft", "healthcare", "public_transport", "historic"]
        def feature_type(row):
            for tag in tag_candidates:
                value = row.get("osm_" + tag, row.get(tag, ""))
                value = str(value or "").strip()
                if value and value.lower() not in {"nan", "none", "unknown", "no", "false"}:
                    return value.replace("_", " ").title()
            return "—"
        display["Map feature"] = labelled_df.apply(feature_type, axis=1)

        search = st.text_input("Search places by name, activity, or map feature", key="business_search")
        view = display.copy()
        if search:
            view = view[view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)]

        named_count = int(labelled_df["name"].fillna("").astype(str).str.strip().ne("").sum())
        recovered_count = int(labelled_df.get("name_source", pd.Series("", index=labelled_df.index)).fillna("").astype(str).str.strip().ne("").sum())
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Places shown", f"{len(view):,}")
        col_b.metric("With names", f"{named_count:,}")
        col_c.metric("Names available from OSM fields", f"{recovered_count:,}")

        st.dataframe(
            view,
            width="stretch",
            hide_index=True,
            height=420,
            column_config={
                "Name": st.column_config.TextColumn("Name", help="Recovered from available OSM name, alternate-name, brand, or operator fields; blank means no name was supplied.", width="large"),
                "Activity": st.column_config.TextColumn("Activity", width="medium"),
                "Latitude": st.column_config.NumberColumn("Latitude", format="%.5f"),
                "Longitude": st.column_config.NumberColumn("Longitude", format="%.5f"),
                "Map feature": st.column_config.TextColumn("Map feature", width="medium"),
            },
        )

        st.download_button(
            "Download corridor CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"{info['short'].lower().replace(' ','_')}_businesses.csv",
            mime="text/csv",
        )


elif page == "Business Analytics":
    st.markdown("## 📊 Business Analytics")
    st.write("Explore the observed business mix across the corridor datasets currently available on this device.")
    available = {name: df.copy() for name, df in all_data.items() if not df.empty}
    if not available:
        st.warning("No corridor datasets are loaded yet. Go to Overview and fetch a corridor from OpenStreetMap.")
    else:
        choices = ["All corridors"] + list(available.keys())
        choice = st.selectbox("Analyse", choices, key="analytics_corridor")
        frames = []
        for cname, data in available.items():
            if choice == "All corridors" or choice == cname:
                part = data.copy()
                part["corridor"] = cname
                frames.append(part)
        analysis = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if not analysis.empty:
            analysis = enrich_categories(analysis)
            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Business records", f"{len(analysis):,}")
            metric2.metric("Named businesses", f"{analysis['name'].fillna('').astype(str).str.strip().ne('').sum():,}")
            metric3.metric("Activity categories", int(analysis['major_activity'].nunique()))
            metric4.metric("Corridors represented", int(analysis['corridor'].nunique()))
            st.markdown("### Observed activity mix")
            mix = analysis["major_activity"].fillna("Miscellaneous Retail & Services").value_counts().sort_values(ascending=False)
            st.bar_chart(mix, horizontal=True)
            st.markdown("### Activity mix by corridor")
            cross = pd.crosstab(analysis["corridor"], analysis["major_activity"])
            st.dataframe(cross, width="stretch")
            st.markdown("### Search and inspect records")
            term = st.text_input("Filter by business name, raw category, or activity", key="analytics_search")
            view = analysis.copy()
            if term.strip():
                mask = view.astype(str).apply(lambda col: col.str.contains(term.strip(), case=False, na=False)).any(axis=1)
                view = view.loc[mask]
            st.caption(f"Showing {len(view):,} of {len(analysis):,} records. Counts describe the loaded OSM sample, not a complete business census.")
            st.dataframe(view, width="stretch", hide_index=True)
            st.download_button("Download analytics records (CSV)", view.to_csv(index=False).encode("utf-8"), "business_analytics.csv", "text/csv")

elif page == "Cluster Analysis":
    st.markdown("## 🧩 Cluster Analysis")
    st.write("DBSCAN groups nearby business locations. Cluster labels are recalculated from coordinates when data is loaded.")
    available = {name: df.copy() for name, df in all_data.items() if not df.empty}
    if not available:
        st.warning("No corridor datasets are loaded yet. Fetch data from the Overview page first.")
    else:
        chosen = st.selectbox("Choose corridor", list(available), key="cluster_corridor")
        cdf = available[chosen].copy()
        if "cluster" not in cdf.columns:
            try:
                from sklearn.cluster import DBSCAN
                coords = np.radians(cdf[["latitude", "longitude"]].dropna().to_numpy(dtype=float))
                labels = DBSCAN(eps=100 / EARTH_RADIUS_M, min_samples=5, metric="haversine", algorithm="ball_tree").fit_predict(coords) if len(coords) >= 2 else np.array([-1] * len(coords))
                cdf.loc[cdf[["latitude", "longitude"]].dropna().index, "cluster"] = labels
            except Exception as exc:
                st.error(f"Could not calculate DBSCAN clusters: {exc}")
        if "cluster" in cdf.columns:
            labels = pd.to_numeric(cdf["cluster"], errors="coerce").fillna(-1).astype(int)
            non_noise = sorted(x for x in labels.unique() if x != -1)
            noise_count = int((labels == -1).sum())
            k1, k2, k3 = st.columns(3)
            k1.metric("Clusters found", len(non_noise))
            k2.metric("Businesses in clusters", int((labels != -1).sum()))
            k3.metric("Noise / isolated points", noise_count)
            counts = labels[labels != -1].value_counts().sort_index()
            if not counts.empty:
                st.markdown("### Businesses per cluster")
                counts.index = [f"Cluster {x}" for x in counts.index]
                st.bar_chart(counts)
            else:
                st.info("DBSCAN did not find any dense clusters with the current settings. All points may be noise.")
            st.markdown("### Cluster summary")
            temp = cdf.copy()
            temp["cluster"] = labels
            temp["major_activity"] = temp.get("major_activity", pd.Series("Miscellaneous Retail & Services", index=temp.index)).fillna("Miscellaneous Retail & Services")
            summary = temp.groupby("cluster", dropna=False).agg(Businesses=("name", "size"), Activities=("major_activity", lambda x: x.nunique()), Mean_latitude=("latitude", "mean"), Mean_longitude=("longitude", "mean")).reset_index()
            summary["cluster"] = summary["cluster"].apply(lambda x: "Noise / unclustered" if int(x) == -1 else f"Cluster {int(x)}")
            st.dataframe(summary, width="stretch", hide_index=True)
            st.caption("Current default: haversine distance, 100 m epsilon, and minimum 5 points. Noise label −1 means a point was not assigned to a dense cluster; it does not mean the record is invalid.")
        st.markdown("### Spatial records")
        st.dataframe(cdf[[c for c in ["name", "major_activity", "latitude", "longitude", "cluster", "nearest_business_m"] if c in cdf.columns]], width="stretch", hide_index=True)

elif page == "Corridor Comparison":
    st.markdown("## ⚖️ Corridor Comparison")
    st.write("Compare only the datasets available locally. Missing corridors are shown as unavailable rather than filled with estimated counts.")
    rows = []
    for cname, cdf in all_data.items():
        stt = stats_for(cdf)
        leaders = CORRIDOR_LEADERS.get(cname, {})
        observed_leader, observed_support = activity_leaders_for(cdf)
        rows.append({"Corridor": cname, "Data status": "Available" if not cdf.empty else "Not collected", "Business records": stt["records"], "Named records": stt["named"], "Observed activity categories": stt["categories"], "Most common observed activity": stt["top"], "DBSCAN clusters": stt["clusters"] if stt["clusters"] is not None else "—", "Signature profile leader": leaders.get("Leading activity", observed_leader), "Other strong profile activities": leaders.get("Other strong activities", observed_support)})
    comparison = pd.DataFrame(rows)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Loaded business records")
        records = comparison.set_index("Corridor")["Business records"].astype(int)
        st.bar_chart(records)
    with c2:
        st.markdown("### Observed activity diversity")
        diversity = comparison.set_index("Corridor")["Observed activity categories"].astype(int)
        st.bar_chart(diversity)
    st.markdown("### Comparison table")
    st.dataframe(comparison, width="stretch", hide_index=True)
    st.download_button("Download corridor comparison (CSV)", comparison.to_csv(index=False).encode("utf-8"), "corridor_comparison.csv", "text/csv")
    st.info("For the six corridors with researched profiles, leaders are qualitative planning-informed themes. For newly added corridors without a researched profile, leader and supporting activities are derived from the loaded OSM sample and are shown as observed activity leaders, not as a separate planning study.")

elif page == "Standardized Buffer Comparison":
    st.markdown("## 📏 Standardized Buffer Comparison")
    st.write("Understand how the study boundary changes the commercial picture of a corridor. The same road centreline and the same saved business records are tested at 50 m, 100 m and 150 m.")
    st.info("A smaller buffer focuses on businesses closest to the street. A wider buffer captures more surrounding commercial activity, but may also include destinations that are less directly connected to the corridor. The best choice depends on the planning question—not simply the largest count.")
    selected_buffer_corridor = st.selectbox("Select corridor for buffer comparison", list(CORRIDORS), key="buffer_comparison_corridor")
    info = CORRIDORS[selected_buffer_corridor]
    cdf = all_data[selected_buffer_corridor]
    st.markdown(f"### {selected_buffer_corridor}")
    if cdf.empty:
        st.warning("No business dataset is loaded for this corridor. Collect its OSM records first; this page will not estimate missing businesses.")
    else:
        try:
            import geopandas as gpd
            import folium
            from streamlit_folium import st_folium
            from sklearn.cluster import DBSCAN

            file_key = info["short"].lower().replace(" ", "_").replace("/", "_")
            road_path = DATA_DIR / ("roads_" + file_key + ".geojson")
            if selected_buffer_corridor == "South Congress Avenue (SoCo)" and (DATA_DIR / "soco_corridor_roads.geojson").exists():
                road_path = DATA_DIR / "soco_corridor_roads.geojson"
            if not road_path.exists():
                st.error(f"Saved road geometry is missing: {road_path.name}. The buffer maps cannot be calculated without it.")
            else:
                roads = gpd.read_file(road_path)
                roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
                if roads.empty:
                    st.error("The saved road file contains no usable road geometry.")
                else:
                    metric_crs = roads.estimate_utm_crs()
                    roads_m = roads.to_crs(metric_crs)
                    centreline = roads_m.geometry.union_all()
                    points = cdf.copy()
                    points["latitude"] = pd.to_numeric(points["latitude"], errors="coerce")
                    points["longitude"] = pd.to_numeric(points["longitude"], errors="coerce")
                    points = points.dropna(subset=["latitude", "longitude"])
                    points = points[points["latitude"].between(-90, 90) & points["longitude"].between(-180, 180)]
                    points_gdf = gpd.GeoDataFrame(points, geometry=gpd.points_from_xy(points["longitude"], points["latitude"]), crs="EPSG:4326").to_crs(metric_crs)
                    activity_col = "major_activity" if "major_activity" in points_gdf.columns else ("category" if "category" in points_gdf.columns else None)
                    activity_groups = ["Food & drink", "Retail & shopping", "Health & care", "Professional & financial services", "Education & culture", "Accommodation & tourism", "Recreation & fitness", "Transport & automotive", "Community & public services", "Miscellaneous Retail & Services"]
                    comparison_rows, activity_table, share_table, subsets = [], {}, {}, {}
                    map_cols = st.columns(3)
                    for col, width_m in zip(map_cols, [50, 100, 150]):
                        polygon = centreline.buffer(width_m)
                        subset = points_gdf.loc[points_gdf.geometry.intersects(polygon)].copy()
                        subsets[width_m] = subset
                        n_points = len(subset)
                        if n_points >= 5:
                            coords = np.radians(subset[["latitude", "longitude"]].to_numpy(dtype=float))
                            labels = DBSCAN(eps=100 / EARTH_RADIUS_M, min_samples=5, metric="haversine", algorithm="ball_tree").fit_predict(coords)
                            cluster_count = len(set(labels) - {-1})
                            noise_count = int((labels == -1).sum())
                        else:
                            cluster_count, noise_count = 0, n_points
                        if activity_col and n_points:
                            vals = subset[activity_col].fillna("Miscellaneous Retail & Services").astype(str).str.strip().replace("", "Miscellaneous Retail & Services")
                            counts = vals.value_counts()
                        else:
                            counts = pd.Series(dtype=int)
                        activity_table[f"{width_m} m"] = counts
                        share_table[f"{width_m} m"] = (counts / counts.sum() * 100) if counts.sum() else counts
                        area_km2 = polygon.area / 1_000_000
                        diversity_count = int((counts > 0).sum())
                        comparison_rows.append({"Buffer": f"{width_m} m", "Business records": n_points, "Activity types represented": diversity_count, "Study area (km²)": round(area_km2, 3), "Businesses / km²": round(n_points / area_km2, 2) if area_km2 else 0, "DBSCAN clusters": cluster_count, "Noise points": noise_count})
                        with col:
                            st.markdown(f"#### {width_m} m buffer")
                            st.metric("Business records", f"{n_points:,}")
                            st.caption(f"{diversity_count} activity types · {area_km2:.2f} km²")
                            m = folium.Map(location=[info["center"][0], info["center"][1]], zoom_start=14, tiles="OpenStreetMap", control_scale=True)
                            polygon_ll = gpd.GeoSeries([polygon], crs=metric_crs).to_crs("EPSG:4326")
                            folium.GeoJson(polygon_ll.to_json(), name=f"{width_m} m study buffer", style_function=lambda feature, color=info["color"]: {"color": color, "weight": 2, "fillOpacity": 0.08}).add_to(m)
                            for _, row in subset.iterrows():
                                folium.CircleMarker(location=[float(row["latitude"]), float(row["longitude"])], radius=3, color="#ffffff", weight=1, fill=True, fill_color=info["color"], fill_opacity=0.9).add_to(m)
                            st_folium(m, height=340, use_container_width=True, key=f"{file_key}_standard_buffer_{width_m}")

                    comparison = pd.DataFrame(comparison_rows)
                    st.markdown("### 1. Overall buffer performance")
                    st.dataframe(comparison, hide_index=True, use_container_width=True)
                    st.download_button("Download buffer metrics (CSV)", comparison.to_csv(index=False).encode("utf-8"), file_name=f"{file_key}_buffer_comparison.csv", mime="text/csv")

                    st.markdown("### 2. Business mix: which activities are present?")
                    st.caption("Counts below are based on the activity classification already stored in the corridor dataset. They are observed mapped records, not a complete census of every business.")
                    activity_df = pd.DataFrame(activity_table).reindex(activity_groups).fillna(0).astype(int)
                    activity_df = activity_df.loc[activity_df.sum(axis=1).sort_values(ascending=False).index]
                    st.markdown("**Business counts by activity and buffer**")
                    st.bar_chart(activity_df, use_container_width=True)
                    share_df = pd.DataFrame(share_table).reindex(activity_df.index).fillna(0).round(1)
                    st.markdown("**Share of each buffer's mapped business mix (%)**")
                    st.bar_chart(share_df, use_container_width=True)
                    st.caption("Counts show scale; percentages show composition. A category's percentage can fall in a wider buffer even when its actual count increases, because other categories are also added.")

                    st.markdown("### 3. What does each wider buffer add?")
                    incremental_rows = []
                    for width_m, previous_m in [(50, 0), (100, 50), (150, 100)]:
                        current = subsets[width_m]
                        if previous_m == 0:
                            added = len(current)
                            label = "50 m baseline"
                        else:
                            previous_ids = set(subsets[previous_m].index)
                            added = len(current.loc[~current.index.isin(previous_ids)])
                            label = f"Additional records from {previous_m} m to {width_m} m"
                        incremental_rows.append({"Comparison": label, "Additional records": added})
                    incremental_df = pd.DataFrame(incremental_rows)
                    st.bar_chart(incremental_df.set_index("Comparison"), use_container_width=True)
                    st.dataframe(incremental_df, hide_index=True, use_container_width=True)

                    st.markdown("### 4. Buffer recommendation for this corridor")
                    # Transparent, descriptive score: balance mapped coverage, activity diversity and spatial density.
                    score_df = comparison.copy()
                    for metric in ["Business records", "Activity types represented", "Businesses / km²"]:
                        maximum = float(score_df[metric].max())
                        score_df[metric + " score"] = score_df[metric] / maximum if maximum > 0 else 0.0
                    score_df["Balanced score"] = (0.40 * score_df["Business records score"] + 0.30 * score_df["Activity types represented score"] + 0.30 * score_df["Businesses / km² score"]) * 100
                    best_idx = score_df["Balanced score"].idxmax()
                    recommended = score_df.loc[best_idx]
                    score_view = score_df[["Buffer", "Business records score", "Activity types represented score", "Businesses / km² score", "Balanced score"]].copy()
                    for column in score_view.columns[1:]:
                        score_view[column] = score_view[column].map(lambda value: f"{value:.1f}%")
                    st.dataframe(score_view, hide_index=True, use_container_width=True)
                    st.success(f"Balanced-data recommendation: **{recommended['Buffer']}** for {selected_buffer_corridor}.")
                    st.write(f"This buffer achieved the highest transparent balance score ({recommended['Balanced score']:.1f}/100), combining mapped business coverage (40%), activity diversity (30%) and business density (30%). It is a decision aid for this dataset—not a universal planning standard.")
                    density_winner = comparison.loc[comparison["Businesses / km²"].idxmax(), "Buffer"]
                    coverage_winner = comparison.loc[comparison["Business records"].idxmax(), "Buffer"]
                    diversity_winner = comparison.loc[comparison["Activity types represented"].idxmax(), "Buffer"]
                    st.markdown(f"""- **Closest-street focus:** 50 m is most useful when the question is about immediate frontage and walk-up activity. It may miss businesses just behind or beyond the street edge.
- **Balanced corridor view:** 100 m is a practical starting point when you want nearby commercial context without expanding too far. The score above checks whether it is actually balanced for this corridor.
- **Wider neighbourhood context:** 150 m is useful for capturing a broader business ecosystem, but can include destinations less directly tied to the corridor.
- **Highest observed density:** {density_winner}. **Highest mapped coverage:** {coverage_winner}. **Most activity types:** {diversity_winner}.""")
                    st.warning("Interpretation caution: buffer counts depend on OSM coverage, saved road geometry, corridor length and record quality. A wider buffer naturally tends to include more points. Do not interpret these counts as official business totals or conclude that one buffer is universally best. Compare corridors using the same buffer width and collection method.")
                    st.markdown("### 5. Suggested planning use")
                    st.write("Use 50 m for street-frontage audits and pedestrian-facing retail; 100 m for a consistent corridor business profile; and 150 m for neighbourhood catchment, supporting services and broader land-use context. For cross-corridor benchmarking, keep the same buffer width, coordinate validation, activity taxonomy and OSM collection date across every corridor.")
        except ImportError as exc:
            st.error(f"Buffer comparison requires GeoPandas, Folium, streamlit-folium and scikit-learn: {exc}")
        except Exception as exc:
            st.error(f"Buffer comparison could not be calculated from the saved road and business data: {exc}")

elif page == "Point Density":
    st.markdown("## 🔵 Point Density Analysis")
    st.write("Calculates mapped business-point density using only valid coordinates located inside the 150 m road-buffer study area. This is mapped-point density, not a complete business census.")
    rows = []
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        for cname, cdf in all_data.items():
            info = CORRIDORS[cname]
            key = info["short"].lower().replace(" ", "_").replace("/", "_")
            road_path = DATA_DIR / ("roads_" + key + ".geojson")
            if not road_path.exists():
                rows.append({"Corridor": cname, "Mapped points inside buffer": "—", "Road length (km)": "—", "150 m study area (km²)": "—", "Points/km²": "—", "Status": "Road file missing"})
                continue
            roads = gpd.read_file(road_path)
            roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
            if roads.empty:
                rows.append({"Corridor": cname, "Mapped points inside buffer": 0, "Road length (km)": 0, "150 m study area (km²)": 0, "Points/km²": "—", "Status": "No usable road geometry"})
                continue
            metric_crs = roads.estimate_utm_crs()
            roads_m = roads.to_crs(metric_crs)
            road_union = roads_m.geometry.union_all()
            study_area = road_union.buffer(150)
            area_km2 = study_area.area / 1_000_000
            length_km = road_union.length / 1000

            points = cdf.copy()
            for col in ["latitude", "longitude"]:
                if col not in points.columns:
                    points[col] = np.nan
                points[col] = pd.to_numeric(points[col], errors="coerce")
            points = points.dropna(subset=["latitude", "longitude"])
            points = points[points["latitude"].between(-90, 90) & points["longitude"].between(-180, 180)]
            if points.empty:
                inside_count = 0
            else:
                points_gdf = gpd.GeoDataFrame(
                    points,
                    geometry=gpd.points_from_xy(points["longitude"], points["latitude"]),
                    crs="EPSG:4326",
                ).to_crs(metric_crs)
                inside_count = int(points_gdf.geometry.within(study_area).sum())
            density = inside_count / area_km2 if area_km2 > 0 else np.nan
            rows.append({
                "Corridor": cname,
                "Mapped points inside buffer": inside_count,
                "Road length (km)": round(length_km, 2),
                "150 m study area (km²)": round(area_km2, 3),
                "Points/km²": round(density, 2) if pd.notna(density) else "—",
                "Status": "Calculated",
            })
        density_df = pd.DataFrame(rows)
        st.dataframe(density_df, width="stretch", hide_index=True)
        st.markdown("### Mapped points inside each corridor buffer")
        chart_df = density_df[pd.to_numeric(density_df["Mapped points inside buffer"], errors="coerce").notna()].copy()
        if not chart_df.empty:
            st.bar_chart(chart_df.set_index("Corridor")["Mapped points inside buffer"])
        st.download_button("Download point density summary (CSV)", density_df.to_csv(index=False).encode("utf-8"), "corridor_point_density.csv", "text/csv")
        st.caption("Study area is the union of saved road lines buffered by 150 m, so overlapping buffer areas are counted once. Only valid point coordinates inside this polygon contribute to the density numerator.")
    except Exception as exc:
        st.error(f"Point density analysis could not be calculated: {exc}")

elif page == "Road Connectivity":
    st.markdown("## 🛣️ Road Connectivity Analysis")
    st.write("Builds a planar road-line graph from the saved road geometry. Intersections are estimated after noding crossing linework; results are geometric indicators, not a substitute for a fully attributed turn-restriction road-routing graph.")
    rows = []
    try:
        import geopandas as gpd
        import networkx as nx
        from shapely.geometry import LineString, MultiLineString, GeometryCollection
        from shapely.ops import unary_union

        for cname, cdf in all_data.items():
            info = CORRIDORS[cname]
            key = info["short"].lower().replace(" ", "_").replace("/", "_")
            road_path = DATA_DIR / ("roads_" + key + ".geojson")
            if not road_path.exists():
                rows.append({"Corridor": cname, "Road length (km)": "—", "Graph nodes": "—", "Graph edges": "—", "Intersections (degree ≥ 3)": "—", "Dead-end nodes": "—", "Connected components": "—", "Average node degree": "—", "Intersection density (/km²)": "—", "Status": "Road file missing"})
                continue
            roads = gpd.read_file(road_path)
            roads = roads[roads.geometry.notna() & ~roads.geometry.is_empty].copy()
            if roads.empty:
                rows.append({"Corridor": cname, "Road length (km)": 0, "Graph nodes": 0, "Graph edges": 0, "Intersections (degree ≥ 3)": 0, "Dead-end nodes": 0, "Connected components": 0, "Average node degree": "—", "Intersection density (/km²)": "—", "Status": "No usable road geometry"})
                continue

            metric_crs = roads.estimate_utm_crs()
            roads_m = roads.to_crs(metric_crs)
            line_geometries = [g for g in roads_m.geometry if g is not None and not g.is_empty]
            noded = unary_union(line_geometries)
            if isinstance(noded, (LineString, MultiLineString)):
                noded_lines = [noded] if isinstance(noded, LineString) else list(noded.geoms)
            elif isinstance(noded, GeometryCollection):
                noded_lines = [g for g in noded.geoms if isinstance(g, LineString)]
            else:
                noded_lines = []

            graph = nx.Graph()
            for line in noded_lines:
                coords = list(line.coords)
                for a, b in zip(coords[:-1], coords[1:]):
                    # Round projected coordinates to decimetres to merge coincident nodes robustly.
                    u = (round(a[0], 1), round(a[1], 1))
                    v = (round(b[0], 1), round(b[1], 1))
                    if u != v:
                        graph.add_edge(u, v, length_m=math.hypot(v[0] - u[0], v[1] - u[1]))

            node_count = graph.number_of_nodes()
            edge_count = graph.number_of_edges()
            degrees = dict(graph.degree())
            intersections = sum(1 for degree in degrees.values() if degree >= 3)
            dead_ends = sum(1 for degree in degrees.values() if degree == 1)
            avg_degree = float(np.mean(list(degrees.values()))) if degrees else np.nan
            components = nx.number_connected_components(graph) if node_count else 0
            road_length_km = sum(data["length_m"] for _, _, data in graph.edges(data=True)) / 1000
            study_area_km2 = unary_union(line_geometries).buffer(150).area / 1_000_000
            intersection_density = intersections / study_area_km2 if study_area_km2 > 0 else np.nan
            rows.append({
                "Corridor": cname,
                "Road length (km)": round(road_length_km, 2),
                "Graph nodes": node_count,
                "Graph edges": edge_count,
                "Intersections (degree ≥ 3)": intersections,
                "Dead-end nodes": dead_ends,
                "Connected components": components,
                "Average node degree": round(avg_degree, 2) if pd.notna(avg_degree) else "—",
                "Intersection density (/km²)": round(intersection_density, 2) if pd.notna(intersection_density) else "—",
                "Status": "Calculated" if node_count else "No graph could be built",
            })

        connectivity_df = pd.DataFrame(rows)
        st.dataframe(connectivity_df, width="stretch", hide_index=True)
        st.download_button("Download road connectivity summary (CSV)", connectivity_df.to_csv(index=False).encode("utf-8"), "corridor_road_connectivity.csv", "text/csv")
        st.caption("Road lines are noded geometrically before graph construction. Degree ≥ 3 is used as an intersection proxy; degree 1 indicates a dead end. Connected components reveal disconnected linework. Results depend on the completeness and topology of the saved OSM road geometry.")
    except Exception as exc:
        st.error(f"Road connectivity analysis could not be calculated: {exc}")

elif page == "Data & Methodology":
    st.markdown("## 📚 Data & Methodology")
    st.write("This page documents the two datasets, the simple calculations used, and the limits of comparing housing and commercial activity.")
    st.markdown("### Study corridors")
    st.dataframe(pd.DataFrame([{"Corridor": name, "Reference centre (lat, lon)": f"{info['center'][0]:.4f}, {info['center'][1]:.4f}", "Search radius (m)": info["search_radius_m"], "Study buffer (m)": info["buffer_m"], "Commercial character": info["description"]} for name, info in CORRIDORS.items()]), width="stretch", hide_index=True)
    st.markdown("### Data source and collection")
    st.markdown("- **Source:** OpenStreetMap features and road-network data, retrieved through OSMnx when a corridor is fetched.\n- **Storage:** CSV files are stored in the app's `data` directory; matched roads and study boundaries may be saved as GeoJSON.\n- **Study boundary:** selected road segments buffered by a configured distance in a projected coordinate reference system. It is an analytical boundary, not an official zoning or legal boundary.\n- **Refreshes:** public Overpass services can time out or rate-limit requests. A failed fetch should be retried later; the app does not substitute fabricated business counts.")
    st.markdown("### Activity classification")
    st.write("The app classifies each record into broad activity groups using available OSM tags first, then name/category fallbacks for older CSVs. Raw source categories and `osm_` fields are retained where available so the classification can be audited.")
    st.dataframe(pd.DataFrame([{"Activity group": x} for x in ["Food & drink", "Retail & shopping", "Health & care", "Professional & financial services", "Education & culture", "Accommodation & tourism", "Recreation & fitness", "Transport & automotive", "Community & public services", "Miscellaneous Retail & Services"]]), width="stretch", hide_index=True)
    st.markdown("### Spatial methods used in the corridor dataset")
    st.markdown("- **Algorithm:** DBSCAN using haversine distance on latitude/longitude coordinates.\n- **Default epsilon:** 100 metres.\n- **Default minimum samples:** 5 points.\n- **Cluster labels:** non-negative values identify dense groups; `-1` identifies noise/unclustered points.\n- **Nearest-business distance:** distance to the nearest other record, estimated from the coordinates; it is not a walking-route distance.")
    st.markdown("### Housing affordability")
    st.markdown("- **Geography:** 255 Census tracts across Travis, Williamson and Hays counties in the supplied Austin-area export.\n- **Affordability benchmark:** monthly median gross rent × 12 ÷ 0.30 gives the annual income required for rent to equal 30% of income.\n- **Rent burden:** the supplied tract-level rent-to-income share is compared with the 30% screening threshold.\n- **Corridor connection:** official Texas Census tract polygons are intersected with each saved corridor study boundary. The resulting indicators are area-weighted tract-level contextual estimates, not household-level corridor medians.")
    st.markdown("### Interpretation and limitations")
    st.markdown("- OpenStreetMap is community-maintained and can omit businesses, contain duplicates, or have inconsistent tagging.\n- A downloaded sample is **not** a complete business census and should not be treated as official economic statistics.\n- A qualitative signature profile is a research-informed description of corridor character; it is not computed from the raw business counts.\n- Housing indicators are calculated from intersecting Census tracts using land-area weights. These contextual estimates are not household-level corridor values and do not establish causation.")
    status = pd.DataFrame([{"Corridor": name, "CSV path": str(corridor_csv(name).relative_to(BASE_DIR)) if corridor_csv(name).is_relative_to(BASE_DIR) else str(corridor_csv(name)), "File exists": corridor_csv(name).exists(), "Loaded records": len(all_data[name])} for name in CORRIDORS])
    st.markdown("### Local dataset status")
    st.dataframe(status, width="stretch", hide_index=True)
    st.download_button("Download dataset status (CSV)", status.to_csv(index=False).encode("utf-8"), "dataset_status.csv", "text/csv")



elif page == "Housing Affordability":
    st.markdown("## 🏠 Housing Affordability")
    st.write("Understand rent and renter-income conditions around each of Austin's 11 commercial corridors.")
    st.info("**In simple words:** We compare the typical rent in overlapping Census tracts with the typical renter-household income, then estimate the income needed to keep rent at 30% of income.")

    summary_path = DATA_DIR / "housing_affordability_tract_summary.csv"
    raw_path = DATA_DIR / "Austin_Housing_Affordability.csv"
    housing = pd.DataFrame()
    if summary_path.exists():
        housing = pd.read_csv(summary_path, dtype={"GEOID": str})
    elif raw_path.exists():
        raw = pd.read_csv(raw_path, dtype={"geoid": str})
        rent_id = "housing.national_tracts_v3.median_gross_rent_usd"
        income_id = "people.comprehensive_v3.median_renter_household_income_usd"
        headroom_id = "housing.national_tracts_v3.median_renter_income_30pct_headroom_vs_median_gross_rent_usd"
        share_id = "housing.national_tracts_v3.median_gross_rent_to_median_renter_income_share"
        vals = raw.pivot(index="geoid", columns="metric_id", values="value")
        for metric in [rent_id, income_id, headroom_id, share_id]:
            if metric not in vals.columns:
                vals[metric] = np.nan
        housing = pd.DataFrame({
            "GEOID": vals.index.astype(str),
            "Median gross rent (monthly USD)": vals[rent_id].values,
            "Median renter household income (annual USD)": vals[income_id].values,
            "Income required at 30% benchmark (annual USD)": vals[rent_id].values * 12 / 0.30,
            "Rent-to-income share": vals[share_id].values,
            "Monthly headroom at 30% benchmark (USD)": vals[headroom_id].values,
        })
    else:
        st.error("Housing data is missing. Add housing_affordability_tract_summary.csv to the app's data folder.")

    if not housing.empty:
        housing["GEOID"] = housing["GEOID"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(11)
        numeric_cols = [
            "Median gross rent (monthly USD)",
            "Median renter household income (annual USD)",
            "Income required at 30% benchmark (annual USD)",
            "Rent-to-income share",
            "Monthly headroom at 30% benchmark (USD)",
        ]
        for col in numeric_cols:
            housing[col] = pd.to_numeric(housing[col], errors="coerce")

        boundary_files = {
            "South Congress Avenue (SoCo)": ["boundary_soco.geojson"],
            "South Lamar Boulevard": ["boundary_south_lamar.geojson"],
            "East Riverside Drive": ["boundary_east_riverside.geojson"],
            "Burnet Road": ["boundary_burnet_road.geojson"],
            "North Lamar Boulevard": ["boundary_north_lamar.geojson"],
            "Guadalupe Street (The Drag)": ["boundary_guadalupe___the_drag.geojson", "boundary_guadalupe_the_drag.geojson"],
            "Congress Avenue (Downtown)": ["boundary_congress_ave.geojson", "boundary_congress_avenue.geojson"],
            "Manor Road": ["boundary_manor_road.geojson"],
            "Airport Boulevard": ["boundary_airport_blvd.geojson", "boundary_airport_boulevard.geojson"],
            "Research Boulevard (US 183)": ["boundary_research_blvd.geojson", "boundary_research_boulevard.geojson"],
            "Cameron Road": ["boundary_cameron_road.geojson"],
        }
        tract_candidates = [DATA_DIR / "census_tracts" / "tl_2024_48_tract.shp"]
        tract_dir = DATA_DIR / "census_tracts"
        if tract_dir.exists():
            tract_candidates += sorted(tract_dir.glob("*.shp"))
        tract_candidates += sorted(DATA_DIR.glob("*tract*.shp"))
        tract_path = next((p for p in tract_candidates if p.exists()), None)
        corridor_results = []

        if tract_path is not None:
            try:
                import geopandas as gpd
                tracts = gpd.read_file(tract_path)
                if tracts.crs is None:
                    raise ValueError("The Census tract shapefile has no CRS. Use the official TIGER shapefile including its .prj file.")
                if "GEOID" not in tracts.columns:
                    if {"STATEFP", "COUNTYFP", "TRACTCE"}.issubset(tracts.columns):
                        tracts["GEOID"] = tracts["STATEFP"].astype(str).str.zfill(2) + tracts["COUNTYFP"].astype(str).str.zfill(3) + tracts["TRACTCE"].astype(str).str.zfill(6)
                    else:
                        raise ValueError("The tract file needs a GEOID field or STATEFP, COUNTYFP and TRACTCE fields.")
                tracts["GEOID"] = tracts["GEOID"].astype(str).str.zfill(11)
                tracts = tracts[["GEOID", "geometry"]].merge(housing, on="GEOID", how="inner")
                tracts = tracts[tracts.geometry.notna() & ~tracts.geometry.is_empty].copy()
                if tracts.empty:
                    raise ValueError("No Census tract GEOIDs matched the housing table.")
                tracts_m = tracts.to_crs("EPSG:26914")

                for cname in CORRIDORS:
                    bpath = next((DATA_DIR / fn for fn in boundary_files.get(cname, []) if (DATA_DIR / fn).exists()), None)
                    if bpath is None:
                        corridor_results.append({"Corridor": cname, "Status": "Boundary file missing"})
                        continue
                    boundary = gpd.read_file(bpath)
                    if boundary.crs is None:
                        boundary = boundary.set_crs("EPSG:4326")
                    boundary_m = boundary.to_crs("EPSG:26914")
                    boundary_geom = boundary_m.geometry.union_all()
                    if boundary_geom is None or boundary_geom.is_empty:
                        corridor_results.append({"Corridor": cname, "Status": "Empty boundary"})
                        continue
                    clipped = tracts_m.copy()
                    clipped["intersection_area_m2"] = clipped.geometry.intersection(boundary_geom).area
                    clipped = clipped[clipped["intersection_area_m2"] > 0].copy()
                    if clipped.empty:
                        corridor_results.append({"Corridor": cname, "Status": "No tract overlap"})
                        continue
                    row = {"Corridor": cname, "Status": "Calculated", "Tracts intersecting": int(clipped["GEOID"].nunique())}
                    for col in numeric_cols:
                        valid = clipped[col].notna() & clipped["intersection_area_m2"].gt(0)
                        if valid.any():
                            weights = clipped.loc[valid, "intersection_area_m2"]
                            row[col] = float(np.average(clipped.loc[valid, col], weights=weights))
                            row[col + " — valid tracts"] = int(clipped.loc[valid, "GEOID"].nunique())
                        else:
                            row[col] = np.nan
                            row[col + " — valid tracts"] = 0
                    rent = row.get("Median gross rent (monthly USD)", np.nan)
                    income = row.get("Median renter household income (annual USD)", np.nan)
                    required = (rent * 12 / 0.30) if pd.notna(rent) else np.nan
                    row["Income required at 30% benchmark (annual USD)"] = required
                    row["Annual income gap (required minus actual)"] = required - income if pd.notna(required) and pd.notna(income) else np.nan
                    share = row.get("Rent-to-income share", np.nan)
                    if pd.isna(share) and pd.notna(rent) and pd.notna(income) and income > 0:
                        share = rent * 12 / income
                        row["Rent-to-income share"] = share
                    row["Rent burden status"] = ("Above 30% benchmark" if share > 0.30 else "At 30% benchmark" if np.isclose(share, 0.30) else "Below 30% benchmark") if pd.notna(share) else "Data unavailable"
                    corridor_results.append(row)
            except Exception as exc:
                st.error(f"Could not calculate corridor-wise housing indicators: {exc}")
        else:
            st.warning("The housing CSV is available, but the Census tract shapefile was not found. Put the extracted TIGER files in data/census_tracts/ to calculate corridor-wise results.")
            st.code("data/census_tracts/tl_2024_48_tract.shp\ndata/census_tracts/tl_2024_48_tract.shx\ndata/census_tracts/tl_2024_48_tract.dbf\ndata/census_tracts/tl_2024_48_tract.prj", language="text")

        if corridor_results:
            result_df = pd.DataFrame(corridor_results)
            calculated = result_df[result_df.get("Status", pd.Series(index=result_df.index, dtype=str)).eq("Calculated")].copy()
            st.markdown("### 1. Quick summary")
            if not calculated.empty:
                share_valid = calculated["Rent-to-income share"].dropna() if "Rent-to-income share" in calculated else pd.Series(dtype=float)
                gap_valid = calculated["Annual income gap (required minus actual)"].dropna() if "Annual income gap (required minus actual)" in calculated else pd.Series(dtype=float)
                a, b, c, d = st.columns(4)
                a.metric("Corridors calculated", f"{len(calculated)} / 11")
                b.metric("Corridors above 30%", int((share_valid > 0.30).sum()) if len(share_valid) else "—")
                c.metric("Corridors below 30%", int((share_valid < 0.30).sum()) if len(share_valid) else "—")
                d.metric("Corridors with income gap", int(gap_valid.notna().sum()))
                st.caption("Counts are based only on corridors with a calculated result and available values. These are area-weighted tract indicators, not household-level measurements.")
            else:
                st.warning("No corridor result could be calculated. Check that all corridor boundary files and Census tract files are present.")

            st.markdown("### 2. Compare all 11 corridors")
            st.write("See monthly rent, annual renter income, income needed under the 30% rule, and the estimated annual gap side by side.")
            display_cols = [
                "Corridor", "Status", "Tracts intersecting",
                "Median gross rent (monthly USD)",
                "Median renter household income (annual USD)",
                "Income required at 30% benchmark (annual USD)",
                "Annual income gap (required minus actual)",
                "Rent-to-income share", "Rent burden status"
            ]
            display = result_df[[c for c in display_cols if c in result_df.columns]].copy()
            rename = {
                "Corridor": "Corridor", "Status": "Calculation status", "Tracts intersecting": "Tracts overlapping",
                "Median gross rent (monthly USD)": "Typical monthly rent",
                "Median renter household income (annual USD)": "Typical annual renter income",
                "Income required at 30% benchmark (annual USD)": "Annual income needed",
                "Annual income gap (required minus actual)": "Annual income gap (+ = shortfall)",
                "Rent-to-income share": "Rent share of income", "Rent burden status": "Affordability indicator"
            }
            display = display.rename(columns=rename)
            for col in ["Typical monthly rent", "Typical annual renter income", "Annual income needed", "Annual income gap (+ = shortfall)"]:
                if col in display:
                    display[col] = display[col].map(lambda x: f"${x:,.0f}" if pd.notna(x) else "Not available")
            if "Rent share of income" in display:
                display["Rent share of income"] = display["Rent share of income"].map(lambda x: f"{x:.1%}" if pd.notna(x) else "Not available")
            st.dataframe(display, width="stretch", hide_index=True)
            st.download_button("⬇️ Download corridor comparison (CSV)", result_df.to_csv(index=False).encode("utf-8"), "housing_affordability_by_corridor.csv", "text/csv")

            if not calculated.empty:
                st.markdown("### 3. Rent compared with the 30% benchmark")
                chart_share = calculated.dropna(subset=["Rent-to-income share"])[["Corridor", "Rent-to-income share"]].sort_values("Rent-to-income share")
                if not chart_share.empty:
                    st.bar_chart(chart_share.set_index("Corridor"), horizontal=True)
                    st.caption("The 30% benchmark is the screening threshold. Higher percentages mean rent takes a larger share of the reported renter income.")
                st.markdown("### 4. Actual income compared with income needed")
                income_chart = calculated[["Corridor", "Median renter household income (annual USD)", "Income required at 30% benchmark (annual USD)"]].dropna()
                if not income_chart.empty:
                    income_chart = income_chart.set_index("Corridor").rename(columns={"Median renter household income (annual USD)": "Reported renter income", "Income required at 30% benchmark (annual USD)": "Income needed at 30% rent rule"})
                    st.bar_chart(income_chart, horizontal=True)
                    st.caption("This compares area-weighted tract estimates. It is not a comparison of individual households.")
                else:
                    st.info("This chart needs both rent and renter-income values for at least one corridor.")

                st.markdown("### 5. Explore one corridor")
                selected_corridor = st.selectbox("Choose a corridor", calculated["Corridor"].tolist(), key="housing_corridor_selector")
                item = calculated.loc[calculated["Corridor"].eq(selected_corridor)].iloc[0]
                x1, x2, x3, x4 = st.columns(4)
                rent_value = item.get("Median gross rent (monthly USD)", np.nan)
                income_value = item.get("Median renter household income (annual USD)", np.nan)
                required_value = item.get("Income required at 30% benchmark (annual USD)", np.nan)
                gap_value = item.get("Annual income gap (required minus actual)", np.nan)
                x1.metric("Monthly rent", f"${rent_value:,.0f}" if pd.notna(rent_value) else "Not available")
                x2.metric("Annual renter income", f"${income_value:,.0f}" if pd.notna(income_value) else "Not available")
                x3.metric("Income needed", f"${required_value:,.0f}" if pd.notna(required_value) else "Not available")
                x4.metric("Annual income gap", f"${gap_value:,.0f}" if pd.notna(gap_value) else "Not available", help="Positive = income shortfall; negative = income above the 30% benchmark requirement.")
                share_value = item.get("Rent-to-income share", np.nan)
                if pd.notna(share_value):
                    if share_value > 0.30:
                        st.warning(f"For {selected_corridor}, the rent-to-income indicator is {share_value:.1%}, above the 30% screening benchmark.")
                    elif np.isclose(share_value, 0.30):
                        st.info(f"For {selected_corridor}, the rent-to-income indicator is around the 30% screening benchmark.")
                    else:
                        st.success(f"For {selected_corridor}, the rent-to-income indicator is {share_value:.1%}, below the 30% screening benchmark.")
                detail_rows = [
                    {"What this means": "Census tracts overlapping this corridor", "Result": int(item.get("Tracts intersecting", 0))},
                    {"What this means": "Tracts with rent data", "Result": int(item.get("Median gross rent (monthly USD) — valid tracts", 0))},
                    {"What this means": "Tracts with renter-income data", "Result": int(item.get("Median renter household income (annual USD) — valid tracts", 0))},
                    {"What this means": "Tracts with rent-to-income data", "Result": int(item.get("Rent-to-income share — valid tracts", 0))},
                ]
                st.markdown("**How much data supports this corridor?**")
                st.dataframe(pd.DataFrame(detail_rows), hide_index=True, width="stretch")

            st.markdown("### 6. Understand the numbers")
            definitions = pd.DataFrame([
                {"Simple label": "Typical monthly rent", "Meaning": "Area-weighted average of the Census tracts' reported median monthly gross rent."},
                {"Simple label": "Typical annual renter income", "Meaning": "Area-weighted average of the tracts' reported median annual renter-household income."},
                {"Simple label": "Income needed", "Meaning": "Monthly rent × 12 ÷ 0.30. The annual income needed for rent to equal 30% of income."},
                {"Simple label": "Annual income gap", "Meaning": "Income needed minus reported renter income. Positive means a shortfall; negative means income is above the benchmark requirement."},
                {"Simple label": "Rent share of income", "Meaning": "Annual rent divided by annual renter income. Above 30% is above the screening benchmark."},
                {"Simple label": "Tracts overlapping", "Meaning": "Number of Census tract polygons that intersect the corridor study boundary."},
                {"Simple label": "Valid tracts", "Meaning": "Number of overlapping tracts with a non-missing value for that particular metric."},
            ])
            st.dataframe(definitions, hide_index=True, width="stretch")
            with st.expander("How we calculate these results and important limitations"):
                st.markdown("- We intersect each corridor's saved study-boundary polygon with the official Texas Census tract polygons.\n- Each tract is weighted by the land area that falls inside the corridor boundary. Missing values are excluded separately for each metric.\n- These are area-weighted averages of tract-level estimates, **not true corridor medians, household-weighted averages, or the exact income/rent of people living along the road**.\n- Land-area weighting can give extra influence to roads, parks or other less-populated land.\n- The 30% rule is a common screening benchmark, not a guarantee of affordability.\n- The rent and income source metrics may come from different data releases. Results should be treated as contextual estimates, not proof that commercial activity causes rent changes.")
            st.caption("The source housing table contains 255 Austin-area Census tracts. A corridor result is calculated only when its boundary overlaps a tract with a matching GEOID and available metric values.")

elif page == "Combined Insights":
    st.markdown("## 🔎 Combined Austin Insights")
    st.write("A simple side-by-side view of area-level housing affordability and commercial activity across the 11 study corridors.")
    housing_path = DATA_DIR / "housing_affordability_tract_summary.csv"
    if housing_path.exists():
        h = pd.read_csv(housing_path)
        share = pd.to_numeric(h.get("Rent-to-income share"), errors="coerce").dropna()
        rent = pd.to_numeric(h.get("Median gross rent (monthly USD)"), errors="coerce").dropna()
        income = pd.to_numeric(h.get("Median renter household income (annual USD)"), errors="coerce").dropna()
        hc1, hc2, hc3 = st.columns(3)
        hc1.metric("Tracts in housing export", f"{len(h):,}")
        hc2.metric("Median rent-to-income share", f"{share.median():.1%}" if len(share) else "—")
        hc3.metric("Tracts at/above 30%", f"{int((share >= .30).sum())}/{len(share)}" if len(share) else "—")
    else:
        st.warning("Housing summary file is missing from the data folder.")
        h = pd.DataFrame()

    corridor_rows = []
    for cname, cdf in all_data.items():
        stt = stats_for(cdf)
        corridor_rows.append({"Corridor": cname, "Mapped business records": stt["records"], "Activity categories": stt["categories"], "Most common mapped activity": stt["top"], "Data status": "Available" if not cdf.empty else "Not collected"})
    corridor_summary = pd.DataFrame(corridor_rows)
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("### Commercial activity across corridors")
        st.bar_chart(corridor_summary.set_index("Corridor")["Mapped business records"].sort_values(ascending=True), horizontal=True)
    with cc2:
        st.markdown("### Housing affordability snapshot")
        if not h.empty and "Rent burden status" in h.columns:
            burden = h["Rent burden status"].value_counts()
            st.bar_chart(burden)
        else:
            st.info("Housing summary is unavailable.")
    st.markdown("### Corridor comparison")
    st.dataframe(corridor_summary, width="stretch", hide_index=True)
    st.download_button("Download combined summary (CSV)", corridor_summary.to_csv(index=False).encode("utf-8"), "austin_combined_corridor_summary.csv", "text/csv")
    st.warning("Important: housing values describe Census tracts, while business counts describe mapped corridor datasets. The supplied files do not include tract polygons for a reliable spatial overlay. These results are shown side by side; they are not a tract-to-corridor match, correlation, or evidence that commercial activity causes rent changes.")

elif page == "Austin Corridor Map":
    st.markdown("## 🗺️ Austin-Wide Map: All 11 Commercial Corridors")
    st.write("A city-wide view of all eleven study corridors, with each corridor shown in its own color. Select a boundary or marker to inspect its corridor details. Use the layer control to turn individual boundaries and road centrelines on or off.")
    try:
        import folium
        import geopandas as gpd
        from streamlit_folium import st_folium

        map_col, legend_col = st.columns([4.6, 1.05], gap="medium")
        with map_col:
            overview_map = folium.Map(
                location=(30.285, -97.755), zoom_start=12, tiles=None,
                control_scale=True, prefer_canvas=True, fade_animation=False,
                zoom_animation=False, marker_zoom_animation=False,
            )
            folium.TileLayer(
                tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
                name="OpenStreetMap", overlay=False, control=True,
                max_zoom=19, update_when_idle=True, keep_buffer=4,
            ).add_to(overview_map)
            all_bounds = []
            legend_rows = []

            for corridor_name, info in CORRIDORS.items():
                lat, lon = info["center"]
                color = info["color"]
                short = info["short"]
                file_key = short.lower().replace(" ", "_").replace("/", "_")
                boundary_path = DATA_DIR / ("boundary_" + file_key + ".geojson")
                roads_path = DATA_DIR / ("roads_" + file_key + ".geojson")

                # Prefer the reviewed SoCo study polygon and road line when present.
                if corridor_name == "South Congress Avenue (SoCo)":
                    if (DATA_DIR / "soco_corridor_area.geojson").exists():
                        boundary_path = DATA_DIR / "soco_corridor_area.geojson"
                    if (DATA_DIR / "soco_corridor_roads.geojson").exists():
                        roads_path = DATA_DIR / "soco_corridor_roads.geojson"

                boundary_gdf = None
                if boundary_path.exists():
                    try:
                        boundary_gdf = gpd.read_file(boundary_path)
                        if boundary_gdf.crs is None:
                            boundary_gdf = boundary_gdf.set_crs("EPSG:4326")
                        boundary_gdf = boundary_gdf.to_crs("EPSG:4326")
                        boundary_gdf = boundary_gdf[boundary_gdf.geometry.notna() & ~boundary_gdf.geometry.is_empty].copy()
                        if boundary_gdf.empty:
                            boundary_gdf = None
                    except Exception:
                        boundary_gdf = None

                # If no saved polygon exists, derive an approximate study polygon from saved road geometry.
                if boundary_gdf is None and roads_path.exists():
                    try:
                        roads_gdf = gpd.read_file(roads_path)
                        if roads_gdf.crs is None:
                            roads_gdf = roads_gdf.set_crs("EPSG:4326")
                        roads_gdf = roads_gdf[roads_gdf.geometry.notna() & ~roads_gdf.geometry.is_empty].copy()
                        if not roads_gdf.empty:
                            projected = roads_gdf.to_crs(roads_gdf.estimate_utm_crs())
                            polygon = projected.geometry.union_all().buffer(int(info["buffer_m"]))
                            boundary_gdf = gpd.GeoDataFrame({"corridor": [corridor_name]}, geometry=[polygon], crs=projected.crs).to_crs("EPSG:4326")
                    except Exception:
                        boundary_gdf = None

                if boundary_gdf is not None:
                    folium.GeoJson(
                        boundary_gdf.to_json(), name=f"{short} study boundary",
                        style_function=lambda feature, c=color: {
                            "color": c, "weight": 3, "fillColor": c,
                            "fillOpacity": 0.32, "opacity": 0.95,
                        },
                        highlight_function=lambda feature, c=color: {
                            "color": c, "weight": 5, "fillOpacity": 0.42,
                        },
                        tooltip=f"{short} — study boundary",
                        popup=folium.Popup(f"<b>{corridor_name}</b><br>Approximate study boundary<br>Buffer: {info['buffer_m']} m", max_width=300),
                    ).add_to(overview_map)
                    minx, miny, maxx, maxy = boundary_gdf.total_bounds
                    all_bounds.extend([[miny, minx], [maxy, maxx]])

                # Draw saved corridor road centreline on top of its polygon.
                if roads_path.exists():
                    try:
                        folium.GeoJson(
                            str(roads_path), name=f"{short} road centreline",
                            style_function=lambda feature, c=color: {"color": c, "weight": 4, "opacity": 1.0},
                            tooltip=f"{short} matched road centreline",
                        ).add_to(overview_map)
                    except Exception:
                        pass

                all_bounds.append([lat, lon])
                popup_html = (
                    f"<div style='min-width:220px'><b>{corridor_name}</b>"
                    f"<br>Reference centre: {lat:.4f}, {lon:.4f}"
                    f"<br>Search radius: {info['search_radius_m']:,} m"
                    f"<br>Study buffer: {info['buffer_m']:,} m"
                    f"<p>{info['description']}</p></div>"
                )
                folium.Marker(
                    location=[lat, lon], tooltip=short,
                    popup=folium.Popup(popup_html, max_width=340),
                    icon=folium.Icon(color="darkgreen", icon="map-marker", prefix="fa"),
                ).add_to(overview_map)
                label_html = (
                    "<div style='font-size:11px;font-weight:800;color:white;background:" + color +
                    ";padding:3px 7px;border:1px solid white;border-radius:6px;white-space:nowrap;"
                    "box-shadow:0 1px 4px #555'>" + short + "</div>"
                )
                folium.Marker(location=[lat, lon], icon=folium.DivIcon(html=label_html, icon_size=(150, 24), icon_anchor=(0, 12))).add_to(overview_map)
                legend_rows.append({"Corridor": corridor_name, "Map label": short, "Reference centre": f"{lat:.4f}, {lon:.4f}", "Boundary displayed": "Yes" if boundary_gdf is not None else "No — boundary/road GeoJSON missing", "Study buffer (m)": info["buffer_m"]})

            if all_bounds:
                overview_map.fit_bounds(all_bounds, padding=(35, 35), max_zoom=13)
            folium.LayerControl(collapsed=True).add_to(overview_map)
            st_folium(overview_map, height=650, width="stretch", key="austin_all_corridors_map_v2")

        with legend_col:
            st.markdown("<div style='background:#ffffff;color:#17352f;border:1px solid #dce7e2;border-radius:12px;padding:14px'>", unsafe_allow_html=True)
            st.markdown("#### Corridor legend")
            for corridor_name, info in CORRIDORS.items():
                st.markdown(
                    f"<div style='display:flex;gap:8px;align-items:flex-start;margin:0 0 13px 0;color:#17352f'>"
                    f"<span style='display:inline-block;min-width:13px;height:13px;margin-top:3px;border-radius:50%;background:{info['color']};border:1px solid #fff;box-shadow:0 0 0 1px {info['color']}'></span>"
                    f"<div><b>{info['short']}</b><br><span style='font-size:11px;color:#52645f'>{corridor_name}</span></div></div>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")
            st.markdown("**Map details**")
            st.caption("📍 Pins show configured reference centres.")
            st.caption("⬟ Colored shapes show saved study boundaries where available.")
            st.caption("━ Colored lines show matched road centre lines where saved.")
            st.caption("Base map: OpenStreetMap.")
            st.info("Boundaries are analytical approximations created from matched roads and configured buffers, not official zoning or legal boundaries.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### All 11 corridor boundary status")
        st.dataframe(pd.DataFrame(legend_rows), width="stretch", hide_index=True)
        st.caption("A corridor boundary is drawn from its saved boundary GeoJSON, or derived from its saved road centreline and configured buffer when possible. If both files are missing, only its reference marker appears; the dashboard does not invent a boundary.")
    except ImportError:
        st.warning("The interactive map needs folium, geopandas, and streamlit-folium. Install them with: pip install folium geopandas streamlit-folium")
    except Exception as exc:
        st.error(f"Could not render the Austin corridor map: {exc}")
