# Test Cases

This document lists the data quality test cases implemented in `tests/test_data_quality.py`.

## Test Setup

1. Install project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Generate source telemetry and device master CSV files:

   ```bash
   python src/generate_data.py
   ```

3. Run the ingestion pipeline to create `database/telemetry.db`:

   ```bash
   python src/ingest.py
   ```

4. Run the data quality test suite:

   ```bash
   pytest tests/test_data_quality.py -v
   ```

## Test Cases

| ID | Test Case | Objective | Steps | Expected Result |
| --- | --- | --- | --- | --- |
| TC-001 | Database file exists | Verify that the ingestion pipeline creates the SQLite database. | 1. Resolve the expected database path: `database/telemetry.db`.<br>2. Check whether the file exists. | `telemetry.db` exists. |
| TC-002 | Raw table has records | Verify that raw telemetry records were loaded into SQLite. | 1. Connect to `database/telemetry.db`.<br>2. Run `SELECT COUNT(*) FROM raw_device_telemetry`.<br>3. Compare the count against zero. | Raw record count is greater than `0`. |
| TC-003 | Clean table has records | Verify that valid processed telemetry records exist. | 1. Connect to `database/telemetry.db`.<br>2. Run `SELECT COUNT(*) FROM clean_telemetry_events`.<br>3. Compare the count against zero. | Clean record count is greater than `0`. |
| TC-004 | Rejected table has bad records | Verify that invalid source records are captured in the rejected table. | 1. Connect to `database/telemetry.db`.<br>2. Run `SELECT COUNT(*) FROM rejected_telemetry_events`.<br>3. Compare the count against the expected number of intentionally bad records. | Rejected record count equals `2`. |
| TC-005 | No null device ID in clean table | Verify clean telemetry records do not contain missing `device_id` values. | 1. Query `clean_telemetry_events` for records where `device_id IS NULL`.<br>2. Count matching rows. | Null `device_id` count equals `0`. |
| TC-006 | No null event ID in clean table | Verify clean telemetry records do not contain missing `event_id` values. | 1. Query `clean_telemetry_events` for records where `event_id IS NULL`.<br>2. Count matching rows. | Null `event_id` count equals `0`. |
| TC-007 | No null firmware version in clean table | Verify clean telemetry records do not contain missing `firmware_version` values. | 1. Query `clean_telemetry_events` for records where `firmware_version IS NULL`.<br>2. Count matching rows. | Null `firmware_version` count equals `0`. |
| TC-008 | Valid event types only | Verify clean telemetry contains only approved event types. | 1. Query `clean_telemetry_events` for records where `event_type` is not in the approved list.<br>2. Count matching rows. | Invalid event type count equals `0`. |
| TC-009 | Battery level range | Verify battery level values are within the accepted range. | 1. Query `clean_telemetry_events` for records where `battery_level < 0` or `battery_level > 100`.<br>2. Count matching rows. | Out-of-range battery level count equals `0`. |
| TC-010 | CPU usage range | Verify CPU usage values are within the accepted range. | 1. Query `clean_telemetry_events` for records where `cpu_usage < 0` or `cpu_usage > 100`.<br>2. Count matching rows. | Out-of-range CPU usage count equals `0`. |
| TC-011 | Memory usage range | Verify memory usage values are within the accepted range. | 1. Query `clean_telemetry_events` for records where `memory_usage < 0` or `memory_usage > 100`.<br>2. Count matching rows. | Out-of-range memory usage count equals `0`. |
| TC-012 | No duplicate event IDs in clean table | Verify each clean telemetry event has a unique `event_id`. | 1. Group `clean_telemetry_events` by `event_id`.<br>2. Identify groups where `COUNT(*) > 1`.<br>3. Count duplicate groups. | Duplicate `event_id` group count equals `0`. |
| TC-013 | All clean devices exist in master | Verify every clean telemetry `device_id` exists in the reference device master table. | 1. Left join `clean_telemetry_events` to `device_master` on `device_id`.<br>2. Filter rows where the joined `device_master.device_id` is null.<br>3. Count unmatched rows. | Unmatched clean device count equals `0`. |
| TC-014 | Source-to-target reconciliation | Verify raw input count reconciles with clean and rejected output counts. | 1. Count records in `raw_device_telemetry`.<br>2. Count records in `clean_telemetry_events`.<br>3. Count records in `rejected_telemetry_events`.<br>4. Compare raw count to clean count plus rejected count. | `raw_count == clean_count + rejected_count`. |
| TC-015 | Daily summary matches clean table | Verify reporting summary totals reconcile with clean telemetry records. | 1. Count records in `clean_telemetry_events`.<br>2. Sum `total_events` from `daily_stability_summary`.<br>3. Compare the two values. | Clean record count equals daily summary total events. |

## Approved Event Types

- `APP_CRASH`
- `DEVICE_REBOOT`
- `MODEM_RESET`
- `CALL_DROP`
- `NETWORK_FAILURE`
- `ANR`
- `BATTERY_DRAIN`
