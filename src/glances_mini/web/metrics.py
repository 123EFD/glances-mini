"""Prometheus plain-text metric exposition generator."""

from glances_mini.models import SystemSnapshot


def generate_prometheus_metrics(snapshot: SystemSnapshot) -> str:
    """Generate Prometheus/OpenMetrics plain-text exposition format from a snapshot."""
    lines = [
        "# HELP glances_cpu_total_percent Current total system CPU utilization percentage",
        "# TYPE glances_cpu_total_percent gauge",
        f"glances_cpu_total_percent {snapshot.cpu_percent_total:.1f}",
        "",
        "# HELP glances_memory_percent Current system memory utilization percentage",
        "# TYPE glances_memory_percent gauge",
        f"glances_memory_percent {snapshot.memory_percent:.1f}",
        "",
        "# HELP glances_memory_used_bytes Memory used in bytes",
        "# TYPE glances_memory_used_bytes gauge",
        f"glances_memory_used_bytes {snapshot.memory_used_bytes}",
        "",
        "# HELP glances_process_cpu_percent Process CPU utilization percentage",
        "# TYPE glances_process_cpu_percent gauge",
    ]
    for process in snapshot.processes:
        lines.append(
            f'glances_process_cpu_percent{{pid="{process.pid}",name="{process.name}"}} {process.cpu_percent:.1f}'
        )

    lines.append("")  # Prometheus requires trailing newline
    
    return "\n".join(lines)
    