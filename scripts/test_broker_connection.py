import json
import os
import time
from datetime import datetime, timezone

import pika
from dotenv import load_dotenv

load_dotenv()

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL")
QUEUE_NAME = "broker_test_queue"


def build_test_message() -> str:
    payload = {
        "type": "broker_test",
        "status": "ok",
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload)


def main() -> None:
    if not CLOUDAMQP_URL:
        raise RuntimeError("Missing CLOUDAMQP_URL in .env")

    params = pika.URLParameters(CLOUDAMQP_URL)
    params.socket_timeout = 5

    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    print(f"[OK] Queue declared: {QUEUE_NAME}")

    message = build_test_message()
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=message)
    print(f"[OK] Test message published: {message}")

    time.sleep(1)
    connection.close()
    print("[OK] Connection closed")


if __name__ == "__main__":
    main()