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


@st.cache_resource
def connection():
    """Connect to the SQL warehouse using the app's own service principal."""
    cfg = Config()  # picks up DATABRICKS_HOST + the app's OAuth credentials
    return sql.connect(
        server_hostname=cfg.host,
        http_path=os.environ["DATABRICKS_WAREHOUSE_HTTP_PATH"],
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

wells = load_wells()
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
