import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "raw" / "telemetry_events.csv"
DEVICE_MASTER_FILE = BASE_DIR / "data" / "reference" / "device_master.csv"
DB_FILE = BASE_DIR / "database" / "telemetry.db"

DB_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_csv_files():
    telemetry_df = pd.read_csv(RAW_FILE)
    device_master_df = pd.read_csv(DEVICE_MASTER_FILE)
    return telemetry_df, device_master_df


def validate_records(telemetry_df, device_master_df):
    valid_event_types = [
        "APP_CRASH",
        "DEVICE_REBOOT",
        "MODEM_RESET",
        "CALL_DROP",
        "NETWORK_FAILURE",
        "ANR",
        "BATTERY_DRAIN",
    ]

    valid_device_ids = set(device_master_df["device_id"])

    rejected_df = telemetry_df[
        telemetry_df["event_id"].isnull()
        | telemetry_df["device_id"].isnull()
        | telemetry_df["firmware_version"].isnull()
        | telemetry_df["event_timestamp"].isnull()
        | ~telemetry_df["event_type"].isin(valid_event_types)
        | ~telemetry_df["device_id"].isin(valid_device_ids)
        | (telemetry_df["battery_level"] < 0)
        | (telemetry_df["battery_level"] > 100)
        | (telemetry_df["cpu_usage"] < 0)
        | (telemetry_df["cpu_usage"] > 100)
        | (telemetry_df["memory_usage"] < 0)
        | (telemetry_df["memory_usage"] > 100)
        | telemetry_df.duplicated(subset=["event_id"], keep=False)
    ].copy()

    clean_df = telemetry_df.drop(rejected_df.index).copy()

    return clean_df, rejected_df


def transform_clean_records(clean_df):
    failure_mapping = {
        "APP_CRASH": "Application Stability",
        "ANR": "Application Stability",
        "DEVICE_REBOOT": "Device Stability",
        "MODEM_RESET": "Modem Stability",
        "CALL_DROP": "Network Stability",
        "NETWORK_FAILURE": "Network Stability",
        "BATTERY_DRAIN": "Power Stability",
    }

    clean_df["failure_category"] = clean_df["event_type"].map(failure_mapping)

    clean_df["is_critical"] = clean_df.apply(
        lambda row: (
            row["event_type"] in ["DEVICE_REBOOT", "MODEM_RESET", "CALL_DROP"]
            or (
                row["event_type"] == "APP_CRASH"
                and row["severity"] in ["HIGH", "CRITICAL"]
            )
        ),
        axis=1,
    )

    clean_df["event_timestamp"] = pd.to_datetime(clean_df["event_timestamp"])
    clean_df["event_date"] = clean_df["event_timestamp"].dt.date.astype(str)

    return clean_df


def create_daily_summary(clean_df, device_master_df):
    enriched_df = clean_df.merge(
        device_master_df[["device_id", "device_model"]],
        on="device_id",
        how="left",
    )

    summary_df = (
        enriched_df.groupby(
            ["event_date", "firmware_version", "device_model", "carrier"],
            as_index=False,
        )
        .agg(
            total_events=("event_id", "count"),
            app_crashes=("event_type", lambda x: (x == "APP_CRASH").sum()),
            device_reboots=("event_type", lambda x: (x == "DEVICE_REBOOT").sum()),
            modem_resets=("event_type", lambda x: (x == "MODEM_RESET").sum()),
            call_drops=("event_type", lambda x: (x == "CALL_DROP").sum()),
            network_failures=("event_type", lambda x: (x == "NETWORK_FAILURE").sum()),
            critical_events=("is_critical", "sum"),
        )
    )

    summary_df["stability_score"] = 100 - (
        summary_df["device_reboots"] * 10
        + summary_df["modem_resets"] * 8
        + summary_df["call_drops"] * 6
        + summary_df["app_crashes"] * 5
        + summary_df["network_failures"] * 4
    )

    summary_df["stability_score"] = summary_df["stability_score"].clip(lower=0)

    return summary_df


def load_to_sqlite(device_master_df, telemetry_df, clean_df, rejected_df, summary_df):
    with sqlite3.connect(DB_FILE) as conn:
        device_master_df.to_sql("device_master", conn, if_exists="replace", index=False)
        telemetry_df.to_sql("raw_device_telemetry", conn, if_exists="replace", index=False)
        clean_df.to_sql("clean_telemetry_events", conn, if_exists="replace", index=False)
        rejected_df.to_sql("rejected_telemetry_events", conn, if_exists="replace", index=False)
        summary_df.to_sql("daily_stability_summary", conn, if_exists="replace", index=False)


def main():
    telemetry_df, device_master_df = load_csv_files()

    clean_df, rejected_df = validate_records(telemetry_df, device_master_df)
    clean_df = transform_clean_records(clean_df)

    summary_df = create_daily_summary(clean_df, device_master_df)

    load_to_sqlite(
        device_master_df,
        telemetry_df,
        clean_df,
        rejected_df,
        summary_df,
    )

    print("SQLite ingestion completed successfully.")
    print(f"Raw records: {len(telemetry_df)}")
    print(f"Clean records: {len(clean_df)}")
    print(f"Rejected records: {len(rejected_df)}")
    print(f"Daily summary records: {len(summary_df)}")
    print(f"Database created at: {DB_FILE}")


if __name__ == "__main__":
    main()