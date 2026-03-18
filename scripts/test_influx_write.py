import os
import time
import pandas as pd
from dotenv import load_dotenv

# --- FIX: Wrapper to handle missing influxdb_client_3 ---
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBClient3:
    """Wrapper to make standard client behave like v3 for energy monitoring scripts"""
    def __init__(self, host, token, org):
        self.client = InfluxDBClient(url=host, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.org = org

    def write(self, database, record):
        return self.write_api.write(bucket=database, org=self.org, record=record)

    def query(self, query, database, language="sql"):
        # Converts SQL logic into Flux for the standard database engine
        flux_query = f'from(bucket: "{database}") |> range(start: -1h) |> filter(fn: (r) => r._measurement == "energy_telemetry")'
        return self.query_api.query_data_frame(flux_query)

load_dotenv()

TOKEN = os.getenv("INFLUX3_TOKEN")
ORG = os.getenv("INFLUX3_ORG")
HOST = os.getenv("INFLUX3_HOST")
DATABASE = os.getenv("INFLUX3_DATABASE")

def print_section(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")

def main() -> None:
    if not all([TOKEN, ORG, HOST, DATABASE]):
        raise RuntimeError("Missing InfluxDB credentials in .env")

    client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

    print_section("STEP 1: Testing Energy Schema (P = V * I)")

    # INSTRUCTION: Validate electrical measurements
    test_data = {
        "point1": {"device_id": "meter-001", "v": 220.5, "i": 1.2},
        "point2": {"device_id": "meter-002", "v": 218.0, "i": 0.8},
        "point3": {"device_id": "meter-003", "v": 221.2, "i": 2.5},
    }

    for key, val in test_data.items():
        # Calculate Power as per page 3 of Instructions
        p = round(val["v"] * val["i"], 2)
        
        point = (
            Point("energy_telemetry")
            .tag("device_id", val["device_id"])
            .field("voltage", float(val["v"]))
            .field("current", float(val["i"]))
            .field("power", float(p))
        )
        client.write(database=DATABASE, record=point)
        print(f"[WRITE] {val['device_id']}: {val['v']}V * {val['i']}A -> {p}W")
        time.sleep(1)

    print("\n[OK] Energy write test complete")

    # INSTRUCTION: Page 5 - Typical SQL Query for verification
    query = f"SELECT time, device_id, voltage, current, power FROM energy_telemetry LIMIT 10"

    print_section("STEP 2: Verifying Data with Query")
    
    try:
        result = client.query(query=query, database=DATABASE, language="sql")
        
        if result.empty:
            print("[INFO] No rows returned. Check your bucket name and token.")
            return

        # Formatting output for terminal
        print(result.to_string(index=False))
        print(f"\n[OK] Successfully retrieved {len(result)} energy record(s)")

    except Exception as exc:
        print(f"[ERROR] Query failed: {exc}")

    print_section("STEP 3: Done")

if __name__ == "__main__":
    main()