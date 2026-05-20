# Device Telemetry Data Pipeline & Reporting
![Telemetry Dashboard](assets/telemetry-dashboard.png)

End-to-end QA/Data Engineering project for mobile device stability telemetry.

## Tech Stack
Python, Pandas, SQLite, Pytest, Streamlit, SQL

## Features
- Simulated device telemetry data generation
- ETL ingestion into SQLite
- Clean and rejected record handling
- Data quality validation with Pytest
- Source-to-target reconciliation
- Streamlit dashboard for stability analytics

## Test Cases & Objectives

The data quality test suite validates the SQLite output created by the telemetry ingestion pipeline. Full test case documentation is available in [TEST_CASES.md](TEST_CASES.md), with an Excel version in [TEST_CASES.xlsx](TEST_CASES.xlsx).

| Area | Objective |
| --- | --- |
| Database creation | Confirm `database/telemetry.db` is created by the ingestion pipeline. |
| Raw data load | Confirm raw telemetry records are loaded into `raw_device_telemetry`. |
| Clean data load | Confirm valid processed records are available in `clean_telemetry_events`. |
| Rejected data handling | Confirm intentionally invalid records are captured in `rejected_telemetry_events`. |
| Required fields | Confirm clean records do not contain null `device_id`, `event_id`, or `firmware_version`. |
| Valid event types | Confirm clean records only contain approved telemetry event types. |
| Metric ranges | Confirm `battery_level`, `cpu_usage`, and `memory_usage` values stay between `0` and `100`. |
| Duplicate prevention | Confirm each clean telemetry event has a unique `event_id`. |
| Reference integrity | Confirm every clean `device_id` exists in the `device_master` table. |
| Source-to-target reconciliation | Confirm raw record count equals clean record count plus rejected record count. |
| Reporting reconciliation | Confirm `daily_stability_summary.total_events` matches clean telemetry volume. |

## Run Project

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/ingest.py
pytest tests/test_data_quality.py -v
streamlit run dashboard/app.py
```

## Future Enhancements

Planned future enhancements for the platform include:

- Kafka-based streaming telemetry ingestion for near real-time device event processing
- REST API-based telemetry ingestion to support application and device clients
- Real-time validation rules for rejecting malformed or incomplete telemetry events earlier in the pipeline
- MongoDB or Elasticsearch integration for large-scale telemetry search and diagnostics
- Snowflake or Azure Data Factory integration for enterprise-grade data warehousing workflows
- Cloud deployment using Azure or AWS for repeatable hosted environments
- Containerization using Docker to simplify local setup and deployment
- CI/CD pipeline expansion with automated data generation, ingestion, testing, and dashboard checks
- Power BI integration for enterprise reporting and stakeholder-ready telemetry views
- Historical trend analysis across firmware releases, carriers, regions, and device models
- Predictive firmware stability scoring based on crash, reboot, modem reset, and call drop patterns
- Automated release-risk scoring to flag unstable firmware builds before rollout
- Anomaly detection for modem resets, crash spikes, battery drain, and network failures
- Device health scoring models using telemetry quality, stability, and performance indicators
- AI-generated telemetry summaries and defect insights for faster QA triage

These enhancements would further align the project with enterprise-scale telemetry analytics, data engineering, QA automation, and reliability engineering workflows.
