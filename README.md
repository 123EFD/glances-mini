# glances-mini 🔍

A lightweight, real-time system contention diagnostic tool built in Python. Designed to identify lag spikes, memory hogs, and resource contention without the overhead of heavy monitoring databases.

Built as part of a 4-stage hands-on Python roadmap for TypeScript developers.

---

## 🚀 Features

- **Resource Contention Focus**: Monitors CPU%, Memory%, and per-process I/O (Disk + Network) where system freezes actually happen.
- **Root-Cause Incident Log**: Automatically snapshots culprit processes whenever CPU or memory crosses a contention threshold (e.g. >85%).
- **Live Streaming**: Real-time push over WebSockets using FastAPI.
- **DevOps Ready**: Plain-text Prometheus `/metrics` exposition format.
- **In-Memory History**: Circular buffer (`collections.deque`) maintaining historical timelines without database complexity.

---

## 🛠️ Tech Stack

- **Language**: Python 3.13+
- **Metrics Collection**: `psutil`
- **Web Framework**: FastAPI, Uvicorn (ASGI)
- **Validation & Serialization**: Pydantic v2
- **Terminal UI**: Rich
- **Frontend** *(Stage 4)*: React, TypeScript, Vite

---

## 📦 Getting Started

### 1. Setup Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Diagnostics (Stage 1 Core)
```powershell
python -c "from glances_mini.collector import SystemCollector; c = SystemCollector(); print(c.get_system_snapshot())"
```

---

## 📚 Learning Notes

For TypeScript developers transitioning to Python, detailed concept comparisons and gotchas are documented in the `notes/` folder:
- [Stage 1: Python Fundamentals for TS Developers](notes/stage_1_fundamentals.md)
- [Stage 2: Web Layer & Streaming (FastAPI, Pydantic, WebSockets)](notes/stage_2_web_layer.md)
