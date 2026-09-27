"""Incident detection and persistent logging using context managers."""

import json
import time
from typing import List, Dict, Any, Optional
from glances_mini.models import SystemSnapshot, ProcessSnapshot


class IncidentRecord:
    """Represents a captured high-contention incident."""

    def __init__(
        self,
        timestamp: float,
        cpu_percent: float,
        memory_percent: float,
        top_processes: List[Dict[str, Any]],
    ) -> None:
        self.timestamp = timestamp
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.top_processes = top_processes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "top_processes": self.top_processes,
        }


class IncidentManager:
    """Detects system contention spikes and logs them to memory and disk."""

    def __init__(self, log_path: str = "incidents.jsonl", max_history: int = 50) -> None:
        self.log_path = log_path
        self.max_history = max_history
        self.incidents: List[IncidentRecord] = []
        self._last_logged_time: float = 0.0
        self._cooldown_seconds: float = 5.0  # Prevent spamming 1 log per second

    def check_and_record(self, snapshot: SystemSnapshot) -> Optional[IncidentRecord]:
        """Check if snapshot is congested (>85%) and record an incident with cooldown."""
        now = time.time()
        if(snapshot.is_congested() and (now - self._last_logged_time >= self._cooldown_seconds)):
            top_processes = [p.to_dict() for p in snapshot.processes[:5]]
            incident = IncidentRecord(
                timestamp=now,
                cpu_percent=snapshot.cpu_percent_total,
                memory_percent=snapshot.memory_percent,
                top_processes=top_processes
            )
            self.incidents.append(incident)
            self.incidents = self.incidents[-self.max_history:]
            self._write_to_disk(incident)
            self._last_logged_time = now
            return incident
        return None


    def _write_to_disk(self, incident: IncidentRecord) -> None:
        """Append the incident as a JSON string to the .jsonl file using a context manager."""
        json_line = json.dumps(incident.to_dict())
        with open(self.log_path, "a") as f:
            f.write(json_line + "\n")

    def get_recent_incidents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return the most recent recorded incidents."""
        return [incident.to_dict() for incident in self.incidents[-limit:]][::-1]