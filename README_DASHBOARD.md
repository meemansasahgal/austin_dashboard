# Austin Corridor Intelligence dashboard

This dashboard expands the existing SoCo project into a six-corridor exploration interface.

## Run on Windows (CMD)

1. Extract the project ZIP.
2. Open Command Prompt in the `SoCo-Corridor` folder.
3. Create and activate a virtual environment (recommended):

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open the dashboard in your browser.

## Included corridors

- South Congress Avenue (SoCo) — uses the existing `data/soco_corridor_businesses.csv` baseline.
- South Lamar Boulevard
- East Riverside Drive
- Burnet Road
- North Lamar Boulevard
- Guadalupe Street (The Drag)

The five new corridors are not pre-populated with fabricated counts. Open **Overview**, select a missing corridor, and click **Fetch corridor data from OpenStreetMap**. An internet connection is required. The OSM query may take a few minutes and can fail if road names differ from OpenStreetMap's naming; the error will be shown in the UI.

## Important notes

- Corridor buffers default to 100 m on each side of the selected road geometry.
- DBSCAN defaults to `eps=100 m` and `min_samples=5`.
- Road reference points and road-name variants are initial settings and may need adjusting after testing each corridor.
- OSM is community-maintained; check duplicate and unnamed records before presenting results.
- For a defensible final comparison, reprocess all six corridors with the same settings and similar collection dates.
