import json
import os
import time
import pika
from dotenv import load_dotenv

load_dotenv()

def main():
    params = pika.URLParameters(os.getenv("CLOUDAMQP_URL"))
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="energy_telemetry", durable=True)

    print("[OK] Single Energy Meter Producer connected")

    try:
        while True:
            v  = 220.5
            i  = 2.1
            payload = {
                "device_id":    "meter-001",
                "voltage":      v,
                "current":      i,
                "power":        round(v * i, 2),
                "energy":       15.6,
                "power_factor": 0.94,
                "frequency":    50.0,
                "device_type":  "industrial_monitor"
            }
            channel.basic_publish(exchange="", routing_key="energy_telemetry", body=json.dumps(payload))
            print(f"[PUB] meter-001 -> {payload['voltage']}V, {payload['current']}A, {payload['power']}W")
            time.sleep(5)
    except KeyboardInterrupt:
        connection.close()

if __name__ == "__main__":
    main()