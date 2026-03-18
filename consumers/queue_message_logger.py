import os
import sys
import json
import pika
from dotenv import load_dotenv

load_dotenv()

# --- INSTRUCTION: Update to Energy Monitoring Queue ---
CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "energy_telemetry" 

def callback(ch, method, properties, body):
    del ch, method, properties
    try:
        # Decode and format the JSON for better readability in the terminal
        message = json.loads(body.decode("utf-8"))
        print(f"[MSG] Received Telemetry from {message.get('device_id', 'unknown')}")
        print(f"      Voltage: {message.get('voltage')}V | Current: {message.get('current')}A")
        print("-" * 30)
    except Exception as e:
        print("[RAW MSG]", body.decode("utf-8"))

def main() -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Ensure we are looking at the energy telemetry queue
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)

        print(f"[OK] Energy Queue Logger Connected")
        print(f"[WAIT] Monitoring {QUEUE_NAME}. Press CTRL+C to exit.")

        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n[STOP] Logger stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    main()