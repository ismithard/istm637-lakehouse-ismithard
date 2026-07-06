# ISTM 637 — Project Report

**Name:** Ieuan Smithard · **NetID:** ismithard · **Catalog:** `istm637_ismithard` · **Schema:** `oilgas`

---

## Part 1 — GitHub integration

Linked my GitHub account to Databricks via the Databricks GitHub App, created a Git
folder cloning `istm637-lakehouse-ismithard`, and demonstrated the check-out / check-in
cycle with commits pushed from the Databricks Git dialog.

Evidence: `screenshots/01_git_dialog_push.png` and the commit history on `main`.

## Part 2 — Lakeflow ingest into Unity Catalog

Created catalog `istm637_ismithard`, schema `oilgas`, and volume `raw` from the starter
notebook; uploaded the three CSVs; ran the Lakeflow Declarative Pipeline attached to
`ISTM637_Lakeflow_Ingest_Pipeline.sql` with `source_path = /Volumes/istm637_ismithard/oilgas/raw`.

Verified row counts: **dim_well = <N>**, **dim_date = <N>**, **fact_production = <N>**
(expected ~50 / ~547 / ~22,800).

Evidence: `screenshots/02_pipeline_run_graph.png`, `03_catalog_tables.png`, `04_rowcount_verification.png`.

## Part 3 — AI-assisted metadata

Generated column comments with the Catalog Explorer AI assistant on all three tables,
then reviewed and corrected them before accepting. Tags applied: `domain`, `layer`
(and `pii='none'`).

**Corrections I made to the AI suggestions (2–3 sentences — TODO, examples of what to look for):**
<!-- e.g., The AI described choke_size_64ths as a generic "size" — corrected to
"surface choke setting in 64ths of an inch". It called gas_mcf "gas volume" without
units — fixed to "thousand cubic feet (mcf) per day". It missed that water cut is
water_bbl / (oil_bbl + water_bbl) when describing water_bbl. -->

Evidence: `screenshots/05_comments_fact.png`, `06_tags_tables.png`.

## Part 4 — Genie Space

Space instructions describe the domain (oil & gas daily production), the grain
(one row per well per day), and key terms (production = oil_bbl, GOR, water cut).
Three trusted queries added: total oil/gas/wells by basin, quarterly oil trend, and
top 5 wells by total gas.

### Test questions

| # | Question | Correct? | Fix made |
|---|---|---|---|
| 1 | Which basin produced the most oil overall? | TODO | TODO |
| 2 | Show monthly oil production trend for 2024. | TODO | TODO |
| 3 | What is the average water cut for wells in the Permian Basin? | TODO | TODO |
| 4 | Which operator has the most producing wells? | TODO | TODO |
| 5 | List the top 5 wells by total gas production. | TODO | TODO |

Evidence: `screenshots/07_genie_answer_sql.png`.

## Part 5 — AI/BI Dashboard

Published dashboard with four visualizations on the star schema — monthly oil trend
(line), total oil by basin (bar), producing well count by operator (bar), and KPI
counters (total oil / gas / water, average water cut) — with a basin filter applied
across the page.

Dataset query (fact joined to both dimensions):

```sql
SELECT f.oil_bbl, f.gas_mcf, f.water_bbl, f.downtime_hours,
       d.calendar_date, d.year, d.quarter_name, d.month, d.month_name,
       w.well_id, w.well_name, w.operator, w.basin, w.state,
       w.target_formation, w.well_type, w.status
FROM fact_production f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_well w ON f.well_id = w.well_id
```

Evidence: `screenshots/08_dashboard_published.png`.

## Part 6 — Prediction model

Ran `ISTM637_Predictive_Model_Notebook.ipynb`: feature table joins the fact to both
dimensions and engineers `days_online`; a gradient-boosted regressor (one-hot encoded
basin, target_formation, well_type + numeric features) predicts daily `oil_bbl`.

| Metric | Value |
|---|---|
| MAE | TODO |
| RMSE | TODO |
| R² | TODO (target > 0.8) |

Registered in Unity Catalog as `istm637_ismithard.oilgas.oil_rate_predictor` with the
`@champion` alias; `forecast_well()` output saved to the `well_forecast` table.

Evidence: `screenshots/09_model_metrics.png`, `10_uc_model_champion.png`, `11_forecast_180d.png`.

## Part 7 — Data app

**Where the app's data comes from:** The app runs entirely on governed Unity Catalog
tables — no hard-coded data. The well selector is populated from `dim_well`. For the
selected well, the history chart queries `fact_production` joined to `dim_date` on
`date_id` to plot daily oil (bbl) over calendar dates. The forecast chart reads the
pre-computed `well_forecast` table, which the Part 6 notebook produced by calling the
registered `oil_rate_predictor` model (`@champion`) — so the app stays light on
compute while still serving the governed model's predictions. The app's service
identity was granted SELECT on the `oilgas` schema so its queries are authorized by
Unity Catalog.

Evidence: `screenshots/12_app_deployed.png`, `13_app_history_forecast.png`.

## Part 8 — OpenSharing

<!-- Keep ONE of the two sections below and delete the other. -->

### Option A — Full Databricks-to-Databricks exchange

Partnered with **<PARTNER NAME / NETID>**. As provider I created a share containing
`dim_well`, added my partner as a recipient using their sharing identifier, and
granted the share. As recipient I mounted my partner's share to a catalog and queried
their `dim_well` from a notebook. Both directions verified.

Evidence: `screenshots/14_shared_table_query.png`.

### Option B — Fallback (recipient creation restricted on Free Edition)

Recipient creation was blocked on my Free Edition account, so per the assignment I
completed the provider workflow and document here how a non-Databricks recipient
would consume the share via the open sharing protocol.

I created the share object and added `dim_well` to it
(`screenshots/14_share_object.png`). To serve a recipient outside Databricks, the
provider creates a recipient **without** a Databricks sharing identifier. Unity
Catalog then issues an **activation link**, from which the recipient downloads a
credential file (`config.share`) — a JSON profile containing the sharing server
endpoint and a bearer token that authenticates every request. The token is the
secret: it is downloadable once and should be transferred out-of-band.

The recipient consumes the share with any open-source Delta Sharing client — no
Databricks account required. In Python:

```python
# pip install delta-sharing
import delta_sharing

profile = "config.share"                      # credential file from the activation link
client = delta_sharing.SharingClient(profile)
client.list_all_tables()                      # discover what the provider granted

# Load the shared table: <profile>#<share>.<schema>.<table>
df = delta_sharing.load_as_pandas(f"{profile}#istm637_share.oilgas.dim_well")
print(df.head())
```

Or with Spark SQL after `CREATE CATALOG shared_oilgas USING SHARE ...` on a platform
that supports it, the recipient simply runs:

```sql
SELECT basin, COUNT(*) AS wells FROM shared_oilgas.oilgas.dim_well GROUP BY basin;
```

Because the share is governed by Unity Catalog, the provider can revoke the
recipient or remove the table at any time, and every read is audited — the same
governance that applies to my own workspace queries.
