from pathlib import Path
import pandas as pd
data = Path("data")
summary_file = data / "soco_corridor_summary.csv"
business_file = data / "soco_corridor_businesses.csv"
if not summary_file.exists() or not business_file.exists():
    raise FileNotFoundError("Required SoCo output CSV files are missing.")
s = pd.read_csv(summary_file).iloc[0]
b = pd.read_csv(business_file)
counts = pd.read_csv(data / "soco_category_counts.csv")
def val(key, default="N/A"):
    return s[key] if key in s.index else default
names = b["name"].astype("string").str.strip() if "name" in b.columns else pd.Series(dtype="string")
missing_names = int((names.isna() | names.eq("")).sum()) if len(names) else len(b)
unique_names = int(names[names.notna() & names.ne("")].nunique()) if len(names) else 0
report = f"""# SoCo Corridor Analysis — Final Report
## 1. Project Objective
This project analyses the commercial corridor around South Congress Avenue (SoCo) in Austin, Texas, using road-network and business-location data.
## 2. Methodology
1. Load road-network and business-location datasets.
2. Analyse business clusters and nearby roads.
3. Select road segments named South Congress Avenue.
4. Buffer the selected road geometry by 100 metres on each side.
5. Count business records inside the corridor and summarise their categories.
6. Generate a corridor map and category distribution chart.
## 3. Corridor Results
| Metric | Result |
|---|---:|
| Selected road records | {val('road_records')} |
| Connected road components | {val('connected_road_components')} |
| Centerline length (km) | {float(val('corridor_length_km', 0)):.3f} |
| Buffer on each side (m) | {val('buffer_each_side_m')} |
| Buffered area (sq km) | {float(val('corridor_area_sq_km', 0)):.4f} |
| Businesses inside | {val('businesses_inside')} |
| Businesses outside | {val('businesses_outside')} |
| Unique category count from corridor summary | {val('unique_business_categories')} |
| Business records per km | {float(val('businesses_per_km', 0)):.2f} |
## 4. Business Category Distribution
{counts.to_markdown(index=False)}
![SoCo business category chart](soco_business_category_chart.png)
## 5. Data Quality
- Business records in corridor file: {len(b)}
- Unique named businesses: {unique_names}
- Records with missing or blank names: {missing_names}
Repeated names and unnamed records should be checked before treating the dataset as a complete business census.
## 6. Corridor Map
![SoCo Corridor Map](soco_corridor_map.png)
## 7. Interpretation
The available records show a mix of dining, retail, and service businesses. Category counts describe the collected dataset and may not include every business in the real-world district.
## 8. Limitations
- The 100-metre buffer is an analytical choice, not an official district boundary.
- The road geometry contains {val('connected_road_components')} connected components, so continuity should be verified.
- Business names, categories, and locations may be missing or inaccurate.
- Business counts depend on the completeness of the collected data.
- Business density alone does not measure customer demand or business performance.
## 9. Key Output Files
- `soco_corridor_map.png` — corridor map
- `soco_corridor_area.geojson` — buffered corridor
- `soco_corridor_centerline.geojson` — selected road geometry
- `soco_corridor_businesses.csv` — business records inside the corridor
- `soco_corridor_summary.csv` — corridor metrics
- `soco_category_counts.csv` — business category counts
- `soco_business_category_chart.png` — category chart
- `soco_data_quality_summary.csv` — data-quality metrics
## 10. Conclusion
The project produces a preliminary road-based commercial corridor, maps business locations, and summarises business categories. The results are suitable for an initial spatial analysis, with road continuity and data quality remaining important limitations.
"""
output = data / "SoCo_Final_Project_Report_FINAL.md"
output.write_text(report, encoding="utf-8")
print(f"Report created: {output.resolve()}")
