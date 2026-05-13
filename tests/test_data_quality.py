import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "database" / "telemetry.db"


def run_query(query):
    """Helper function to run SQL query and return first value."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()[0]


def test_database_file_exists():
    """Verify SQLite database was created by ingestion pipeline."""
    assert DB_FILE.exists()


def test_raw_table_has_records():
    """Verify raw telemetry table is not empty."""
    count = run_query("SELECT COUNT(*) FROM raw_device_telemetry")
    assert count > 0


def test_clean_table_has_records():
    """Verify clean telemetry table contains valid processed records."""
    count = run_query("SELECT COUNT(*) FROM clean_telemetry_events")
    assert count > 0


def test_rejected_table_has_bad_records():
    """Verify invalid records are captured in rejected table."""
    count = run_query("SELECT COUNT(*) FROM rejected_telemetry_events")
    assert count == 2


def test_no_null_device_id_in_clean_table():
    """Clean table should not contain null device_id."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE device_id IS NULL
    """)
    assert count == 0


def test_no_null_event_id_in_clean_table():
    """Clean table should not contain null event_id."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE event_id IS NULL
    """)
    assert count == 0


def test_no_null_firmware_version_in_clean_table():
    """Clean table should not contain null firmware_version."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE firmware_version IS NULL
    """)
    assert count == 0


def test_valid_event_types_only():
    """Clean table should only contain approved telemetry event types."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE event_type NOT IN (
            'APP_CRASH',
            'DEVICE_REBOOT',
            'MODEM_RESET',
            'CALL_DROP',
            'NETWORK_FAILURE',
            'ANR',
            'BATTERY_DRAIN'
        )
    """)
    assert count == 0


def test_battery_level_range():
    """Battery level should be between 0 and 100."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE battery_level < 0 OR battery_level > 100
    """)
    assert count == 0


def test_cpu_usage_range():
    """CPU usage should be between 0 and 100."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE cpu_usage < 0 OR cpu_usage > 100
    """)
    assert count == 0


def test_memory_usage_range():
    """Memory usage should be between 0 and 100."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events
        WHERE memory_usage < 0 OR memory_usage > 100
    """)
    assert count == 0


def test_no_duplicate_event_ids_in_clean_table():
    """Each clean telemetry event should have a unique event_id."""
    count = run_query("""
        SELECT COUNT(*)
        FROM (
            SELECT event_id
            FROM clean_telemetry_events
            GROUP BY event_id
            HAVING COUNT(*) > 1
        )
    """)
    assert count == 0


def test_all_clean_devices_exist_in_master():
    """Every clean device_id should exist in device master reference table."""
    count = run_query("""
        SELECT COUNT(*)
        FROM clean_telemetry_events c
        LEFT JOIN device_master d
            ON c.device_id = d.device_id
        WHERE d.device_id IS NULL
    """)
    assert count == 0


def test_source_to_target_reconciliation():
    """
    Raw count should equal clean count plus rejected count.
    This is a core ETL source-to-target validation.
    """
    raw_count = run_query("SELECT COUNT(*) FROM raw_device_telemetry")
    clean_count = run_query("SELECT COUNT(*) FROM clean_telemetry_events")
    rejected_count = run_query("SELECT COUNT(*) FROM rejected_telemetry_events")

    assert raw_count == clean_count + rejected_count


def test_daily_summary_matches_clean_table():
    """
    Reporting summary total_events should match clean table count.
    This validates backend-to-reporting reconciliation.
    """
    clean_count = run_query("SELECT COUNT(*) FROM clean_telemetry_events")
    summary_total = run_query("SELECT SUM(total_events) FROM daily_stability_summary")

    assert clean_count == summary_total