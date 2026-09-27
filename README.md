# glances-mini 🔍

A lightweight, real-time system contention diagnostic tool built in Python. Designed to identify lag spikes, memory hogs, and resource contention without the overhead of heavy monitoring databases.

Built as a hands-on, 4-stage Python mastery project for TypeScript developers.

---

## 🚀 Features

- **Resource Contention Focus**: Monitors CPU%, Memory%, and per-process I/O (Disk + Network) where system freezes actually happen.
- **Root-Cause Incident Log**: Automatically snapshots culprit processes whenever CPU or memory crosses a contention threshold (e.g. >85%).
- **Live Streaming**: Real-time push over WebSockets using FastAPI broadcast pattern.
- **DevOps Ready**: Plain-text Prometheus `/metrics` exposition format.
- **In-Memory History**: Circular ring buffer (`collections.deque`) maintaining historical timelines without database complexity.
- **Instant Browser Dashboard**: Dark-mode UI with live animated gauges, 60s historical canvas sparkline, and real-time process table.

---

## 🏗️ Architecture & Component Flow

```mermaid
flowchart TD
    subgraph Host System
        PS[psutil OS C Calls]
    end

    subgraph "Core Engine (Background Task)"
        POL[asyncio Poller Loop\n1-second tick] -->|asyncio.to_thread| PS
        POL -->|Produce Snapshot| SNAP[SystemSnapshot & ProcessSnapshot]
        SNAP -->|O(1) Append| RING[SystemHistoryBuffer\ndeque maxlen=300]
        SNAP -->|Threshold Check >85%| INC[IncidentManager]
        INC -->|with open 'a'| DISK[(incidents.jsonl)]
    end

    subgraph "FastAPI Server"
        POL -->|Broadcast Frame| WS["/ws/live"]
        RING -->|Read Latest (0ms)| REST_SYS["GET /api/system"]
        RING -->|Read Timeline| REST_HIST["GET /api/history"]
        INC -->|Read Reverse Log| REST_INC["GET /api/incidents"]
        RING -->|Generate Gauges| PROM["GET /metrics"]
        UI_ROUTE["GET /"] --> DASH["dashboard.html"]
    end

    subgraph "Clients"
        DASH <-->|WebSocket Stream| WS
        DASH -->|Fetch History & Incidents| REST_HIST
        PROM_CLIENT[Prometheus / Grafana] --> PROM
    end
```

---

## 🗺️ Project Roadmap & Deliverables

| Stage | Focus Area | Status | Deliverables | Key Concepts Learned |
| :--- | :--- | :---: | :--- | :--- |
| **Stage 1** | **Fundamentals & Core Engine** | ✅ Completed | `models.py`, `collector.py` | Virtual environments (`venv`), type hints, OOP dunder methods (`__init__`, `__repr__`, `__lt__`), list comprehensions vs `.map()/.filter()`, safe `psutil` process handling. |
| **Stage 2** | **Web & Streaming Layer** | ✅ Completed | `web/schemas.py`, `web/app.py` | FastAPI routing with `@app` decorators, Pydantic v2 schemas vs Zod, async coroutines vs JS Promises, WebSocket streaming (`/ws/live`), Uvicorn `--app-dir src`. |
| **Stage 3** | **DevOps & Observability** | ✅ Completed | `incidents.py`, `web/metrics.py`, `Dockerfile` | Context managers (`with open`), JSON Lines (`.jsonl`), OpenMetrics / Prometheus exposition format (`/metrics`), container process table inspection (`--pid=host`). |
| **Stage 4** | **Advanced Concurrency & Frontend** | ✅ Completed | `history.py`, `web/dashboard.html` | Ring buffer with `collections.deque(maxlen=300)`, non-blocking thread offloading with `asyncio.to_thread()`, FastAPI `lifespan` context manager, single-producer multi-consumer WebSocket broadcast, live Tailwind + Canvas dashboard. |

---

## 📁 Project Structure

```
glances-mini/
├── .venv/                      # Python virtual environment
├── Dockerfile                  # Container build with host process visibility
├── README.md                   # Project overview & walkthrough
├── requirement.txt             # Installed dependencies
├── notes/                      # Learning notebooks for TypeScript developers
│   ├── stage_1_fundamentals.md # TS vs Python syntax, comprehensions, dunders, venv
│   ├── stage_2_web_layer.md    # FastAPI vs Express, Pydantic vs Zod, WebSockets
│   ├── stage_3_devops.md       # Context managers, JSONL, Prometheus formats, slicing
│   └── stage_4_advanced.md     # Ring buffers (deque), asyncio.to_thread, lifespan, generics
└── src/
    └── glances_mini/
        ├── __init__.py
        ├── models.py           # ProcessSnapshot & SystemSnapshot with dunders
        ├── collector.py        # psutil OS metrics collector with exception safety
        ├── incidents.py        # IncidentRecord & IncidentManager (>85% congestion)
        ├── history.py          # SystemHistoryBuffer (deque ring buffer)
        └── web/
            ├── __init__.py
            ├── schemas.py       # Pydantic v2 schemas for REST validation
            ├── metrics.py       # Prometheus plain-text exposition formatter
            ├── dashboard.html   # Standalone dark-mode dashboard (Canvas + Tailwind)
            └── app.py           # FastAPI app, lifespan, background worker, WS broadcast
```

---

## 📦 Getting Started

### 1. Setup Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirement.txt
python -m pip install "fastapi[standard]" pydantic uvicorn
```

### 2. Launch the Application
```powershell
uvicorn glances_mini.web.app:app --app-dir src --reload --port 8001
```

### 3. Verification & Live Endpoints
- **Interactive UI Dashboard**: Open `http://127.0.0.1:8001/`
  - Real-time CPU & Memory animated gauges.
  - 60-second historical canvas sparkline showing past lag spikes.
  - Live process table updating via WebSocket broadcast.
- **Interactive API Documentation**: Open `http://127.0.0.1:8001/docs`
  - `GET /api/system`: 0ms latency snapshot served directly from RAM.
  - `GET /api/processes?limit=10&sort_by=cpu`: Top processes.
  - `GET /api/history?limit=60`: Rolling 60-second timeline.
  - `GET /api/incidents`: Audit log of past resource spikes.
- **Prometheus Metric Scraper**:
  ```powershell
  curl http://127.0.0.1:8001/metrics
  ```
- **Incident Audit Trail**: Check `incidents.jsonl` in your root directory.

---

## 📚 TypeScript to Python Learning Library

For TypeScript developers transitioning to Python, detailed concept comparisons, memory models, and gotchas are documented in the `notes/` directory:
- [Stage 1: Python Fundamentals for TS Developers](notes/stage_1_fundamentals.md)
- [Stage 2: Web Layer & Streaming (FastAPI, Pydantic, WebSockets)](notes/stage_2_web_layer.md)
- [Stage 3: DevOps & Observability (Context Managers, JSONL, Prometheus)](notes/stage_3_devops.md)
- [Stage 4: Advanced Concurrency & Historical Buffers](notes/stage_4_advanced.md)
