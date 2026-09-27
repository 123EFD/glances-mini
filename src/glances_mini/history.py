"""In-memory rolling history buffer using collections.deque."""

from collections import deque
from typing import List, Dict, Any, Optional
from glances_mini.models import SystemSnapshot


class SystemHistoryBuffer:
    """Maintains a fixed-size rolling circular buffer of system snapshots.
    
    Default max_points=300 represents 5 minutes of data at 1-second intervals.
    """

    def __init__(self, max_points: int = 300) -> None:
        # collections.deque automatically drops oldest elements in O(1) time
        self.buffer: deque[SystemSnapshot] = deque(maxlen=max_points)

    def append(self, snapshot: SystemSnapshot) -> None:
        """Add a new snapshot. Oldest snapshot is automatically discarded if full."""
        self.buffer.append(snapshot)

    def get_latest(self) -> Optional[SystemSnapshot]:
        """Return the most recent snapshot without triggering a new OS scan."""
        return self.buffer[-1] if self.buffer else None
    

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return a timeline of past metrics for charting.
        
        Each item includes: timestamp, cpu_percent, memory_percent, is_congested.
        """
        items = list(self.buffer)
        if limit is not None:
            items = items[-limit:]
        return [
            {
                "timestamp": s.timestamp,
                "cpu_percent": s.cpu_percent_total,
                "memory_percent": s.memory_percent,
                "is_congested": s.is_congested(),
            }
            for s in items
        ]
