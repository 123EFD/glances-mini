"""FastAPI application providing REST endpoints and WebSocket live streaming."""

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from glances_mini.collector import SystemCollector
from glances_mini.web.schemas import SystemResponse, ProcessResponse

# Initialize FastAPI application
app = FastAPI(
    title="glances-mini API",
    description="Lightweight system contention diagnostic API and WebSocket stream",
    version="0.1.0",
)

# Enable CORS for React/Vite frontend (default port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton collector instance
collector = SystemCollector()


@app.get("/api/system", response_model=SystemResponse)
def get_system_metrics(limit: int = Query(default=10, ge=1, le=100)):
    """Fetch the latest snapshot of system health and top processes."""

    snapshot = collector.get_system_snapshot(limit=limit)
    return {
            "timestamp": snapshot.timestamp,
            "cpu_percent_total": snapshot.cpu_percent_total,
            "memory_percent": snapshot.memory_percent,
            "memory_used_bytes": snapshot.memory_used_bytes,
            "memory_total_bytes": snapshot.memory_total_bytes,
            "processes": [p.to_dict() for p in snapshot.processes],
            "is_congested": snapshot.is_congested(),
    }


@app.get("/api/processes", response_model=list[ProcessResponse])
def get_processes(
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="cpu", regex="^(cpu|memory)$"),
):
    """Fetch top N processes sorted by CPU or memory."""

    process_result = collector.get_processes(limit=limit, sort_by=sort_by)
    return [p.to_dict() for p in process_result]


@app.websocket("/ws/live")
async def live_metrics_stream(websocket: WebSocket):
    """Push real-time system snapshots to connected clients every second."""
    # 1. Accept client WebSocket connection
    await websocket.accept()
    try:
        while True:
            snapshot  = collector.get_system_snapshot(limit=10)
            payload = {
                "timestamp": snapshot.timestamp,
                "cpu_percent_total": snapshot.cpu_percent_total,
                "memory_percent": snapshot.memory_percent,
                "memory_used_bytes": snapshot.memory_used_bytes,
                "memory_total_bytes": snapshot.memory_total_bytes,
                "processes": [p.to_dict() for p in snapshot.processes],
                "is_congested": snapshot.is_congested(),
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        # Client closed tab / disconnected
        print("WebSocket client disconnected.")