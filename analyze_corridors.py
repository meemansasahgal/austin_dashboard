
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

FILE = DATA_DIR / "business_clusters.csv"

if not FILE.exists():
    raise FileNotFoundError(
        "business_clusters.csv not found. Run cluster_corridors.py first."
    )

df = pd.read_csv(FILE)

# Count businesses in each cluster
clustered = df[df["cluster"] != -1].copy()

if clustered.empty:
    print("No clusters found. DBSCAN parameters may need adjustment.")
    raise SystemExit

summary = (
    clustered.groupby("cluster")
    .agg(
        business_count=("cluster", "size"),
        average_latitude=("latitude", "mean"),
        average_longitude=("longitude", "mean"),
        different_categories=("category", "nunique")
    )
    .reset_index()
)

# Find the most common business category in each cluster
top_categories = (
    clustered.groupby("cluster")["category"]
    .agg(lambda x: x.value_counts().index[0])
    .rename("most_common_category")
    .reset_index()
)

summary = summary.merge(top_categories, on="cluster")

# Sort biggest clusters first
summary = summary.sort_values(
    "business_count", ascending=False
)

summary.to_csv(
    DATA_DIR / "corridor_analysis.csv",
    index=False
)

print("\n===== SOCO BUSINESS CLUSTER ANALYSIS =====")
print(summary.to_string(index=False))

print("\nTotal businesses:", len(df))
print("Businesses in clusters:", len(clustered))
print("Number of clusters:", len(summary))
print("Unclustered businesses:", (df["cluster"] == -1).sum())

print("\nSaved report to:", DATA_DIR / "corridor_analysis.csv")

