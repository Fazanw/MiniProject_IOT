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
    └── amqp_to_influx3.py
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

> **Note:** `.env` and `wokwi/secrets.h` are gitignored and never committed. You must create them locally before running anything.

### Python scripts — `.env`

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
CLOUDAMQP_URL=amqps://USERNAME:PASSWORD@your-broker.lmq.cloudamqp.com/VHOST

INFLUX3_HOST=https://us-east-1-1.aws.cloud2.influxdata.com
INFLUX3_ORG=your_org
INFLUX3_DATABASE=your_database
INFLUX3_TOKEN=your_influx_token
```

| Variable         | Description                     |
| ---------------- | ------------------------------- |
| CLOUDAMQP_URL    | CloudAMQP broker connection URL |
| INFLUX3_HOST     | InfluxDB Cloud endpoint         |
| INFLUX3_ORG      | Influx organization             |
| INFLUX3_DATABASE | Database name                   |
| INFLUX3_TOKEN    | API token                       |

### Arduino / Wokwi — `wokwi/secrets.h`

Copy the template and fill in your MQTT credentials:

```bash
cp wokwi/secrets.h.example wokwi/secrets.h
```

Then edit `wokwi/secrets.h`:

```cpp
#define MQTT_SERVER "your-broker.lmq.cloudamqp.com"
#define MQTT_PORT   8883
#define MQTT_USER   "your_user:your_vhost"
#define MQTT_PASS   "your_mqtt_password"
#define MQTT_TOPIC  "energy/telemetry"
```

| Variable    | Description                        |
| ----------- | ---------------------------------- |
| MQTT_SERVER | CloudAMQP broker hostname          |
| MQTT_PORT   | TLS port (8883)                    |
| MQTT_USER   | CloudAMQP username:vhost           |
| MQTT_PASS   | CloudAMQP password                 |
| MQTT_TOPIC  | MQTT topic to publish telemetry to |

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

Producer scripts simulate energy meters publishing telemetry to the `energy_telemetry` queue.

### `single_device_producer.py`

Simulates a single energy meter (`meter-001`) with static electrical values.

```bash
python producers/single_device_producer.py
```

Example payload:

```json
{
  "device_id": "meter-001",
  "voltage": 220.5,
  "current": 2.1,
  "power": 463.05,
  "energy": 15.6,
  "power_factor": 0.94,
  "frequency": 50.0,
  "device_type": "industrial_monitor"
}
```

Example output:

```
[PUB] meter-001 -> 220.5V, 2.1A, 463.05W
```

### `fleet_device_simulator.py`

Simulates **5 meters** concurrently with randomized electrical telemetry every 5 seconds.

```bash
python producers/fleet_device_simulator.py
```

Example output:

```
[PUB] meter-001 -> 224.3V, 3.12A, 699.82W
[PUB] meter-002 -> 218.7V, 7.45A, 1629.32W
```

---

## Consumer Scripts

### `queue_message_logger.py`

Debugging consumer — prints voltage and current from each incoming message.

```bash
python consumers/queue_message_logger.py
```

Example output:

```
[MSG] Received Telemetry from meter-001
      Voltage: 224.3V | Current: 3.12A
------------------------------
```

### `minimal_amqp_to_influx.py`

Minimal ingestion pipeline. Reads `voltage` and `current`, calculates `power` (`P = V × I`), and writes to InfluxDB.

```bash
python consumers/minimal_amqp_to_influx.py
```

Stored fields:

| Tag       | Field   |
| --------- | ------- |
| device_id | voltage |
|           | current |
|           | power   |

Example output:

```
[WRITE] meter-001 -> 224.3V, 3.12A, 699.82W
```

### `amqp_to_influx3.py`

Full ingestion service. Validates and transforms all electrical fields, then writes to InfluxDB.

- Validates and transforms incoming telemetry
- Stores measurements in the time-series database
- Acts as the data pipeline entry point

Workflow:

```
Queue message → JSON decode → validate fields → InfluxDB Point → Write to database
```

**Electrical Telemetry Data:**

| Field        | Description                        |
| ------------ | ---------------------------------- |
| device_id    | Unique meter identifier (tag)      |
| device_type  | Meter category (tag)               |
| voltage      | Electrical voltage (V)             |
| current      | Electrical current (A)             |
| power        | Active power consumption (W)       |
| energy       | Accumulated energy usage (kWh)     |
| power_factor | Efficiency of electrical load      |
| frequency    | Grid frequency (Hz)                |

**Power calculation** — if `power` is not present in the message, it is derived as:

```
P = V × I
```

| Tag         | Field        |
| ----------- | ------------ |
| device_id   | voltage      |
| device_type | current      |
|             | power        |
|             | energy       |
|             | power_factor |
|             | frequency    |

```bash
python consumers/amqp_to_influx3.py
```

Example output:

```
[INGEST] meter-001: 224.3V, 3.12A, 699.82W, 45.6kWh, PF=0.95, 50.0Hz
```

---

## Running the End-to-End Demo

Open two terminals.

**Terminal 1** — start the ingestion service:

```bash
python consumers/amqp_to_influx3.py
```

**Terminal 2** — start the fleet simulator:

```bash
python producers/fleet_device_simulator.py
```

Expected behavior:

| Component | Output                                                    |
| --------- | --------------------------------------------------------- |
| Producer  | `[PUB] meter-003 -> 221.4V, 4.5A, 996.3W`                |
| Consumer  | `[INGEST] meter-003: 221.4V, 4.5A, 996.3W, ...`          |
| CloudAMQP | Queue activity visible                                    |
| InfluxDB  | Row count increasing in `energy_telemetry` measurement    |

---

## Querying Data in InfluxDB

**Latest telemetry:**

```sql
SELECT *
FROM energy_telemetry
ORDER BY time DESC
LIMIT 20;
```

**Average power consumption:**

```sql
SELECT AVG(power)
FROM energy_telemetry;
```

**Energy consumption by device:**

```sql
SELECT device_id, SUM(energy)
FROM energy_telemetry
GROUP BY device_id;
```

**Voltage stability monitoring:**

```sql
SELECT time, device_id, voltage
FROM energy_telemetry
ORDER BY time DESC
LIMIT 20;
```

---

## Grafana Dashboards

| Panel                     | Type        | Query                                                        |
| ------------------------- | ----------- | ------------------------------------------------------------ |
| Power consumption over time | Time series | `SELECT time, power FROM energy_telemetry`                 |
| Voltage monitoring        | Time series | `SELECT time, voltage FROM energy_telemetry`                 |
| Current load monitoring   | Time series | `SELECT time, current FROM energy_telemetry`                 |
| Energy usage per device   | Bar gauge   | `SELECT device_id, SUM(energy) FROM energy_telemetry GROUP BY device_id` |
| Power factor efficiency   | Stat panel  | `SELECT device_id, power_factor FROM energy_telemetry`       |
| Frequency stability       | Time series | `SELECT time, frequency FROM energy_telemetry`               |

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
