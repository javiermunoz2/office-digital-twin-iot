# Office digital twin: IoT environmental monitoring

A digital twin of an office floor. A custom ESP32 sensor node measures temperature, humidity, CO₂, gas/VOC and ambient noise. **ThingsBoard** receives the telemetry and raises alarms, and **n8n** automates storing the history in PostgreSQL. A web dashboard shows the live state of the building on a map and includes a **virtual assistant**, backed by an LLM, that answers questions about current and historical conditions.

> Built during my internship (Nov 2025 – Jan 2026). It covers the full stack: hardware and PCB design, firmware, IoT platform, data pipeline, frontend and LLM integration.

## Architecture

```
 ┌───────────────────────┐   HTTP /telemetry   ┌──────────────┐  alarms / REST API  ┌──────────────────────┐
 │ ESP32 sensor node     │ ──────────────────▶ │ ThingsBoard  │ ◀─────────────────▶ │ n8n workflows        │
 │ SCD41 · MQ-2 · INMP441│                     │ (IoT platform│                     │ · ingest → Postgres  │
 └───────────────────────┘                     │  + alarms)   │                     │ · dashboard webhook  │
 ┌───────────────────────┐   MQTT              └──────────────┘                     │ · chatbot webhook    │
 │ Python simulator      │ ──────────────────▶        ▲                             └──────────┬───────────┘
 │ (public dataset)      │                            │                                        │
 └───────────────────────┘                            │ REST (exporter ETL)          ┌─────────▼─────────┐
                                                      └────────────────────────────▶ │ PostgreSQL        │
 ┌──────────────────────────────────────────┐                                        │ 1-min readings +  │
 │ Web dashboard (Leaflet map, live KPIs,   │ ◀── n8n webhooks ── LLM assistant ◀─── │ 30-min / daily    │
 │ building alarm status, chat assistant)   │                    (Gemini, Qdrant)    │ aggregate views   │
 └──────────────────────────────────────────┘                                        └───────────────────┘
```

## Components

### 1. Hardware: ESP32 sensor node (`hardware/`, `firmware/`)

| Sensor | Measures | Interface |
|---|---|---|
| **SCD41** (Sensirion) | CO₂ (ppm), temperature, humidity | I²C (GPIO 21/22) |
| **MQ-2** | Gas / VOC (analog level) | ADC1, GPIO 34, through a 5 V → 3.3 V voltage divider |
| **INMP441** | Ambient noise (dB) | I²S (GPIO 14/15/32) |

- **Custom PCB** designed in KiCad (`hardware/pcb/`): a carrier board for the ESP32 with connectors for the three sensors, and Gerber and drill files ready for fabrication.
- **Firmware** (`firmware/main/`, Arduino/ESP32) with a modular structure: `sensores.*` for acquisition, `red.*` for Wi-Fi and HTTP, and `config.h` for configuration.
  - **Non-blocking main loop.** It uses `millis()` timers instead of `delay()`, so no sensor readings are lost while the node waits between transmissions.
  - **Noise level.** Computed from the I²S signal amplitude and converted to dB. Audio is never recorded.
  - **Gas filtering.** The gas reading is the average of 50 ADC samples, which filters out the noise induced by the Wi-Fi radio.
  - **Robust networking.** Automatic Wi-Fi reconnection, a 3-second HTTP timeout, and a JSON payload built in a static buffer (no `String`s, to avoid heap fragmentation).

### 2. IoT platform: ThingsBoard

The device sends telemetry to ThingsBoard's HTTP API. ThingsBoard stores the time series and evaluates **alarm rules**, for example high CO₂. Active alarms are shown on the dashboard.

### 3. Data pipeline and storage (`services/`, `database/`)

- **n8n** workflows:
  - Store one reading per minute in PostgreSQL.
  - Expose a webhook with the latest telemetry and alarms for the dashboard.
  - Expose a webhook for the chat assistant.
- **PostgreSQL schema** (`database/schema.sql`): a raw table `lecturas_sensores`, which is the ML-ready history, plus **30-minute** and **daily** aggregate views. The assistant uses these views to answer questions about recent and historical conditions without scanning the raw data.
- **Python services**, used in the first, simulated stage of the project:
  - `publisher`: replays the public UCI *Occupancy Detection* office dataset to ThingsBoard over MQTT, acting as a virtual sensor before the hardware existed.
  - `ingestor`: a debug subscriber that prints the MQTT messages it receives.
  - `exporter`: an ETL job that downloads 30 days of telemetry through the ThingsBoard REST API, aligns the variables by timestamp with pandas and loads them into PostgreSQL.
- `analysis/extraccion_datos.ipynb`: reads the history from PostgreSQL and converts timestamps from UTC to Europe/Madrid, as preparation for ML.

### 4. Frontend (`frontend/index.html`)

A single-page dashboard with a dark theme. It shows:
- A **Leaflet map** with the building's location.
- Live **KPI cards**: temperature, humidity, CO₂, VOC and noise, refreshed every 2 seconds.
- A **building status panel** that turns red when a ThingsBoard alarm is active.
- A **chat assistant** that answers in natural language using the stored data (an LLM called from n8n).

## Tech stack

`ESP32` · `Arduino C++` · `KiCad` · `ThingsBoard` · `MQTT (paho, Mosquitto)` · `n8n` · `PostgreSQL` · `Qdrant` · `Google Gemini` · `Python (pandas, SQLAlchemy, requests)` · `Docker Compose` · `HTML/CSS/JS + Leaflet`

## Running it

```bash
cp .env.example .env               # fill in your own passwords
docker compose up -d               # ThingsBoard :8080, n8n :6789, Postgres, Adminer, Qdrant
```

1. In ThingsBoard, create a device and copy its access token.
2. **Real sensor**: copy `firmware/main/config.example.h` to `config.h`, fill in your Wi-Fi details and the device token, and flash the board with the Arduino IDE. It needs the ESP32 core and the *SparkFun SCD4x Arduino Library*.
   **Simulated sensor**: run `services/publisher` with `MQTT_ACCESS_TOKEN` set.
3. Create the n8n workflows (ingestion, dashboard webhook `estado_oficina`, chat webhook `chat_oficina2`) and add the LLM API key as an **n8n credential**.
4. Open `frontend/index.html` in a browser.

## Repository structure

```
firmware/main/        ESP32 firmware (config.example.h → config.h)
hardware/pcb/         KiCad project + Gerber/drill files
services/             publisher (simulator), ingestor (debug), exporter (ETL)
database/schema.sql   PostgreSQL table + aggregate views
frontend/index.html   Dashboard + chat assistant
analysis/             Data extraction notebook
data/                 Public dataset used for simulation (see data/README.md)
docker-compose.yml    ThingsBoard, n8n, PostgreSQL, Adminer, Qdrant
```

## Author

Javier Muñoz Vera
