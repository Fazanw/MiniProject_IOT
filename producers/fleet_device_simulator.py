import json
import os
import random
import time
import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry" 

def make_energy_payload(device_id):
    v  = round(random.uniform(210, 240), 1)
    i  = round(random.uniform(0.5, 10.0), 2)
    p  = round(v * i, 2)
    e  = round(random.uniform(0, 100), 2)
    pf = round(random.uniform(0.80, 1.00), 2)
    hz = round(random.uniform(49.5, 50.5), 1)
    return {
        "device_id":    device_id,
        "voltage":      v,
        "current":      i,
        "power":        p,
        "energy":       e,
        "power_factor": pf,
        "frequency":    hz,
        "device_type":  "smart_meter",
        "ts":           time.time()
    }

def main():
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    params = pika.URLParameters(CLOUDAMQP_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    print(f"[OK] Fleet Simulator started. Sending to {QUEUE_NAME}...")

    try:
        while True:
            for i in range(1, 6): # Simulating 5 meters
                device_id = f"meter-{i:03d}"
                payload = make_energy_payload(device_id)
                
                body = json.dumps(payload)
                channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=body)
                print(f"[PUB] {device_id} -> {payload['voltage']}V, {payload['current']}A, {payload['power']}W")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[STOP] Stopping simulator...")
        connection.close()

if __name__ == "__main__":
    main()