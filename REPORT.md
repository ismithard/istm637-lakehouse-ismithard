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

Verified row counts: **dim_well = 50**, **dim_date = 547**, **fact_production = 22,806**
(expected ~50 / ~547 / ~22,800). The two Lakeflow `EXPECT` constraints on
`fact_production` (`valid_oil`, `valid_dates`) passed on load.

Evidence: `screenshots/02_pipeline_run_graph.png`, `03_catalog_tables.png`, `04_rowcount_verification.png`.

## Part 3 — AI-assisted metadata

Generated column comments with the Catalog Explorer AI assistant on all three tables,
then reviewed and corrected them before accepting. Tags applied: `domain`, `layer`
(and `pii='none'`).

**Corrections I made to the AI suggestions:**

The AI's drafts were fluent but consistently missing the domain units, so I rewrote
them column by column. It described the volume columns generically — `oil_bbl` and
`water_bbl` became "barrels **per day**" (they are daily rates, not cumulative
volumes) and `gas_mcf` became "**thousand cubic feet (mcf) per day**" rather than
just "gas volume". It called `choke_size_64ths` a generic "choke size", which I
corrected to the surface choke opening measured in **64ths of an inch** (so 40 means
40/64"), and it treated `date_id` as an identifier when it is really an integer
**yyyymmdd** date key; I also specified that `tubing_pressure_psi` and
`casing_pressure_psi` are *flowing* pressures in psi, that `lateral_length_ft` is the
horizontal lateral in feet (0 for vertical wells), and that
`initial_oil_potential_bopd` is an estimated initial rate in barrels of oil per day.

Finally I added the two derived metrics an analyst would actually ask for to the
`fact_production` table description — **GOR = gas_mcf / oil_bbl** and
**water cut = water_bbl / (oil_bbl + water_bbl)** — so that Genie can resolve those
terms in Part 4 without being told again in the space instructions.

Evidence: `screenshots/05_comments_fact.png`, `06_tags_tables.png`.

## Part 4 — Genie Space

Space instructions describe the domain (oil & gas daily production), the grain
(one row per well per day), and key terms (production = oil_bbl, GOR, water cut).
Three trusted queries added: total oil/gas/wells by basin, quarterly oil trend, and
top 5 wells by total gas.

### Test questions

| # | Question | Correct? | Answer Genie gave | Fix made |
|---|---|---|---|---|
| 1 | Which basin produced the most oil overall? | Yes | Permian Basin, ~2.2 M bbl from 14 wells (Eagle Ford second at 2.1 M) | None — resolved against the "Total oil production by basin" trusted query |
| 2 | Show monthly oil production trend for 2024. | Yes | Peak of 731 K bbl in May, declining to 429 K by December | None — used `dim_date.year = 2024` and ordered by `month`, exactly the join the instructions describe |
| 3 | What is the average water cut for wells in the Permian Basin? | Yes | 51.79% across 5,431 records and 14 wells | None — Genie applied the `water_bbl / (oil_bbl + water_bbl)` definition from the space instructions and added an `(oil_bbl + water_bbl) > 0` guard on its own |
| 4 | Which operator has the most producing wells? | Yes | Coterra and Marathon Oil tied at 7 each | None — correctly filtered `status = 'Producing'`, which is defined in the instructions |
| 5 | List the top 5 wells by total gas production. | Yes | Weld 35-34 (1.13 M mcf), Lea 20-2, Martin 28-2H, La Salle 5-11H, Eddy 25-15H | None — matched the trusted query and helpfully added operator and basin columns |

All five questions were answered correctly on the first attempt, which I attribute to the
Part 3 metadata work rather than luck: the corrected column comments gave Genie the units,
and the space instructions supplied the two derived terms and the meaning of "producing".
Question 3 is the clearest evidence — "water cut" appears nowhere in the schema, yet Genie
generated the correct formula and even guarded against divide-by-zero.

One nuance worth recording: for question 3 Genie computed the *average of the daily
per-record ratios* rather than the pooled ratio `SUM(water_bbl) / SUM(oil_bbl + water_bbl)`.
Both are defensible readings of "average water cut", but they are not the same number —
the pooled version weights high-volume days more heavily. Since the question said
"average", I accepted the row-level average; if this space were going to production I would
pin the intended definition in the instructions so the two never diverge.

Evidence: `screenshots/07_genie_answer_sql.png` (question 3, generated SQL visible), plus
`07b_genie_q1_basin.png`, `07c_genie_q2_monthly.png`, `07d_genie_q4_operator.png`, and
`07e_genie_q5_topgas.png` for the remaining four.

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

Six widgets in total: the monthly oil line chart, total oil by basin, producing wells by
operator (filtered to `status = 'Producing'`), and three KPI counters for total oil, gas,
and water. A **global filter on `basin`** sits in the page's filter rail and drives every
widget at once — the screenshots were captured with `Permian Basin` selected, which is why
the counters read 2.2 M bbl oil / 6.27 M mcf gas / 2.4 M bbl water and the basin bar chart
collapses to a single column. Those figures reconcile with the Genie answer in Part 4,
where the Permian Basin was identified as the top producer at approximately 2.2 M barrels.

Evidence: `screenshots/08_dashboard_published.png` (upper half + filter rail) and
`08b_dashboard_counters.png` (lower half).

## Part 6 — Prediction model

Ran `ISTM637_Predictive_Model_Notebook.ipynb`: feature table joins the fact to both
dimensions and engineers `days_online`; a gradient-boosted regressor (one-hot encoded
basin, target_formation, well_type + numeric features) predicts daily `oil_bbl`.

| Metric | Value |
|---|---|
| MAE | 33.5 bbl/day |
| RMSE | 70.0 bbl/day |
| R² | **0.933** (target > 0.8) |

The model explains 93.3% of the variance in daily oil rate on the held-out test set.
The gap between MAE (33.5) and RMSE (70.0) is worth noting: RMSE penalises large errors
quadratically, so a value roughly twice the MAE says the residuals are not uniform — most
days are predicted within ~34 bbl, but a minority of days (most plausibly early flowback,
when rates move fastest, and shut-in or workover days) carry much larger errors. For a
screening tool at this grain that is acceptable, and it is the expected signature of a
decline-driven process.

Registration to Unity Catalog succeeded on the first attempt, so the notebook's
Volume-fallback path (for workspaces that block model-artifact uploads) was not needed:

```
Successfully registered model 'istm637_ismithard.oilgas.oil_rate_predictor'.
Created version '1' of model 'istm637_ismithard.oilgas.oil_rate_predictor'
Registered: istm637_ismithard.oilgas.oil_rate_predictor version 1
Alias @champion -> istm637_ismithard.oilgas.oil_rate_predictor
```

`forecast_well()` produced a 180-day forecast for the sample well `WELL-0001` totalling
**51,855 bbl**, and the batch step wrote the `well_forecast` table with **6,660 rows
(37 producing wells × 180 days)** — this is the table the Part 7 app reads, which is why
the app needs no model loading of its own.

Evidence: `screenshots/09_model_metrics.png`, `10_uc_model_champion.png`,
`11_forecast_180d.png`, `11b_well_forecast_table.png`.

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

**Implementation.** The app is a single-page Streamlit app (source committed under
`app/` in this repo: `app.py`, `app.yaml`, `requirements.txt`). It connects to the
serverless SQL warehouse with the `databricks-sql-connector`, authenticating as the app's
own service principal via the SDK's `Config()` — no personal token is embedded anywhere.
The warehouse is wired in as a declared **app resource** keyed `sql-warehouse`, and the
three queries are parameterised on `well_id` rather than string-formatted, so the well
selector cannot inject SQL.

Two things were needed to make Unity Catalog authorise the app, and both are worth
recording because neither is obvious from the app scaffold:

1. The app's service principal starts with **no** privileges. It needed
   `USE CATALOG`, `USE SCHEMA`, and `SELECT` granted on `istm637_ismithard.oilgas`
   before any query would return rows.
2. A SQL warehouse resource had to be attached to the app; without it the connector has
   no HTTP path and the page hangs on the first query rather than failing loudly. I
   handled that in code by resolving the path from either the HTTP-path or warehouse-ID
   environment variable and surfacing connection failures to the page.

**Verification.** Selecting `Adams 21-32` (EOG Resources, DJ Basin) renders 318 days of
daily oil history — the decline curve and its downtime dips are both visible — alongside
the 180-day forecast declining from roughly 260 to 195 bbl/day, totalling **38,367 bbl**.
The forecast series starts near where the history ends, which is the sanity check that
matters: the batch predictions are continuous with the observed rate rather than offset.

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
