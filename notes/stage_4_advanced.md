# Stage 4: Advanced Concurrency & Historical In-Memory Buffers

A reference notebook covering `collections.deque` (Ring Buffers), `asyncio.to_thread` for non-blocking OS metrics, FastAPI Lifespan context managers, background task cancellation, and WebSocket broadcast streaming.

---

## 1. Data Structure: `collections.deque` vs `list` (The Ring Buffer)

When maintaining a rolling window of metrics (e.g. the last 5 minutes of 1-second ticks = 300 data points), using a standard list has significant performance drawbacks.

| Operation | Python `list` (or JS Array) | `collections.deque(maxlen=N)` |
| :--- | :--- | :--- |
| **Append to end** | $O(1)$ amortized | $O(1)$ |
| **Pop / Discard oldest from front** | $O(N)$ *(shifts all elements left)* | $O(1)$ *(drops head pointer in C)* |
| **Enforcing Max Capacity** | Manual slicing: `arr = arr[-N:]` ($O(N)$ memory copy) | **Automatic & Silent** ($O(1)$) |
| **Internal Architecture** | Dynamic array (contiguous memory) | Doubly-linked list of 64-element blocks in C |

### Example:
```python
from collections import deque

# Create a circular ring buffer capped at 5 items
buffer = deque(maxlen=5)

for i in range(7):
    buffer.append(i)

print(list(buffer))  # Output: [2, 3, 4, 5, 6] -> Oldest items 0 and 1 were automatically dropped!
```

---

## 2. The Blocking I/O Trap in Async Python (`asyncio.to_thread`)

### The Node.js vs Python Difference:
- In Node.js, `libuv` automatically pushes filesystem and system lookups to a C++ background thread pool. Your JavaScript code never halts the event loop unless you run heavy synchronous CPU math.
- In Python, `psutil` functions (`psutil.cpu_percent()`, scanning all system processes, reading disk I/O) are **synchronous blocking C calls**. Scanning 300 processes can take 50ms – 150ms.

> **CRITICAL GOTCHA**:
> If you call `collector.get_system_snapshot()` directly inside an `async def` route or WebSocket loop, the **entire asyncio event loop freezes for 100ms**! During those 100ms, no other HTTP requests or WebSocket messages can be processed.

### The Solution: `asyncio.to_thread()`
Python 3.9+ provides `asyncio.to_thread()` to run blocking synchronous functions in a background worker thread:

```python
import asyncio

# Non-blocking execution!
snapshot = await asyncio.to_thread(collector.get_system_snapshot, limit=10)
```
While `psutil` scans the OS in a background thread, the main asyncio event loop remains free to serve WebSocket clients and HTTP requests without latency spikes.

---

## 3. Background Tasks & Lifespan in FastAPI

In Node.js / Express, background intervals are started globally with `setInterval()`.
In modern FastAPI, background services are managed via the **Lifespan Context Manager** (`@asynccontextmanager`).

### Why Lifespan?
It cleanly ties background services to the server's lifecycle:
1. **Startup**: Spawns the background worker task before accepting traffic.
2. **Shutdown**: Gracefully cancels the task when the server terminates (`Ctrl+C`), preventing zombie loops or dangling file handles.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("Starting background metric poller...")
    task = asyncio.create_task(background_poller())
    
    yield  # Application runs and handles traffic here
    
    # --- SHUTDOWN ---
    print("Stopping background metric poller...")
    task.cancel()  # Signal the background loop to stop
    try:
        await task
    except asyncio.CancelledError:
        print("Poller task successfully canceled.")

app = FastAPI(lifespan=lifespan)
```

---

## 4. Canceling Async Tasks & `asyncio.CancelledError`

In TypeScript, you cancel a timer with `clearInterval(timerId)`.
In Python, async loops are usually structured as:

```python
async def background_poller():
    try:
        while True:
            # Gather metrics
            await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        # Cleanup when task.cancel() is called
        print("Cleaning up poller resources...")
```

When `task.cancel()` is called:
1. Python injects an `asyncio.CancelledError` exception directly at the line where the task is currently awaiting (usually `await asyncio.sleep(1.0)`).
2. The `except asyncio.CancelledError:` block catches it, allowing you to run cleanup before exiting.

---

## 5. WebSocket Broadcast Pattern

Instead of having every connected WebSocket client independently query `psutil` (which would overwhelm the CPU if 10 tabs are open), Stage 4 uses the **Single-Producer, Multi-Consumer Pattern**:
1. **One background task** polls `psutil` every 1 second and appends the snapshot to the shared `deque` ring buffer.
2. The background task **broadcasts** that single snapshot to all connected WebSocket clients simultaneously.
3. If no clients are connected, the background task still records history and incidents without wasted work.

---

## 6. Python Gotcha: "Function must return value on all code paths"

In TypeScript:
```typescript
function getHistory(limit?: number): Item[] {
  let items = [...buffer];
  if (limit !== undefined) {
    items = items.slice(-limit);
    return items.map(...); // ⚠️ TS Error: Not all code paths return a value!
  }
}
```

In Python:
```python
def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    items = list(self.buffer)
    if limit is not None:
        items = items[-limit:]
        return [...] # ⚠️ Indented inside 'if'!
```

### Why this happens:
1. When `limit is None` (the default!), the `if` block is skipped.
2. The execution reaches the end of the function without hitting a `return` statement.
3. In Python, reaching the end of a function without an explicit `return` implicitly returns **`None`**.
4. The type checker (Pylance/mypy) detects that `None` can be returned, violating the declared return type `List[Dict[str, Any]]`.

### The Fix:
Unindent the `return` statement so only the slice `items = items[-limit:]` is conditional, while the `return` runs unconditionally on all code paths:
```python
def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
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
```

---

## 7. Generics Syntax: Why Square Brackets `Set[...]` instead of `<...>`?

In TypeScript:
```typescript
const activeWebsockets: Set<WebSocket> = new Set();
const userMap: Map<string, number> = new Map();
const items: Array<string> = [];
```

In Python:
```python
active_websockets: Set[WebSocket] = set()
# Or in modern Python 3.9+:
active_websockets: set[WebSocket] = set()
user_map: dict[str, int] = {}
items: list[str] = []
```

### Why Python uses `[...]` instead of `<...>`:
1. **Avoiding Grammar Ambiguities**: In Python's syntax, `<` and `>` are reserved strictly for comparison operators (less-than and greater-than). Using `<` and `>` for types would cause severe parsing ambiguities with chained comparisons like `a < b > c`.
2. **Dunder Method Hook (`__class_getitem__`)**: In Python, generics are implemented at runtime using square brackets `[]`. When you write `set[WebSocket]`, Python invokes the class dunder method `set.__class_getitem__(WebSocket)`.
3. **Consistency**: In Python, all indexing, slicing, and type parameterization share the unified `[...]` bracket syntax.

---

## 8. Python Project Hygiene & Windows System Diagnostics

### 8.1 What to `.gitignore`: `__pycache__` and `*.jsonl`
- **`__pycache__/` and `*.pyc`**: In Node.js/TypeScript, you never commit `/dist`, `.tsbuildinfo`, or `node_modules/.cache`. Similarly, `.pyc` files are Python's pre-compiled bytecode caches. They are machine-specific and Python-version specific. Committing them clutters Git with binary diffs.
- **`*.jsonl` / `*.log`**: Runtime data and audit logs generated on your local machine should never be committed to source control.

### 8.2 Windows Multi-Core CPU Quirk: `System Idle Process`
In your process list, you may see:
```text
PID 0 | System Idle Process | 923.7% CPU
```
**Why CPU% is over 100% and what PID 0 means:**
1. **Multi-core scaling**: In `psutil`, CPU usage per process is calculated across all logical CPU cores. If your CPU has 10 cores, total capacity is $1000\%$.
2. **System Idle Process**: On Windows, PID 0 represents the kernel thread that executes when **no other thread is scheduled to run**.
3. **923.7% Idle means the CPU is doing NOTHING!** The machine is actually ~92% idle and relaxed. A diagnostic tool must filter out PID 0 or treat it as idle capacity, not a resource hog!

---

## 9. The `while True:` Pattern in Python & Async Architectures

### 9.1 Why `while True:` instead of `while condition is not None`?
- **In TypeScript / Node.js**: You use `setInterval(fn, 1000)` to execute recurring work indefinitely.
- **In Python `asyncio`**: The combination of `while True:` and `await asyncio.sleep(1.0)` is the **canonical equivalent of `setInterval()`**.

```python
async def poller():
    while True:
        await fetch_data()
        await asyncio.sleep(1.0) # Yields execution back to event loop!
```

#### Why not `while condition is not None`?
1. **Lifespan vs Stream**: Checking `while item is not None:` is for **streams of finite data** (e.g. reading lines from a file until EOF). A background monitoring service has an **indefinite lifespan**—it must run as long as the server is powered on.
2. **Instant Cancellation**: Rather than checking a boolean flag on every iteration, `asyncio` tasks are halted via `task.cancel()`. This immediately interrupts the coroutine at `await asyncio.sleep(1.0)` by raising `asyncio.CancelledError`.

### 9.2 The 5 Classic Situations Where `while True` is Used:
1. **Recurring Background Daemons (Event Loops)**:
   - Polling metrics, heartbeat pings, scheduled jobs.
2. **Network Servers & WebSockets**:
   - Accepting continuous incoming client connections or frames (`while True: await ws.receive()`).
3. **Queue Consumers & Message Workers**:
   - Polling Redis, RabbitMQ, Kafka, or SQS for jobs (`while True: job = queue.pop()`).
4. **Retry Logic with Exponential Backoff**:
   - Retrying a failing network call until it succeeds or reaches a break threshold.
5. **Interactive CLI Input Validation**:
   - Prompting the user until they supply valid input (`while True: val = input(); if valid: break`).




