import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ---------------------------------------------------
# File paths
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "telemetry.db"


# ---------------------------------------------------
# Load data from SQLite
# ---------------------------------------------------

@st.cache_data
def load_data():
    with sqlite3.connect(DB_FILE) as conn:
        raw_df = pd.read_sql_query("SELECT * FROM raw_device_telemetry", conn)
        clean_df = pd.read_sql_query("SELECT * FROM clean_telemetry_events", conn)
        summary_df = pd.read_sql_query("SELECT * FROM daily_stability_summary", conn)
        rejected_df = pd.read_sql_query("SELECT * FROM rejected_telemetry_events", conn)

    clean_df["event_timestamp"] = pd.to_datetime(clean_df["event_timestamp"])
    clean_df["event_date"] = pd.to_datetime(clean_df["event_date"])
    clean_df["event_hour"] = clean_df["event_timestamp"].dt.hour

    return raw_df, clean_df, summary_df, rejected_df


# ---------------------------------------------------
# Streamlit page setup
# ---------------------------------------------------

st.set_page_config(
    page_title="Device Telemetry Stability Dashboard",
    layout="wide"
)

st.title("Device Telemetry Stability Dashboard")
st.caption("Mobile Stability Test Telemetry | ETL Validation | Reporting Analytics")

raw_df, clean_df, summary_df, rejected_df = load_data()


# ---------------------------------------------------
# Sidebar filters
# ---------------------------------------------------

st.sidebar.header("Filters")

firmware_filter = st.sidebar.multiselect(
    "Firmware Version",
    options=sorted(clean_df["firmware_version"].unique()),
    default=sorted(clean_df["firmware_version"].unique())
)

carrier_filter = st.sidebar.multiselect(
    "Carrier",
    options=sorted(clean_df["carrier"].unique()),
    default=sorted(clean_df["carrier"].unique())
)

event_filter = st.sidebar.multiselect(
    "Event Type",
    options=sorted(clean_df["event_type"].unique()),
    default=sorted(clean_df["event_type"].unique())
)

severity_filter = st.sidebar.multiselect(
    "Severity",
    options=sorted(clean_df["severity"].unique()),
    default=sorted(clean_df["severity"].unique())
)

filtered_df = clean_df[
    clean_df["firmware_version"].isin(firmware_filter)
    & clean_df["carrier"].isin(carrier_filter)
    & clean_df["event_type"].isin(event_filter)
    & clean_df["severity"].isin(severity_filter)
]


# ---------------------------------------------------
# Executive KPI section
# ---------------------------------------------------

st.header("Executive Stability Overview")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Raw Records", len(raw_df))
col2.metric("Clean Records", len(clean_df))
col3.metric("Rejected Records", len(rejected_df))
col4.metric("Filtered Events", len(filtered_df))
col5.metric("Devices Tested", filtered_df["device_id"].nunique())

col6, col7, col8, col9 = st.columns(4)

critical_count = int(filtered_df["is_critical"].sum())
app_crash_count = len(filtered_df[filtered_df["event_type"] == "APP_CRASH"])
reboot_count = len(filtered_df[filtered_df["event_type"] == "DEVICE_REBOOT"])
modem_reset_count = len(filtered_df[filtered_df["event_type"] == "MODEM_RESET"])

col6.metric("Critical Events", critical_count)
col7.metric("App Crashes", app_crash_count)
col8.metric("Device Reboots", reboot_count)
col9.metric("Modem Resets", modem_reset_count)


# ---------------------------------------------------
# Failure count by event type
# ---------------------------------------------------

st.header("Failure Analysis")

event_counts = (
    filtered_df["event_type"]
    .value_counts()
    .reset_index()
)

event_counts.columns = ["event_type", "failure_count"]

st.subheader("Failure Count by Event Type")
st.bar_chart(event_counts, x="event_type", y="failure_count")


# ---------------------------------------------------
# Firmware stability analysis
# ---------------------------------------------------

st.subheader("Firmware Stability Analysis")

firmware_summary = (
    filtered_df.groupby("firmware_version")
    .agg(
        total_events=("event_id", "count"),
        critical_failures=("is_critical", "sum"),
        app_crashes=("event_type", lambda x: (x == "APP_CRASH").sum()),
        device_reboots=("event_type", lambda x: (x == "DEVICE_REBOOT").sum()),
        modem_resets=("event_type", lambda x: (x == "MODEM_RESET").sum()),
        call_drops=("event_type", lambda x: (x == "CALL_DROP").sum()),
        network_failures=("event_type", lambda x: (x == "NETWORK_FAILURE").sum()),
        battery_drain_events=("event_type", lambda x: (x == "BATTERY_DRAIN").sum()),
    )
    .reset_index()
)

firmware_summary["stability_score"] = 100 - (
    firmware_summary["device_reboots"] * 10
    + firmware_summary["modem_resets"] * 8
    + firmware_summary["call_drops"] * 6
    + firmware_summary["app_crashes"] * 5
    + firmware_summary["network_failures"] * 4
)

firmware_summary["stability_score"] = firmware_summary["stability_score"].clip(lower=0)

st.dataframe(firmware_summary, use_container_width=True)

st.bar_chart(
    firmware_summary,
    x="firmware_version",
    y="critical_failures"
)


# ---------------------------------------------------
# Daily failure trend
# ---------------------------------------------------

st.subheader("Daily Failure Trend")

daily_counts = (
    filtered_df.groupby("event_date")
    .size()
    .reset_index(name="failure_count")
)

st.line_chart(daily_counts, x="event_date", y="failure_count")


# ---------------------------------------------------
# Carrier network failure analysis
# ---------------------------------------------------

st.subheader("Carrier Network Failure Analysis")

carrier_failures = (
    filtered_df[filtered_df["event_type"] == "NETWORK_FAILURE"]
    .groupby("carrier")
    .size()
    .reset_index(name="network_failures")
)

st.dataframe(carrier_failures, use_container_width=True)

st.bar_chart(
    carrier_failures,
    x="carrier",
    y="network_failures"
)


# ---------------------------------------------------
# Overnight stress test analysis
# ---------------------------------------------------

st.subheader("Failure Distribution by Hour")

hourly_failures = (
    filtered_df.groupby("event_hour")
    .size()
    .reset_index(name="failure_count")
)

st.line_chart(
    hourly_failures,
    x="event_hour",
    y="failure_count"
)

st.caption(
    "Use this to identify overnight stress-test failure spikes, especially between 12 AM and 4 AM."
)


# ---------------------------------------------------
# Device hotspot analysis
# ---------------------------------------------------

st.subheader("Top Unstable Devices")

device_failures = (
    filtered_df.groupby("device_id")
    .size()
    .reset_index(name="failure_count")
    .sort_values(by="failure_count", ascending=False)
    .head(10)
)

st.dataframe(device_failures, use_container_width=True)

st.bar_chart(
    device_failures,
    x="device_id",
    y="failure_count"
)


# ---------------------------------------------------
# Battery drain analysis
# ---------------------------------------------------

st.subheader("Battery Drain Analysis by Firmware")

battery_drain_df = filtered_df[
    filtered_df["event_type"] == "BATTERY_DRAIN"
]

battery_summary = (
    battery_drain_df.groupby("firmware_version")
    .size()
    .reset_index(name="battery_drain_count")
)

st.dataframe(battery_summary, use_container_width=True)

st.bar_chart(
    battery_summary,
    x="firmware_version",
    y="battery_drain_count"
)


# ---------------------------------------------------
# Critical failure events
# ---------------------------------------------------

st.subheader("Critical Failure Events")

critical_events = filtered_df[
    filtered_df["is_critical"] == 1
]

st.dataframe(
    critical_events[
        [
            "event_timestamp",
            "device_id",
            "event_type",
            "firmware_version",
            "carrier",
            "network_type",
            "severity",
            "failure_category",
            "battery_level",
            "cpu_usage",
            "memory_usage",
        ]
    ],
    use_container_width=True
)


# ---------------------------------------------------
# Data quality / rejected records
# ---------------------------------------------------

st.header("Data Quality Exceptions")

st.subheader("Rejected Telemetry Records")

st.dataframe(
    rejected_df,
    use_container_width=True
)


# ---------------------------------------------------
# Backend reconciliation
# ---------------------------------------------------

st.header("Backend Reconciliation")

raw_count = len(raw_df)
clean_count = len(clean_df)
rejected_count = len(rejected_df)

recon_status = "PASS" if raw_count == clean_count + rejected_count else "FAIL"

recon_df = pd.DataFrame(
    {
        "Metric": [
            "Raw Records",
            "Clean Records",
            "Rejected Records",
            "Clean + Rejected",
            "Reconciliation Status",
        ],
        "Value": [
            raw_count,
            clean_count,
            rejected_count,
            clean_count + rejected_count,
            recon_status,
        ],
    }
)

st.dataframe(recon_df, use_container_width=True)


# ---------------------------------------------------
# Sample engineering insights
# ---------------------------------------------------

st.header("Sample Engineering Insights")

if not firmware_summary.empty:
    worst_firmware = firmware_summary.sort_values(
        by="critical_failures",
        ascending=False
    ).iloc[0]["firmware_version"]

    st.write(
        f"Firmware **{worst_firmware}** currently shows the highest critical failure volume."
    )

if not carrier_failures.empty:
    worst_carrier = carrier_failures.sort_values(
        by="network_failures",
        ascending=False
    ).iloc[0]["carrier"]

    st.write(
        f"Carrier **{worst_carrier}** shows the highest network failure count."
    )

if not device_failures.empty:
    worst_device = device_failures.iloc[0]["device_id"]

    st.write(
        f"Device **{worst_device}** is the top unstable device by total failure count."
    )

st.write(
    "Rejected records are isolated separately, allowing QA teams to validate data quality exceptions without corrupting reporting tables."
)