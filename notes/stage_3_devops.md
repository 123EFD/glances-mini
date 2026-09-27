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

---

## 6. Python Idioms: Slicing, Comprehensions, and Serialization

### 6.1 Brackets `[...]` in List Comprehensions
- **Square Brackets `[...]`**: Instructs Python to evaluate the loop immediately and return a populated in-memory `list` (array).
  ```python
  top_5 = [p.to_dict() for p in snapshot.processes[:5]]
  ```
- **Round Parentheses `(...)`**: Creates a **Generator Expression** (lazy iterator). It does not compute values until iterated over (like a JS generator function `function*`).
- **Curly Braces `{...}`**: Creates a `set` or a `dict`.

### 6.2 Advanced Slicing: `sequence[start : stop : step]`
Slicing is Python's native equivalent of `.slice()` in JavaScript, but with support for step direction and negative indices:

| Slice Syntax | Meaning | TypeScript Equivalent | Example on `[0, 1, 2, 3, 4, 5]` |
| :--- | :--- | :--- | :--- |
| `arr[:5]` | First 5 items (from start to index 5) | `arr.slice(0, 5)` | `[0, 1, 2, 3, 4]` |
| `arr[-5:]` | Last 5 items (from 5 from end to end) | `arr.slice(-5)` | `[1, 2, 3, 4, 5]` |
| `arr[::-1]` | Reverse entire sequence | `[...arr].reverse()` | `[5, 4, 3, 2, 1, 0]` |
| `arr[-3:][::-1]` | Last 3 items, in reverse order | `arr.slice(-3).reverse()` | `[5, 4, 3]` |

- **Why negative index for `max_history`?**
  `self.incidents[-self.max_history:]` keeps only the newest $N$ items and drops the oldest, implementing an in-memory sliding window / ring buffer. If the list has fewer items than `max_history`, Python safely returns all items without an error.
- **Single colon `:` vs Double colon `::`**:
  - `start:stop` uses a single colon (e.g. `[-limit:]`).
  - When `stop` is omitted and you want to specify `step`, a second colon is used (e.g. `[::-1]` sets `step=-1`).

### 6.3 Why `json.dumps()` in Files vs No `json.dumps()` in FastAPI?
- **In FastAPI endpoints**: FastAPI has an internal JSON encoder. When you `return {"status": "ok"}`, FastAPI automatically runs `json.dumps()` under the hood before sending the HTTP response.
- **In File I/O (`open()`)**: Python's `file.write()` only accepts raw strings (`str`) or bytes (`bytes`). Passing a `dict` raises `TypeError`. You must explicitly call `json.dumps(dict_data)` to convert it to a string.

### 6.4 Why Append Mode (`"a"`) and `\n`?
- Mode `"w"` wipes/truncates the file every time it is opened.
- Mode `"a"` moves to the end of the file so previous incidents are preserved.
- `f.write()` does **not** insert newlines automatically. Adding `"\n"` guarantees that every incident occupies exactly one line, producing a valid JSON Lines (`.jsonl`) file.

