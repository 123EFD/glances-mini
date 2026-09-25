"""Data models for system and process snapshots."""

import json
from typing import Any, Dict

class ProcessSnapshot:
    """Represents a point-in-time snapshot of a single running OS process."""

    def __init__(
        self,
        pid: int,
        name: str,
        cpu_percent: float,
        memory_percent: float,
        memory_rss_bytes: int,
        disk_read_bytes_sec: float = 0.0,
        disk_write_bytes_sec: float = 0.0,
    ) -> None:
        self.pid = pid
        self.name = name
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.memory_rss_bytes = memory_rss_bytes
        self.disk_read_bytes_sec = disk_read_bytes_sec
        self.disk_write_bytes_sec = disk_write_bytes_sec

    def __repr__(self) -> str:

        return f"ProcessSnapshot(pid={self.pid}, name='{self.name}', cpu={self.cpu_percent}%, mem={self.memory_percent}%)"

    def __lt__(self, other: "ProcessSnapshot") -> bool:

        return self.cpu_percent < other.cpu_percent

    def to_dict(self) -> Dict[str, Any]:
        """Convert the snapshot into a plain dictionary (for JSON serialization later)."""
        return {
            "pid": self.pid,
            "name": self.name,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "memory_rss_bytes": self.memory_rss_bytes,
            "disk_read_bytes_sec": self.disk_read_bytes_sec,
            "disk_write_bytes_sec": self.disk_write_bytes_sec,
        }

class SystemSnapshot:
    """Represents overall system CPU, Memory, and top processes."""

    def __init__(
        self,
        timestamp: float,
        cpu_percent_total: float,
        memory_percent: float,
        memory_used_bytes: int,
        memory_total_bytes: int,
        processes: list[ProcessSnapshot],
    ) -> None:
        self.timestamp = timestamp
        self.cpu_percent_total = cpu_percent_total
        self.memory_percent = memory_percent
        self.memory_used_bytes = memory_used_bytes
        self.memory_total_bytes = memory_total_bytes
        self.processes = processes

    def is_congested(self, threshold: float = 85.0) -> bool:
        """Check if CPU or Memory usage exceeds the contention threshold."""
        return self.cpu_percent_total > threshold or self.memory_percent > threshold