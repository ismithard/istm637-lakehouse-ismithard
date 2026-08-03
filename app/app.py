"""
ISTM 637 — Part 7: Well Production & Forecast
Databricks App (Streamlit) reading governed Unity Catalog tables.

The app deliberately loads NO ML model. Part 6 already ran the registered
oil_rate_predictor (@champion) in batch and materialised its output to the
well_forecast table, so this app just reads two small tables through the SQL
warehouse. That keeps it inside Free Edition's app resource limits.
"""

import os

import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

CATALOG = "istm637_ismithard"
SCHEMA = "oilgas"

st.set_page_config(page_title="Well Production & Forecast", layout="wide")


def warehouse_http_path():
    """
    Resolve the warehouse HTTP path from whichever env var the app resource set.
    A SQL warehouse resource may expose either the full HTTP path or just the
    warehouse ID, so accept both rather than assuming one.
    """
    for var in ("DATABRICKS_WAREHOUSE_HTTP_PATH", "DATABRICKS_HTTP_PATH"):
        value = os.environ.get(var)
        if value and value.startswith("/sql/"):
            return value
    for var in ("DATABRICKS_WAREHOUSE_ID", "DATABRICKS_WAREHOUSE_HTTP_PATH"):
        value = os.environ.get(var)
        if value:
            return f"/sql/1.0/warehouses/{value.strip('/').split('/')[-1]}"
    raise RuntimeError(
        "No warehouse env var found. Add a SQL warehouse resource to the app "
        "with key 'sql-warehouse'. Present vars: "
        + ", ".join(sorted(k for k in os.environ if "DATABRICKS" in k))
    )


@st.cache_resource
def connection():
    """Connect to the SQL warehouse using the app's own service principal."""
    cfg = Config()  # picks up DATABRICKS_HOST + the app's OAuth credentials
    return sql.connect(
        server_hostname=cfg.host.replace("https://", "").rstrip("/"),
        http_path=warehouse_http_path(),
        credentials_provider=lambda: cfg.authenticate,
    )


def query(statement, params=None):
    with connection().cursor() as cur:
        cur.execute(statement, params or {})
        return pd.DataFrame(
            cur.fetchall(), columns=[c[0] for c in cur.description]
        )


@st.cache_data(ttl=600)
def load_wells():
    return query(
        f"""
        SELECT well_id, well_name, operator, basin
        FROM {CATALOG}.{SCHEMA}.dim_well
        ORDER BY well_name
        """
    )


@st.cache_data(ttl=600)
def load_history(well_id):
    return query(
        f"""
        SELECT d.calendar_date, f.oil_bbl
        FROM {CATALOG}.{SCHEMA}.fact_production f
        JOIN {CATALOG}.{SCHEMA}.dim_date d ON f.date_id = d.date_id
        WHERE f.well_id = :well
        ORDER BY d.calendar_date
        """,
        {"well": well_id},
    )


@st.cache_data(ttl=600)
def load_forecast(well_id):
    return query(
        f"""
        SELECT day_ahead, predicted_oil_bbl
        FROM {CATALOG}.{SCHEMA}.well_forecast
        WHERE well_id = :well
        ORDER BY day_ahead
        """,
        {"well": well_id},
    )


st.title("Well Production & Forecast")
st.caption(
    f"Governed by Unity Catalog · {CATALOG}.{SCHEMA} · "
    "forecast from the registered oil_rate_predictor @champion model"
)

try:
    with st.spinner("Connecting to the SQL warehouse…"):
        wells = load_wells()
except Exception as exc:  # surface the failure instead of spinning forever
    st.error(f"Could not read dim_well: {type(exc).__name__}: {exc}")
    st.caption(
        "Checks: (1) the app has a SQL warehouse resource, (2) the warehouse is "
        "running, (3) the app's service principal has SELECT on "
        f"{CATALOG}.{SCHEMA}."
    )
    st.stop()

if wells.empty:
    st.error(
        "No wells returned. The app's service principal probably lacks SELECT on "
        f"{CATALOG}.{SCHEMA} — see the GRANT statements in the project report."
    )
    st.stop()

labels = {
    row.well_id: f"{row.well_name} — {row.operator} ({row.basin})"
    for row in wells.itertuples()
}
selected = st.selectbox(
    "Well", options=list(labels), format_func=lambda wid: labels[wid]
)

history = load_history(selected)
forecast = load_forecast(selected)

left, right = st.columns(2)

with left:
    st.subheader("Production history")
    if history.empty:
        st.info("No production records for this well.")
    else:
        st.line_chart(
            history.set_index("calendar_date")["oil_bbl"],
            x_label="Date",
            y_label="Oil (bbl/day)",
        )
        st.metric("Days on production", f"{len(history):,}")

with right:
    st.subheader("180-day forecast")
    if forecast.empty:
        st.info(
            "No forecast rows for this well — well_forecast only covers wells "
            "with status 'Producing'."
        )
    else:
        st.line_chart(
            forecast.set_index("day_ahead")["predicted_oil_bbl"],
            x_label="Days ahead",
            y_label="Predicted oil (bbl/day)",
        )
        st.metric(
            "Forecast total", f"{forecast.predicted_oil_bbl.sum():,.0f} bbl"
        )
