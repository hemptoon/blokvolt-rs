# region-data

Open charging data for Serbia and its neighbours, fetched by `scripts/region_fetch.py` in `.github/workflows/region-data.yml` on the `main` branch (monthly and by hand). This branch is replaced on every run — do not edit it.

- `<CC>/osm.json` — © OpenStreetMap contributors, Open Database License 1.0 (https://www.openstreetmap.org/copyright).
- `<CC>/ocm.json`, `referencedata.json` — Open Charge Map (https://openchargemap.org), from the public export https://github.com/openchargemap/ocm-export; licence per data provider, CC BY 4.0 for OCM contributors.
- `meta.json` — fetch times, servers and counts.
