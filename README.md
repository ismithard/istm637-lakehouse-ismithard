# ISTM 637 — Building a Governed Lakehouse

**Name:** <YOUR NAME>
**NetID:** <NETID>
**Catalog:** `istm637_<NETID>`

An end-to-end governed data + AI product on Databricks Free Edition: three oil & gas
production CSVs ingested to a Unity Catalog star schema with Lakeflow, documented with
AI-assisted metadata, explored through a Genie Space and an AI/BI Dashboard, forecast
with an MLflow-registered regression model, and served in a Databricks App — with one
table shared to a classmate via OpenSharing.

## Repository contents

| Path | What it is |
|---|---|
| `ISTM637_Databricks_Project_Starter.ipynb` | Setup + verification notebook (catalog, schema, volume, tags, validation queries) |
| `ISTM637_Predictive_Model_Notebook.ipynb` | Trains, evaluates, and registers `oil_rate_predictor`; writes `well_forecast` |
| `ISTM637_Lakeflow_Ingest_Pipeline.sql` | Lakeflow Declarative Pipeline source — ingests the 3 CSVs into Unity Catalog |
| `REPORT.md` | Written report covering Parts 1–8 |
| `screenshots/` | Evidence for each part (see `screenshots/README.md` for the shot list) |

Data files (`dim_well.csv`, `dim_date.csv`, `fact_production.csv`) are intentionally
not committed; they live in the Unity Catalog Volume
`/Volumes/istm637_<NETID>/oilgas/raw`.
