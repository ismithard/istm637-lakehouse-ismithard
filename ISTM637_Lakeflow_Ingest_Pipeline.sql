-- =============================================================================
-- ISTM 637 — Lakeflow Declarative Pipeline
-- Ingest the oil & gas star schema (3 CSVs) into Unity Catalog
-- MS Analytics · Texas A&M University · Mays Business School
-- =============================================================================
--
-- HOW TO USE THIS FILE
--   1) Create your catalog/schema/volume and upload the 3 CSVs to the volume,
--      e.g.  /Volumes/istm637_<netid>/oilgas/raw/   (the starter notebook does this).
--   2) In the sidebar: Jobs & Pipelines -> Create -> ETL pipeline (Lakeflow
--      Declarative Pipeline). Choose SQL and attach this file as the source.
--   3) In pipeline Settings, set:
--        Default catalog:  istm637_<netid>
--        Default schema:   oilgas
--        Configuration ->  key: source_path
--                          value: /Volumes/istm637_<netid>/oilgas/raw
--   4) Click Run. The pipeline reads the CSVs with read_files() and creates
--      dim_well, dim_date, and fact_production as Unity Catalog tables.
--
-- NO-CODE ALTERNATIVE: build the same three flows visually in Lakeflow Designer;
-- every Designer flow compiles to a Spark Declarative Pipeline like this one.
--
-- COLUMN COMMENTS: you do NOT write column comments here. In Part 3 you use the
-- AI assistant in Catalog Explorer to generate and accept column comments for
-- each table. Lakeflow EXPECT constraints below validate data quality on load.
-- Free Edition allows one active pipeline per type -- one pipeline is all you need.
-- =============================================================================


-- ---------- Dimension: dim_well -------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW dim_well
  COMMENT 'Well master data: one row per well, with location and completion attributes. Ingested from raw CSV via Lakeflow.'
  TBLPROPERTIES ('quality' = 'silver', 'source' = 'lakeflow_read_files')
AS SELECT * FROM read_files(
  '${source_path}/dim_well.csv',
  format            => 'csv',
  header            => true,
  inferColumnTypes  => true
);


-- ---------- Dimension: dim_date -------------------------------------------------
CREATE OR REFRESH MATERIALIZED VIEW dim_date
  COMMENT 'Calendar date dimension (one row per day). Ingested from raw CSV via Lakeflow.'
  TBLPROPERTIES ('quality' = 'silver', 'source' = 'lakeflow_read_files')
AS SELECT * FROM read_files(
  '${source_path}/dim_date.csv',
  format            => 'csv',
  header            => true,
  inferColumnTypes  => true
);


-- ---------- Fact: fact_production ------------------------------------------------
-- Lakeflow data-quality EXPECTATIONS validate the data as it loads.
CREATE OR REFRESH MATERIALIZED VIEW fact_production (
  CONSTRAINT valid_oil    EXPECT (oil_bbl >= 0),
  CONSTRAINT valid_dates  EXPECT (date_id >= 20240101)
)
  COMMENT 'Daily production fact table: one row per well per producing day. Grain = well_id + date_id. Ingested from raw CSV via Lakeflow.'
  TBLPROPERTIES ('quality' = 'silver', 'source' = 'lakeflow_read_files')
AS SELECT * FROM read_files(
  '${source_path}/fact_production.csv',
  format            => 'csv',
  header            => true,
  inferColumnTypes  => true
);
