
---

# Cloud IoT Workshop

A hands-on workshop demonstrating a **cloud-based IoT telemetry pipeline** using managed services and Python-based device simulation.

The workshop simulates a fleet of IoT devices sending telemetry to a cloud message broker, which is then ingested into a time-series database and visualized using Grafana.

---

# Architecture Overview

The system architecture:

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

Pipeline flow:

```
Producer(s) → CloudAMQP Queue → Consumer → InfluxDB → Grafana
```

Each component has a clearly defined role:

| Component        | Role                                         |
| ---------------- | -------------------------------------------- |
| Python Producers | Simulated IoT devices sending telemetry      |
| CloudAMQP        | Managed message broker buffering device data |
| Python Consumer  | Reads queue messages and stores them         |
| InfluxDB 3       | Time-series database for telemetry           |
| Grafana          | Visualization dashboards                     |

---

# Project Structure

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

# Environment Setup

## 1 Install Python

Recommended:

```
Python 3.10+
```

Check version:

```bash
python --version
```

---

## 2 Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## 3 Install dependencies

```bash
pip install -r requirements.txt
```

Dependencies:

| Package          | Purpose                          |
| ---------------- | -------------------------------- |
| pika             | AMQP client for CloudAMQP        |
| influxdb3-python | InfluxDB client                  |
| python-dotenv    | Load environment variables       |
| pandas           | Used for query output formatting |

---

# Environment Configuration

Create a `.env` file from the template.

```bash
cp .env.example .env
```

Edit `.env`:

```
CLOUDAMQP_URL=amqps://USERNAME:PASSWORD@dog.lmq.cloudamqp.com/VHOST

INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=Dev
INFLUX3_DATABASE=room-monitoring
INFLUX3_TOKEN=YOUR_INFLUX_TOKEN
```

Required values:

| Variable         | Description                     |
| ---------------- | ------------------------------- |
| CLOUDAMQP_URL    | CloudAMQP broker connection URL |
| INFLUX3_HOST     | InfluxDB Cloud endpoint         |
| INFLUX3_ORG      | Influx organization             |
| INFLUX3_DATABASE | Database name                   |
| INFLUX3_TOKEN    | API token                       |

---

# Script Overview

## scripts/

### test_broker_connection.py

Purpose:

Test connectivity to CloudAMQP.

Steps performed:

1. connect to AMQP broker
2. declare queue
3. publish test message
4. close connection

Run:

```bash
python scripts/test_broker_connection.py
```

Expected output:

```
[OK] Queue declared
[OK] Test message published
```

---

### test_influx_write.py

Purpose:

Validate InfluxDB connectivity.

Functions:

* write sample points
* execute SQL query
* print query results

Run:

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

# Producer Scripts

Producer scripts simulate IoT devices sending telemetry.

Queue used:

```
iot_telemetry
```

---

## single_device_producer.py

Simulates one IoT device.

Telemetry example:

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

Run:

```bash
python producers/single_device_producer.py
```

---

## fleet_device_simulator.py

Simulates multiple devices concurrently.

Features:

* multiple device threads
* randomized telemetry
* random publish intervals

Run:

```bash
python producers/fleet_device_simulator.py
```

Default simulation:

```
20 devices
```

Example output:

```
[PUB] device-005 -> {...}
[PUB] device-012 -> {...}
```

---

# Consumer Scripts

Consumers read queue messages and process them.

---

## queue_message_logger.py

Simple debugging consumer.

Purpose:

Inspect raw messages in the queue.

Run:

```bash
python consumers/queue_message_logger.py
```

Output example:

```
[MSG] {"device_id":"device-001",...}
```

---

## minimal_amqp_to_influx.py

Minimal ingestion pipeline.

Workflow:

```
AMQP Queue → InfluxDB
```

Stores limited fields:

* device_id
* region
* temperature
* humidity

Run:

```bash
python consumers/minimal_amqp_to_influx.py
```

---

## amqp_to_influx_service.py

Full ingestion service used for the final workshop.

Workflow:

```
Queue message
    ↓
JSON decode
    ↓
InfluxDB Point
    ↓
Write to database
```

Stored fields:

| Tag         | Field         |
| ----------- | ------------- |
| device_id   | temperature   |
| region      | humidity      |
| device_type | soil_moisture |
|             | battery       |
|             | signal_rssi   |

Run:

```bash
python consumers/amqp_to_influx_service.py
```

Output:

```
[WRITE] device-004 -> InfluxDB
```

---

# Running the End-to-End Demo

Open two terminals.

---

## Terminal 1

Start ingestion service.

```bash
python consumers/amqp_to_influx_service.py
```

---

## Terminal 2

Start fleet simulator.

```bash
python producers/fleet_device_simulator.py
```

---

## Expected behavior

Producer output:

```
[PUB] device-003 -> {...}
```

Consumer output:

```
[WRITE] device-003 -> InfluxDB
```

CloudAMQP:

```
Queue activity visible
```

InfluxDB:

```
Rows increasing
```

---

# Querying Data in InfluxDB

Example SQL queries.

---

## Latest telemetry

```sql
SELECT *
FROM iot_telemetry
ORDER BY time DESC
LIMIT 20;
```

---

## Average temperature by region

```sql
SELECT
region,
AVG(temperature)
FROM iot_telemetry
GROUP BY region;
```

---

## Battery health

```sql
SELECT
device_id,
battery
FROM iot_telemetry
ORDER BY battery ASC
LIMIT 20;
```

---

# Grafana Dashboards

Recommended panels.

---

## Temperature over time

```
time series chart
```

Query:

```sql
SELECT time, temperature
FROM iot_telemetry
```

---

## Battery by device

```
bar gauge
```

Query:

```sql
SELECT device_id, battery
FROM iot_telemetry
```

---

## Average temperature by region

```
bar chart
```

Query:

```sql
SELECT region, AVG(temperature)
FROM iot_telemetry
GROUP BY region
```

---

# Troubleshooting

## Broker connection fails

Check:

* CLOUDAMQP_URL
* network connectivity
* TLS port

Test with:

```bash
python scripts/test_broker_connection.py
```

---

## Influx authentication error

Error example:

```
401 unauthorized
```

Solution:

* regenerate API token
* confirm org name
* verify database name

Test with:

```bash
python scripts/test_influx_write.py
```

---

## Queue receives no messages

Check:

* producer running
* queue name matches
* broker dashboard

---

# Workshop Agenda (Example)

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

# Summary

This workshop demonstrates a scalable IoT telemetry pipeline using:

* Python device simulation
* managed AMQP messaging
* time-series storage
* real-time dashboards

Key concept demonstrated:

```
Decoupled cloud ingestion using message queues
```

---