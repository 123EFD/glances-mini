"""System and process metrics collector using psutil."""

import time
from typing import List
import psutil

from glances_mini.models import ProcessSnapshot, SystemSnapshot

class SystemCollector:
    """Collects system metrics and per-process resource consumption."""

    def __init__(self) -> None:
        # Prime psutil CPU counters (first call always returns 0.0)
        psutil.cpu_percent(interval=None)

    def get_processes(self, limit: int = 10, sort_by: str = "cpu") -> List[ProcessSnapshot]:
        """Safely fetch running processes, filter out inactive ones, and sort top N.
        
        Args:
            limit: Maximum number of processes to return.
            sort_by: Metric to sort by ("cpu" or "memory").
        """
        snapshots: List[ProcessSnapshot] = []

        # Iterate over all running processes requesting only needed attributes
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "memory_info"]):
            try:
                info = proc.info

                # Safe fallback if attributes are None
                pid = info.get("pid")
                if not isinstance(pid, int):
                    continue
                name = info.get("name") or "Unknown"
                cpu = info.get("cpu_percent") or 0.0
                mem_percent = info.get("memory_percent") or 0.0
                
                mem_info = info.get("memory_info")
                rss_bytes = mem_info.rss if mem_info else 0

                # Optional: Fetch disk I/O safely if available
                disk_read_sec = 0.0
                disk_write_sec = 0.0
                try:
                    io = proc.io_counters()
                    if io:
                        disk_read_sec = float(io.read_bytes)
                        disk_write_sec = float(io.write_bytes)
                except (psutil.AccessDenied, AttributeError):
                    pass

                snapShot_instance = ProcessSnapshot(
                    pid=pid,
                    name=name,
                    cpu_percent=cpu,
                    memory_percent=mem_percent,
                    memory_rss_bytes=rss_bytes,
                    disk_read_bytes_sec=disk_read_sec,
                    disk_write_bytes_sec=disk_write_sec
                )
                snapshots.append(snapShot_instance)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process ended or system denied permission between iteration steps
                continue

        if sort_by == "cpu":
            snapshots = sorted(snapshots, key=lambda p: p.cpu_percent, reverse=True)[:limit]
        else:
            snapshots = sorted(snapshots, key=lambda p: p.memory_percent, reverse=True)[:limit]
        return snapshots

    def get_system_snapshot(self, limit: int = 10) -> SystemSnapshot:
        """Capture an instant snapshot of overall system health and top processes."""
        timestamp = time.time()
        
        # Total CPU usage since last call (non-blocking)
        cpu_total = psutil.cpu_percent(interval=None)

        # Virtual memory stats
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used = mem.used
        mem_total = mem.total

        processes = self.get_processes(limit=limit)
        return SystemSnapshot(
            timestamp=timestamp,
            cpu_percent_total=cpu_total,
            memory_percent=mem_percent,
            memory_used_bytes=mem_used,
            memory_total_bytes=mem_total,
            processes=processes,
        )