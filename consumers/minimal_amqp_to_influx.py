import json
import os
import pika
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- FIX: Wrapper to handle missing influxdb_client_3 ---
class InfluxDBClient3:
    def __init__(self, host, token, org):
        self.client = InfluxDBClient(url=host, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.org = org
    def write(self, database, record):
        return self.write_api.write(bucket=database, org=self.org, record=record)

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry" # Updated per instructions

TOKEN = os.getenv("INFLUX3_TOKEN")
ORG = os.getenv("INFLUX3_ORG")
HOST = os.getenv("INFLUX3_HOST")
DATABASE = os.getenv("INFLUX3_DATABASE")

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))

        # INSTRUCTION: Calculate Power (P = V * I)
        # These fields must match what your Wokwi/Simulator is sending
        v = float(data.get("voltage", 0))
        i = float(data.get("current", 0))
        p = round(v * i, 2)

        point = (
            Point("energy_telemetry") # Updated measurement name
            .tag("device_id", data["device_id"])
            .field("voltage", v)
            .field("current", i)
            .field("power", p)
        )

        client.write(database=DATABASE, record=point)
        print(f"[WRITE] {data['device_id']} -> {v}V, {i}A, {p}W")
        
    except Exception as exc:
        print("[ERROR]", exc)

def main() -> None:
    global client

    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")
    if not all([TOKEN, ORG, HOST, DATABASE]):
        raise RuntimeError("Missing InfluxDB credentials in .env")

    client = InfluxDBClient3(host=HOST, token=TOKEN, org=ORG)

    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    
    # Ensure queue matches the producer
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    channel.basic_consume(
        queue=QUEUE_NAME, 
        on_message_callback=callback, 
        auto_ack=True
    )

    print("[OK] Minimal Energy Ingestion Service connected")
    print(f"[WAIT] Monitoring queue: {QUEUE_NAME}")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("[STOP] Interrupted by user")
        connection.close()

if __name__ == "__main__":
    main()