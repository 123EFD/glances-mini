"""FastAPI application providing REST endpoints and WebSocket live streaming."""

import asyncio
from contextlib import asynccontextmanager
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from glances_mini.collector import SystemCollector
from glances_mini.history import SystemHistoryBuffer
from glances_mini.web.schemas import SystemResponse, ProcessResponse
from glances_mini.incidents import IncidentManager
from glances_mini.web.metrics import generate_prometheus_metrics

collector = SystemCollector()
history_buffer = SystemHistoryBuffer(max_points=300)  # 5 minutes of history at 1-second intervals
incident_mgr = IncidentManager()

active_websockets: Set[WebSocket] = set()

async def background_metric_poller():
    """Continuously poll metrics every second without blocking the asyncio loop."""
    try:
        while True:
            # TODO 1: Run collector.get_system_snapshot in a background thread:
            snapshot = await asyncio.to_thread(collector.get_system_snapshot, limit=10)
            
            # TODO 2: Store in history buffer and check for incidents:
            history_buffer.append(snapshot)
            incident_mgr.check_and_record(snapshot)
            # TODO 3: Broadcast to all connected WebSocket clients:
            if active_websockets:
                payload = {
                    "timestamp": snapshot.timestamp,
                    "cpu_percent_total": snapshot.cpu_percent_total,
                    "memory_percent": snapshot.memory_percent,
                    "memory_used_bytes": snapshot.memory_used_bytes,
                    "memory_total_bytes": snapshot.memory_total_bytes,
                    "processes": [p.to_dict() for p in snapshot.processes],
                    "is_congested": snapshot.is_congested(),
                }
            # Send to all clients and drop disconnected ones
                for ws in list(active_websockets):
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        active_websockets.discard(ws)
            # Non-blocking 1-second tick
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        print("Background metric poller stopped cleanly.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager to start/stop background tasks."""
    # Start background metric poller
    poller_task = asyncio.create_task(background_metric_poller())
    yield
    # Stop background metric poller on shutdown
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass
    
# Initialize FastAPI application
app = FastAPI(
    title="glances-mini API",
    description="Lightweight system contention diagnostic API and WebSocket stream",
    version="0.1.0",
    lifespan=lifespan,
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

@app.get("/",response_class=HTMLResponse)
def index():
    """Serve the real-time diagnostic dashboard."""
    with open("src/glances_mini/web/dashboard.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/system", response_model=SystemResponse)
def get_system_metrics(limit: int = Query(default=10, ge=1, le=100)):
    """Fetch the latest snapshot of system health and top processes."""
    snapshot = history_buffer.get_latest()

    if snapshot is None:
        # If no snapshot is available, fetch one directly (blocking)
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

@app.get("/api/history")
def get_metrics_history(limit: int = Query(default=60, ge=1, le=300)):
    """Fetch historical metrics for charting."""
    history = history_buffer.get_history(limit=limit)
    return history

@app.get("/metrics")
def get_prometheus_metrics():
    """Expose metrics in Prometheus format."""
    snapshot = history_buffer.get_latest() or collector.get_system_snapshot(limit=10)
    content = generate_prometheus_metrics(snapshot)
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")

@app.websocket("/ws/live")
async def live_metrics_stream(websocket: WebSocket):
    """Push real-time system snapshots to connected clients every second."""
    # 1. Accept client WebSocket connection
    await websocket.accept()
    active_websockets.add(websocket)
    try:
        while True:
            # Keep the connection alive; actual data is pushed from background poller
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client closed tab / disconnected
        active_websockets.discard(websocket)
        
@app.get("/api/incidents")
def get_incidents(limit: int = 10):
    return incident_mgr.get_recent_incidents(limit=limit)