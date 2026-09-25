# Stage 3: DevOps & Observability for TypeScript Developers

A reference notebook covering Context Managers (`with`), File I/O & JSON Lines (`.jsonl`), the Prometheus metric exposition format, and Docker containerization for system diagnostic tools.

---

## 1. Context Managers (`with` statement vs `try...finally`)

In Node.js / TypeScript, managing resources (like file descriptors, database connections, locks) requires manual `try...finally` blocks to guarantee cleanup:

```typescript
// TypeScript / Node.js
const fd = fs.openSync("incidents.log", "a");
try {
  fs.writeSync(fd, "incident data\n");
} finally {
  fs.closeSync(fd);
}
```

In Python, the **`with` statement** provides automated setup and teardown:

```python
# Python
with open("incidents.log", "a", encoding="utf-8") as f:
    f.write("incident data\n")
# File is AUTOMATICALLY closed here, even if an exception was raised inside!
```

### How `with` Works Under the Hood:
Any object can be used with `with` if it implements two dunder methods:
- `__enter__(self)`: Called before entering the block (opens file, acquires lock).
- `__exit__(self, exc_type, exc_val, exc_tb)`: Called when exiting the block (closes file, releases lock, handles exceptions).

---

## 2. String Joining: `"\n".join(lines)` vs `lines.join('\n')`

A classic syntax surprise for TypeScript developers:

| Operation | TypeScript | Python |
| :--- | :--- | :--- |
| **Join array of strings** | `lines.join("\n")` | `"\n".join(lines)` |

In Python, `.join()` is a method on the **separator string**, not the list:
```python
lines = ["line1", "line2", "line3"]
output = "\n".join(lines)
```
*Why?* In Python, `lines` can be any iterable (a list, a tuple, a generator, a set). Placing `.join()` on `str` avoids having to implement it separately on every sequence type.

---

## 3. Incident Logging: Why JSON Lines (`.jsonl`)?

When storing diagnostic alerts or incident logs in DevOps, standard JSON arrays `[ { ... }, { ... } ]` have major flaws:
1. To append a new incident, you must read the entire file into memory, parse it, append, and rewrite the whole file.
2. If the application crashes mid-write, the closing bracket `]` is lost, corrupting the entire file.

**JSON Lines (`.jsonl`)** solves this:
- Every line is a standalone, valid JSON string separated by `\n`.
- New incidents are appended to the end of the file in $O(1)$ time with `"a"` mode.
- Can be processed line-by-line using streaming without loading gigabytes of logs into memory.

```python
import json

incident = {"timestamp": 1727220000, "cpu": 94.2, "top_process": "ffmpeg.exe"}

with open("incidents.jsonl", "a", encoding="utf-8") as f:
    f.write(json.dumps(incident) + "\n")
```

---

## 4. Prometheus Plain-Text Exposition Format

**Prometheus** is the cloud-native standard for metrics collection (Kubernetes, microservices). Instead of sending metrics to a server, Prometheus periodically **scrapes** an HTTP endpoint (conventionally `GET /metrics`).

### OpenMetrics / Prometheus Exposition Syntax:
```text
# HELP <metric_name> <Human-readable description>
# TYPE <metric_name> <gauge|counter|summary|histogram>
<metric_name>{<label_key>="<label_value>",...} <numeric_value>
```

### Metric Types:
1. **Gauge**: A value that can go up and down (e.g. CPU percentage, Memory in bytes, number of running processes).
2. **Counter**: A cumulative metric that only ever increases or resets to zero (e.g. total disk bytes read, total HTTP requests).

### Example for `glances-mini`:
```text
# HELP glances_cpu_total_percent Current total system CPU utilization percentage
# TYPE glances_cpu_total_percent gauge
glances_cpu_total_percent 14.5

# HELP glances_memory_percent Current system memory utilization percentage
# TYPE glances_memory_percent gauge
glances_memory_percent 62.1

# HELP glances_process_cpu_percent Process CPU utilization percentage
# TYPE glances_process_cpu_percent gauge
glances_process_cpu_percent{pid="1234",name="chrome.exe"} 18.2
glances_process_cpu_percent{pid="5678",name="python.exe"} 2.4
```

> **Take Notice: HTTP Content-Type**:
> The standard Content-Type for Prometheus plain-text metrics is:
> `text/plain; version=0.0.4; charset=utf-8`

---

## 5. Dockerizing System Diagnostic Tools (`--pid=host`)

Normally, Docker containers run in isolated Linux namespaces. Inside a standard container:
- `psutil.process_iter()` will **only see processes running inside that container** (often just PID 1).
- It cannot see the host operating system's Chrome, Slack, or Docker daemon.

To turn a Python diagnostic app into a host monitor:
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
EXPOSE 8000
CMD ["uvicorn", "glances_mini.web.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
```

When running in Linux / Docker environments:
```bash
docker run -d --net=host --pid=host glances-mini
```
- `--pid=host`: Shares the host machine's process table with the container so `psutil` can inspect all host processes!
