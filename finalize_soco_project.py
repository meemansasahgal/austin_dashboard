
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"

business_file = DATA / "soco_corridor_businesses.csv"
summary_file = DATA / "soco_corridor_summary.csv"
map_file = DATA / "soco_corridor_map.png"

for file in [business_file, summary_file]:
    if not file.exists():
        raise FileNotFoundError(
            f"Missing required file: {file}\n"
            "Run build_soco_corridor.py first."
        )

businesses = pd.read_csv(business_file)
summary = pd.read_csv(summary_file).iloc[0]

# -------------------------------
# 1. BUSINESS DATA QUALITY
# -------------------------------

if "name" in businesses.columns:
    names = businesses["name"].astype("string").str.strip()
    valid_names = names[names.notna() & names.ne("")]
    missing_names = int((names.isna() | names.eq("")).sum())
    unique_names = int(valid_names.nunique())
    duplicate_mask = valid_names.duplicated(keep=False)
    duplicate_records = int(duplicate_mask.sum())
    duplicate_name_list = sorted(
        valid_names[duplicate_mask].unique().tolist()
    )
else:
    missing_names = len(businesses)
    unique_names = 0
    duplicate_records = 0
    duplicate_name_list = []

if "category" in businesses.columns:
    categories = (
        businesses["category"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )
else:
    categories = pd.Series(
        ["Unknown"] * len(businesses),
        index=businesses.index
    )

category_counts = categories.value_counts().rename_axis(
    "category"
).reset_index(name="business_records")

category_counts.to_csv(
    DATA / "soco_category_counts.csv",
    index=False
)

quality = pd.DataFrame([{
    "business_records": len(businesses),
    "unique_named_businesses": unique_names,
    "missing_or_blank_names": missing_names,
    "records_with_repeated_names": duplicate_records,
    "distinct_categories": int(categories.nunique()),
}])

quality.to_csv(
    DATA / "soco_data_quality_summary.csv",
    index=False
)

# -------------------------------
# 2. CATEGORY CHART
# -------------------------------

chart_data = category_counts.sort_values(
    "business_records", ascending=True
)

fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(
    chart_data["category"],
    chart_data["business_records"]
)
ax.set_title("SoCo Corridor: Business Category Distribution")
ax.set_xlabel("Number of business records")
ax.set_ylabel("Business category")
ax.grid(axis="x", alpha=0.25)

plt.tight_layout()
chart_file = DATA / "soco_business_category_chart.png"
plt.savefig(chart_file, dpi=200, bbox_inches="tight")
plt.close(fig)

# -------------------------------
# 3. PREPARE REPORT VALUES
# -------------------------------

corridor_name = summary["corridor_name"]
road_records = int(summary["road_records"])
components = int(summary["connected_road_components"])
length_km = float(summary["corridor_length_km"])
buffer_m = int(summary["buffer_each_side_m"])
area_km2 = float(summary["corridor_area_sq_km"])
inside = int(summary["businesses_inside"])
outside = int(summary["businesses_outside"])
category_total = int(summary["unique_business_categories"])
density = float(summary["businesses_per_km"])

top_categories = category_counts.sort_values(
    "business_records", ascending=False
).head(10)

category_table = top_categories.to_markdown(index=False)

if map_file.exists():
    map_section = (
        "![SoCo Corridor Map](soco_corridor_map.png)"
    )
else:
    map_section = (
        "The corridor map has not been generated yet."
    )

duplicate_text = (
    "\n".join(f"- {name}" for name in duplicate_name_list)
    if duplicate_name_list
    else "- No repeated nonblank business names were detected."
)

# -------------------------------
# 4. CREATE FINAL REPORT
# -------------------------------

report = f"""# SoCo Corridor Analysis — Final Report

## 1. Project objective

This project uses road-network and business-location data to
analyse the commercial character of the South Congress Avenue
(SoCo) area in Austin, Texas.

The workflow identifies business clusters, matches businesses
to nearby roads, constructs a preliminary road-based corridor,
and summarises the businesses within the selected area.

## 2. Methodology

1. Load the available road-network and business-location data.
2. Cluster business locations and rank candidate commercial areas.
3. Match businesses to nearby road segments.
4. Select road records named South Congress Avenue.
5. Merge the selected road geometries where possible.
6. Buffer the selected road geometry by {buffer_m} metres on
   each side.
7. Count business records whose points fall inside that buffer.
8. Calculate category diversity and business records per kilometre.

## 3. Corridor results

| Metric | Result |
|---|---:|
| Selected road records | {road_records} |
| Connected road components | {components} |
| Merged centerline length | {length_km:.3f} km |
| Buffer on each side | {buffer_m} m |
| Buffered area | {area_km2:.4f} sq km |
| Business records inside | {inside} |
| Business records outside | {outside} |
| Categories inside corridor | {category_total} |
| Business records per km | {density:.2f} |

The density metric is calculated as the number of business records
inside the buffer divided by the merged centerline length.

## 4. Business category distribution

The most common categories in the selected corridor are:

{category_table}

![Business Category Chart](soco_business_category_chart.png)

## 5. Data quality checks

| Check | Result |
|---|---:|
| Business records inside corridor | {len(businesses)} |
| Unique named businesses | {unique_names} |
| Missing or blank business names | {missing_names} |
| Records sharing a repeated name | {duplicate_records} |
| Distinct category labels, including Unknown | {categories.nunique()} |

Repeated names are flagged for review, not automatically removed.
Two legitimate businesses may have the same name. Likewise,
unnamed records may still represent real businesses.

### Repeated names to review

{duplicate_text}

## 6. Corridor map

{map_section}

## 7. Interpretation

The current dataset shows a substantial food-and-dining presence,
alongside retail and service businesses. Category counts describe
the records available in this dataset; they should not be treated
as a complete census of every business in the SoCo district.

The buffered road geometry provides a reproducible first definition
of the corridor for analysis.

## 8. Limitations

- The corridor uses a chosen {buffer_m}-metre buffer, not an official
  district boundary.
- The merged geometry contains {components} disconnected components.
  These sections should be checked before claiming the corridor is
  one continuous road.
- The merged line length may differ from the sum of original road
  segment lengths because segments may overlap or be disconnected.
- Business names, categories, missing values, and duplicates may
  require further verification.
- Business records inside the buffer depend on the completeness and
  accuracy of the source data.
- The category-based analysis describes the available records and
  does not establish customer demand or business performance.

## 9. Output files

- `soco_corridor_map.png` — corridor and business map
- `soco_corridor_area.geojson` — buffered corridor polygon
- `soco_corridor_centerline.geojson` — merged road geometry
- `soco_corridor_businesses.csv` — selected business records
- `soco_corridor_summary.csv` — corridor metrics
- `soco_category_counts.csv` — category counts
- `soco_business_category_chart.png` — category distribution chart
- `soco_data_quality_summary.csv` — data quality summary

## 10. Conclusion

The project has progressed from business clustering to a
preliminary road-based commercial corridor with mapped business
locations, category statistics, and reproducible output files.

The current results are suitable for an initial corridor analysis.
Road continuity and business data quality remain important checks
before treating the measurements as final verified facts.
"""

report_file = DATA / "SoCo_Final_Project_Report_FINAL.md"
report_file.write_text(report, encoding="utf-8")

print("\n=== SOCO PROJECT FINALIZATION ===")
print(f"Business records: {len(businesses)}")
print(f"Unique named businesses: {unique_names}")
print(f"Missing or blank names: {missing_names}")
print(f"Repeated-name records to review: {duplicate_records}")
print(f"Categories: {categories.nunique()}")
print(f"\nCategory chart: {chart_file}")
print(f"Category counts: {DATA / 'soco_category_counts.csv'}")
print(f"Data quality: {DATA / 'soco_data_quality_summary.csv'}")
print(f"Final report: {report_file}")
print("\nFinalization completed successfully.")
