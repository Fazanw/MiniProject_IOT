import json
import os
import pika
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Wrapper Fix for ModuleNotFoundError
class InfluxDBClient3:
    def __init__(self, host, token, org):
        self.client = InfluxDBClient(url=host, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.org = org
    def write(self, database, record):
        return self.write_api.write(bucket=database, org=self.org, record=record)

load_dotenv()

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode("utf-8"))

        voltage      = float(data.get("voltage", 0))
        current      = float(data.get("current", 0))
        power        = round(data.get("power", voltage * current), 2)
        energy       = float(data.get("energy", 0))
        power_factor = float(data.get("power_factor", 1.0))
        frequency    = float(data.get("frequency", 50.0))

        point = (
            Point("energy_telemetry")
            .tag("device_id", data["device_id"])
            .tag("device_type", data.get("device_type", "smart-meter"))
            .field("voltage", voltage)
            .field("current", current)
            .field("power", power)
            .field("energy", energy)
            .field("power_factor", power_factor)
            .field("frequency", frequency)
        )

        client.write(database=os.getenv("INFLUX3_DATABASE"), record=point)
        print(f"[INGEST] {data['device_id']}: {voltage}V, {current}A, {power}W, {energy}kWh, PF={power_factor}, {frequency}Hz")
        
    except Exception as exc:
        print("[ERROR]", exc)

def main():
    global client
    client = InfluxDBClient3(
        host=os.getenv("INFLUX3_HOST"), 
        token=os.getenv("INFLUX3_TOKEN"), 
        org=os.getenv("INFLUX3_ORG")
    )

    params = pika.URLParameters(os.getenv("CLOUDAMQP_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="energy_telemetry", durable=True)
    
    channel.basic_consume(queue="energy_telemetry", on_message_callback=callback, auto_ack=True)
    print("[OK] Energy Ingestion Service Running...")
    channel.start_consuming()

if __name__ == "__main__":
    main()