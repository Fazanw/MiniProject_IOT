# Cloud IoT Workshop

A hands-on workshop demonstrating a **cloud-based IoT telemetry pipeline** using managed services and Python-based device simulation.

The workshop simulates a fleet of IoT devices sending telemetry to a cloud message broker, which is then ingested into a time-series database and visualized using Grafana.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Environment Configuration](#environment-configuration)
- [Script Overview](#script-overview)
- [Producer Scripts](#producer-scripts)
- [Consumer Scripts](#consumer-scripts)
- [Running the End-to-End Demo](#running-the-end-to-end-demo)
- [Querying Data in InfluxDB](#querying-data-in-influxdb)
- [Grafana Dashboards](#grafana-dashboards)
- [Troubleshooting](#troubleshooting)
- [Workshop Agenda](#workshop-agenda)

---

## Architecture Overview

```
Python Device Simulators
        │
        ▼
CloudAMQP (LavinMQ) Queue
        │
        ▼
Python Ingestion Service
        │
        ▼
InfluxDB 3 (Time-Series Database)
        │
        ▼
Grafana Dashboards
```

**Pipeline flow:**

```
Producer(s) → CloudAMQP Queue → Consumer → InfluxDB → Grafana
```

| Component        | Role                                         |
| ---------------- | -------------------------------------------- |
| Python Producers | Simulated IoT devices sending telemetry      |
| CloudAMQP        | Managed message broker buffering device data |
| Python Consumer  | Reads queue messages and stores them         |
| InfluxDB 3       | Time-series database for telemetry           |
| Grafana          | Visualization dashboards                     |

---

## Project Structure

```
cloud-iot-workshop/
│
├── requirements.txt
├── .env.example
├── README.md
│
├── scripts/
│   ├── test_broker_connection.py
│   └── test_influx_write.py
│
├── producers/
│   ├── single_device_producer.py
│   └── fleet_device_simulator.py
│
└── consumers/
    ├── queue_message_logger.py
    ├── minimal_amqp_to_influx.py
    └── amqp_to_influx_service.py
```

---

## Environment Setup

### 1. Install Python

Requires **Python 3.10+**

```bash
python --version
```

### 2. Create virtual environment

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

| Package          | Purpose                          |
| ---------------- | -------------------------------- |
| pika             | AMQP client for CloudAMQP        |
| influxdb3-python | InfluxDB client                  |
| python-dotenv    | Load environment variables       |
| pandas           | Used for query output formatting |

---

## Environment Configuration

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

```env
CLOUDAMQP_URL=amqps://USERNAME:PASSWORD@dog.lmq.cloudamqp.com/VHOST

INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=Dev
INFLUX3_DATABASE=room-monitoring
INFLUX3_TOKEN=YOUR_INFLUX_TOKEN
```

| Variable         | Description                     |
| ---------------- | ------------------------------- |
| CLOUDAMQP_URL    | CloudAMQP broker connection URL |
| INFLUX3_HOST     | InfluxDB Cloud endpoint         |
| INFLUX3_ORG      | Influx organization             |
| INFLUX3_DATABASE | Database name                   |
| INFLUX3_TOKEN    | API token                       |

---

## Script Overview

### `scripts/test_broker_connection.py`

Tests connectivity to CloudAMQP:

1. Connect to AMQP broker
2. Declare queue
3. Publish test message
4. Close connection

```bash
python scripts/test_broker_connection.py
```

Expected output:

```
[OK] Queue declared
[OK] Test message published
```

### `scripts/test_influx_write.py`

Validates InfluxDB connectivity by writing sample points and running a query.

```bash
python scripts/test_influx_write.py
```

Expected output:

```
STEP 1: Writing test points
STEP 2: Running query
STEP 3: Query results
```

---

## Producer Scripts

Producer scripts simulate IoT devices publishing telemetry to the `iot_telemetry` queue.

### `single_device_producer.py`

Simulates a single IoT device.

```bash
python producers/single_device_producer.py
```

Example payload:

```json
{
  "device_id": "device-001",
  "region": "north",
  "temperature": 29.4,
  "humidity": 81.2,
  "soil_moisture": 53.1,
  "battery": 87,
  "signal_rssi": -68
}
```

### `fleet_device_simulator.py`

Simulates **20 devices** concurrently with randomized telemetry and publish intervals.

```bash
python producers/fleet_device_simulator.py
```

Example output:

```
[PUB] device-005 -> {...}
[PUB] device-012 -> {...}
```

---

## Consumer Scripts

### `queue_message_logger.py`

Debugging consumer — prints raw messages from the queue.

```bash
python consumers/queue_message_logger.py
```

```
[MSG] {"device_id":"device-001",...}
```

### `minimal_amqp_to_influx.py`

Minimal ingestion pipeline. Stores `device_id`, `region`, `temperature`, and `humidity`.

```bash
python consumers/minimal_amqp_to_influx.py
```

### `amqp_to_influx_service.py`

Full ingestion service for the final workshop demo.

```
Queue message → JSON decode → InfluxDB Point → Write to database
```

| Tag         | Field         |
| ----------- | ------------- |
| device_id   | temperature   |
| region      | humidity      |
| device_type | soil_moisture |
|             | battery       |
|             | signal_rssi   |

```bash
python consumers/amqp_to_influx_service.py
```

```
[WRITE] device-004 -> InfluxDB
```

---

## Running the End-to-End Demo

Open two terminals.

**Terminal 1** — start the ingestion service:

```bash
python consumers/amqp_to_influx_service.py
```

**Terminal 2** — start the fleet simulator:

```bash
python producers/fleet_device_simulator.py
```

Expected behavior:

| Component  | Output                    |
| ---------- | ------------------------- |
| Producer   | `[PUB] device-003 -> ...` |
| Consumer   | `[WRITE] device-003 -> InfluxDB` |
| CloudAMQP  | Queue activity visible    |
| InfluxDB   | Row count increasing      |

---

## Querying Data in InfluxDB

**Latest telemetry:**

```sql
SELECT *
FROM iot_telemetry
ORDER BY time DESC
LIMIT 20;
```

**Average temperature by region:**

```sql
SELECT region, AVG(temperature)
FROM iot_telemetry
GROUP BY region;
```

**Battery health:**

```sql
SELECT device_id, battery
FROM iot_telemetry
ORDER BY battery ASC
LIMIT 20;
```

---

## Grafana Dashboards

| Panel                        | Type             | Query                                              |
| ---------------------------- | ---------------- | -------------------------------------------------- |
| Temperature over time        | Time series      | `SELECT time, temperature FROM iot_telemetry`      |
| Battery by device            | Bar gauge        | `SELECT device_id, battery FROM iot_telemetry`     |
| Avg temperature by region    | Bar chart        | `SELECT region, AVG(temperature) FROM iot_telemetry GROUP BY region` |

---

## Troubleshooting

**Broker connection fails**

- Check `CLOUDAMQP_URL` in `.env`
- Verify network connectivity and TLS port (8883)

```bash
python scripts/test_broker_connection.py
```

**InfluxDB 401 Unauthorized**

- Regenerate API token
- Confirm `INFLUX3_ORG` and `INFLUX3_DATABASE` values

```bash
python scripts/test_influx_write.py
```

**Queue receives no messages**

- Confirm producer is running
- Verify queue name matches between producer and consumer
- Check CloudAMQP dashboard

---

## Workshop Agenda

Total duration: **2 hours**

| Time | Activity                 |
| ---- | ------------------------ |
| 0:00 | Architecture overview    |
| 0:15 | Broker test              |
| 0:30 | Single device simulation |
| 0:45 | Fleet simulation         |
| 1:00 | Ingestion service        |
| 1:20 | InfluxDB queries         |
| 1:40 | Grafana dashboards       |
| 2:00 | Q&A                      |

---

## Summary

This workshop demonstrates a scalable IoT telemetry pipeline using:

- Python device simulation
- Managed AMQP messaging
- Time-series storage
- Real-time dashboards

> Key concept: **Decoupled cloud ingestion using message queues**
