import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "data" / "reference"

RAW_DIR.mkdir(parents=True, exist_ok=True)
REF_DIR.mkdir(parents=True, exist_ok=True)


event_types = [
    "APP_CRASH",
    "DEVICE_REBOOT",
    "MODEM_RESET",
    "CALL_DROP",
    "NETWORK_FAILURE",
    "ANR",
    "BATTERY_DRAIN",
]

firmware_versions = ["S24_U1_6.1", "S24_U2_6.1", "S23_U5_6.0"]
carriers = ["Verizon", "AT&T", "T-Mobile"]
network_types = ["LTE", "5G", "WiFi"]
severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
device_models = ["Galaxy S24", "Galaxy S23", "Galaxy Z Fold 5"]


# ---------------------------------------------------
# Generate device master reference data
# ---------------------------------------------------

devices = []

for i in range(1, 51):
    devices.append(
        {
            "device_id": f"DVC-{i:03}",
            "device_model": random.choice(device_models),
            "os_version": random.choice(["Android 14", "Android 15"]),
            "region": random.choice(["US-East", "US-West", "US-Central"]),
            "active_flag": "Y",
        }
    )

device_master_df = pd.DataFrame(devices)
device_master_df.to_csv(REF_DIR / "device_master.csv", index=False)


# ---------------------------------------------------
# Generate telemetry event data
# ---------------------------------------------------

records = []
start_date = datetime.now() - timedelta(days=30)

for i in range(1, 5001):
    device = random.choice(devices)

    firmware = random.choice(firmware_versions)
    carrier = random.choice(carriers)

    # Simulate unstable firmware behavior
    if firmware == "S24_U2_6.1":
        event_weights = {
            "APP_CRASH": 25,
            "DEVICE_REBOOT": 20,
            "MODEM_RESET": 20,
            "CALL_DROP": 15,
            "NETWORK_FAILURE": 10,
            "ANR": 5,
            "BATTERY_DRAIN": 5,
        }

    elif firmware == "S23_U5_6.0":
        event_weights = {
            "APP_CRASH": 10,
            "DEVICE_REBOOT": 5,
            "MODEM_RESET": 5,
            "CALL_DROP": 10,
            "NETWORK_FAILURE": 15,
            "ANR": 20,
            "BATTERY_DRAIN": 35,
        }

    else:
        event_weights = {
            "APP_CRASH": 15,
            "DEVICE_REBOOT": 10,
            "MODEM_RESET": 10,
            "CALL_DROP": 10,
            "NETWORK_FAILURE": 10,
            "ANR": 20,
            "BATTERY_DRAIN": 25,
        }

    event_type = random.choices(
        population=list(event_weights.keys()),
        weights=list(event_weights.values()),
        k=1,
    )[0]

    # Carrier-specific instability
    if carrier == "T-Mobile" and random.random() < 0.20:
        event_type = "NETWORK_FAILURE"

    if carrier == "Verizon" and random.random() < 0.15:
        event_type = "CALL_DROP"

    # Severity logic
    if event_type in ["DEVICE_REBOOT", "MODEM_RESET"]:
        severity = random.choice(["HIGH", "CRITICAL"])

    elif event_type in ["CALL_DROP", "NETWORK_FAILURE"]:
        severity = random.choice(["MEDIUM", "HIGH"])

    else:
        severity = random.choice(severity_levels)

    # Overnight stress testing simulation
    stress_hour = random.choice([0, 1, 2, 3, 4, 22, 23])

    timestamp = start_date + timedelta(
        days=random.randint(0, 30),
        hours=stress_hour,
        minutes=random.randint(0, 59),
    )

    # CPU and memory spike simulation
    if event_type in ["APP_CRASH", "ANR"]:
        cpu_usage = random.randint(70, 100)
        memory_usage = random.randint(75, 100)

    else:
        cpu_usage = random.randint(10, 90)
        memory_usage = random.randint(10, 90)

    # Battery drain simulation
    if event_type == "BATTERY_DRAIN":
        battery_level = random.randint(1, 15)

    else:
        battery_level = random.randint(20, 100)

    records.append(
        {
            "event_id": str(uuid.uuid4()),
            "device_id": device["device_id"],
            "test_session_id": f"TS-{random.randint(1000, 1100)}",
            "event_timestamp": timestamp,
            "event_type": event_type,
            "firmware_version": firmware,
            "carrier": carrier,
            "network_type": random.choice(network_types),
            "battery_level": battery_level,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "app_name": random.choice(
                ["Camera", "Messages", "Phone", "Settings", "Samsung Health"]
            ),
            "severity": severity,
            "error_code": f"ERR-{random.randint(100, 999)}",
            "region": device["region"],
        }
    )

telemetry_df = pd.DataFrame(records)


# ---------------------------------------------------
# Add intentionally bad records for validation testing
# ---------------------------------------------------

bad_records = pd.DataFrame(
    [
        {
            "event_id": None,
            "device_id": "DVC-001",
            "test_session_id": "TS-9999",
            "event_timestamp": datetime.now(),
            "event_type": "APP_CRASH",
            "firmware_version": "S24_U1_6.1",
            "carrier": "Verizon",
            "network_type": "5G",
            "battery_level": 50,
            "cpu_usage": 70,
            "memory_usage": 80,
            "app_name": "Camera",
            "severity": "HIGH",
            "error_code": "ERR-101",
            "region": "US-East",
        },
        {
            "event_id": str(uuid.uuid4()),
            "device_id": None,
            "test_session_id": "TS-9998",
            "event_timestamp": datetime.now(),
            "event_type": "MODEM_RESET",
            "firmware_version": None,
            "carrier": "T-Mobile",
            "network_type": "LTE",
            "battery_level": 120,
            "cpu_usage": 110,
            "memory_usage": 75,
            "app_name": "Phone",
            "severity": "CRITICAL",
            "error_code": "ERR-202",
            "region": "US-West",
        },
    ]
)

telemetry_df = pd.concat([telemetry_df, bad_records], ignore_index=True)

telemetry_df.to_csv(RAW_DIR / "telemetry_events.csv", index=False)


print("Sample telemetry data generated successfully.")
print(f"Telemetry records: {len(telemetry_df)}")
print(f"Device master records: {len(device_master_df)}")
print(f"Raw telemetry file: {RAW_DIR / 'telemetry_events.csv'}")
print(f"Device master file: {REF_DIR / 'device_master.csv'}")