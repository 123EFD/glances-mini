"""Diagnostic Advisor: Analyzes system contention and suggests actionable solutions with reference links."""

from typing import List, Dict, Any
from glances_mini.models import SystemSnapshot, ProcessSnapshot


class DiagnosticSuggestion:
    """Actionable advice for resolving a specific resource contention issue."""

    def __init__(
        self,
        severity: str,       # "warning" or "critical"
        process_name: str,
        title: str,
        description: str,
        action: str,
        reference_url: str,
    ) -> None:
        self.severity = severity
        self.process_name = process_name
        self.title = title
        self.description = description
        self.action = action
        self.reference_url = reference_url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "process_name": self.process_name,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "reference_url": self.reference_url,
        }


# Knowledge base of known Windows bottleneck processes
KNOWLEDGE_BASE = {
    "onedrive": {
        "title": "OneDrive Sync Loop / High CPU",
        "description": "OneDrive is actively hashing, uploading, or stuck in a synchronization conflict.",
        "action": "Pause OneDrive syncing for 2 hours or check for files with conflicting sync statuses.",
        "reference_url": "https://support.microsoft.com/office/fix-onedrive-sync-problems-0899b115-05f7-45ec-95b2-e4cc8c4670b2",
    },
    "wmiprvse.exe": {
        "title": "WMI Provider Host CPU Spike",
        "description": "A background service or monitoring utility is bombarding the Windows WMI service with queries.",
        "action": "Open Event Viewer > Applications and Services > Microsoft > Windows > WMI-Activity to find the ClientProcessId issuing queries.",
        "reference_url": "https://learn.microsoft.com/troubleshoot/windows-client/system-management-components/high-cpu-usage-by-wmiprvse-process",
    },
    "memcompression": {
        "title": "Memory Compression Thrashing",
        "description": "System RAM is heavily congested. Windows is using CPU to compress inactive RAM pages to avoid paging to disk.",
        "action": "Close memory-heavy applications (e.g. idle browser tabs, Docker containers) to relieve RAM pressure.",
        "reference_url": "https://learn.microsoft.com/windows/win32/memory/virtual-memory",
    },
    "java.exe": {
        "title": "High JVM CPU/Memory Usage",
        "description": "A Java application (IDE, Gradle daemon, or local service) is executing garbage collection cycles or heavy compilation.",
        "action": "Run 'jps -v' in terminal to identify the daemon, or stop idle Gradle daemons via './gradlew --stop'.",
        "reference_url": "https://docs.oracle.com/en/java/",
    },
}


class DiagnosticAdvisor:
    """Analyzes snapshots and returns tailored recommendations."""

    def analyze(self, snapshot: SystemSnapshot) -> List[Dict[str, Any]]:
        """Inspect top processes and generate suggestions, ignoring System Idle Process."""
        suggestions: List[Dict[str, Any]] = []

        # 1. Filter out PID 0 (System Idle Process) and inactive processes
        active_processes = [
            p for p in snapshot.processes 
            if p.pid != 0 and p.name.lower() != "system idle process"
        ]

        # 2. Check each top process against our diagnostic knowledge base
        for p in active_processes[:5]:
            p_name_lower = p.name.lower()
            
            # Check for known patterns
            matched_key = None
            for key in KNOWLEDGE_BASE:
                if key in p_name_lower:
                    matched_key = key
                    break

            if matched_key and (p.cpu_percent > 30.0 or p.memory_percent > 10.0):
                kb_entry = KNOWLEDGE_BASE[matched_key]
                severity = "critical" if p.cpu_percent > 100.0 else "warning"
                
                suggestion = DiagnosticSuggestion(
                    severity=severity,
                    process_name=p.name,
                    title=f"{p.name}: {kb_entry['title']}",
                    description=kb_entry["description"],
                    action=kb_entry["action"],
                    reference_url=kb_entry["reference_url"],
                )
                suggestions.append(suggestion.to_dict())

        # 3. Generic advice for unknown high CPU processes
        if not suggestions:
            for p in active_processes[:3]:
                if p.cpu_percent > 80.0:
                    suggestions.append(
                        DiagnosticSuggestion(
                            severity="warning",
                            process_name=p.name,
                            title=f"High CPU Consumption ({p.cpu_percent:.1f}%) in {p.name}",
                            description=f"Process '{p.name}' (PID {p.pid}) is consuming extensive CPU cycles.",
                            action=f"Check if {p.name} is performing a background task or stuck in an infinite loop.",
                            reference_url="https://learn.microsoft.com/sysinternals/downloads/process-explorer",
                        ).to_dict()
                    )

        return suggestions