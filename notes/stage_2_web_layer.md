# Stage 2: Web & Streaming Layer for TypeScript Developers

A reference notebook covering FastAPI, Pydantic v2, Python decorators, async/await coroutines, and WebSockets compared against Express.js, Zod, and Node.js.

---

## 1. Web Architecture: Express.js vs FastAPI

| Feature | Express.js (Node.js) | FastAPI (Python) |
| :--- | :--- | :--- |
| **Server Runtime** | Node.js runtime (`node index.js`) | ASGI server (e.g. `uvicorn app:app --reload`) |
| **Route Registration** | Method calls: `app.get("/path", handler)` | Decorator syntax: `@app.get("/path")` |
| **Request Parsing & Validation** | External library (Zod, Joi, express-validator) | Built-in via **Pydantic v2** |
| **OpenAPI / Swagger Docs** | Manual setup (swagger-ui-express + JSDoc) | **Automatic out-of-the-box** at `/docs` and `/redoc` |
| **Asynchronous Nature** | Promise-based (Event loop native) | Corout__init__ine-based (`async def` / `await` via `asyncio`) |

---

## 2. Python Decorators (`@decorator`)

In Python, the `@` symbol denotes a **Decorator**. A decorator is a function that takes another function as input, extends its behavior, and returns it.

### In TypeScript / Express:
```typescript
// Explicit function wrapping or chaining
app.get("/api/system", (req, res) => {
  res.json({ status: "ok" });
});
```

### In Python / FastAPI:
```python
@app.get("/api/system")
def get_system():
    return {"status": "ok"}
```

**How it works under the hood**:
```python
# The syntax:
@app.get("/api/system")
def get_system(): ...

# Is syntactic sugar for:
get_system = app.get("/api/system")(get_system)
```
FastAPI inspects the function parameters and return type annotations using reflection to validate requests and auto-generate Swagger UI.

---

## 3. Data Validation: Pydantic v2 vs Zod

If you know **Zod**, you already know 90% of **Pydantic**. Both validate data at runtime and enforce TypeScript/Python types.

### TypeScript + Zod:
```typescript
import { z } from "zod";

export const ProcessSchema = z.object({
  pid: z.number().int(),
  name: z.string(),
  cpuPercent: z.number().default(0.0),
});

export type Process = z.infer<typeof ProcessSchema>;

// Parsing/Validating:
const result = ProcessSchema.parse(rawJson);
```

### Python + Pydantic v2:
```python
from pydantic import BaseModel, Field

class ProcessSchema(BaseModel):
    pid: int
    name: str
    cpu_percent: float = 0.0

    # Optional: Read directly from OOP class attributes (like our ProcessSnapshot!)
    model_config = {"from_attributes": True}

# Parsing/Validating:
result = ProcessSchema.model_validate(raw_dict)

# Exporting back to dictionary or JSON string:
data_dict = result.model_dump()
json_string = result.model_dump_json()
```

> **Take Notice: Type Coercion**:
> Just like Zod, Pydantic will automatically coerce compatible types (e.g. string `"123"` into integer `123`) if valid, or raise `ValidationError` with detailed field paths if invalid.

---

## 4. Async / Await: Python Coroutines vs JS Promises

While the syntax looks nearly identical, Python's runtime model has critical differences.

| Feature | TypeScript / JavaScript | Python |
| :--- | :--- | :--- |
| **Async function definition** | `async function fetchData() { ... }` | `async def fetch_data(): ...` |
| **Return type** | Always returns a `Promise<T>` | Returns a **Coroutine object** |
| **Execution Trigger** | **Eager**: Calling `fetchData()` starts running immediately | **Lazy**: Calling `fetch_data()` does **NOT** run until `await` or scheduled |
| **Sleep / Delay** | `await new Promise(r => setTimeout(r, 1000))` | `await asyncio.sleep(1.0)` |
| **Blocking Sleep (Danger!)** | N/A (unless sync while loop) | `time.sleep(1.0)` **BLOCKS the entire event loop** |

> **CRITICAL GOTCHA**:
> Never call `time.sleep()` inside an `async def` function! It halts the entire thread and freezes all connected WebSocket clients and HTTP requests. Always use `await asyncio.sleep()`.

---

## 5. WebSockets: Real-Time Push vs Polling

HTTP is a request-response protocol: the client must constantly poll (`setInterval`) to get fresh metrics.
**WebSockets** provide a persistent, two-way (full-duplex) TCP connection:
1. Client connects via `ws://localhost:8000/ws/live`.
2. Connection is upgraded from HTTP to WebSocket (`await websocket.accept()`).
3. Server continuously pushes fresh metric snapshots whenever ready.

### FastAPI WebSocket Lifecycle:
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio

app = FastAPI()

@app.websocket("/ws/live")
async def websocket_live_metrics(websocket: WebSocket):
    # 1. Accept the incoming handshake
    await websocket.accept()
    try:
        while True:
            # 2. Gather data and push JSON to client
            data = {"cpu": 15.2, "timestamp": 1727170000}
            await websocket.send_json(data)
            
            # 3. Non-blocking sleep for the push interval
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        # 4. Handle clean disconnect when user closes browser
        print("Client disconnected.")
```

---

## 6. CORS (Cross-Origin Resource Sharing)

When your React/TS frontend (running on `http://localhost:5173`) talks to your FastAPI backend (running on `http://localhost:8000`), the browser enforces CORS.

In Express:
```typescript
import cors from "cors";
app.use(cors());
```

In FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, specify exact frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 7. Python Module Resolution vs Node.js (`ModuleNotFoundError`)

In Node.js, `require('./src/...')` or path aliases in `tsconfig.json` resolve modules easily. In Python, module imports depend on `sys.path`.

### The Problem:
If your project structure is:
```
glances-mini/
└── src/
    └── glances_mini/
```
When running commands from the root directory (`glances-mini/`), Python includes `.` (the root) in `sys.path`, but **not** `./src`.
So when Python sees `from glances_mini.collector import SystemCollector`, it looks for a folder named `glances_mini/` in the root and fails with:
```
ModuleNotFoundError: No module named 'glances_mini'
```

### The Solutions:
1. **The Uvicorn Flag (`--app-dir`)**:
   Tell Uvicorn that application code lives inside `src`:
   ```powershell
   uvicorn glances_mini.web.app:app --app-dir src --reload --port 8001
   ```
2. **Set `PYTHONPATH` in PowerShell**:
   ```powershell
   $env:PYTHONPATH="src"
   uvicorn glances_mini.web.app:app --reload --port 8001
   ```

---

## 8. Python Gotcha: The `JSON.parse(JSON.stringify())` Deep Clone Trap

In JavaScript/TypeScript, a common idiom to convert or clone objects is:
```typescript
const plainObj = JSON.parse(JSON.stringify(instance));
```

In Python, attempting to do this inside a class method like:
```python
def to_dict(self):
    snapshot = ProcessSnapshot(...)
    res = json.dumps(snapshot.to_dict())  # CRASH! RecursionError!
    return json.loads(res)
```
causes an **infinite recursion loop**: `to_dict()` calls `to_dict()` on a new object, which calls `to_dict()` again until Python hits the call stack limit.

### Idiomatic Python Solution:
In Python, an object's state is simply represented by a native `dict`. No serialization/deserialization is needed:
```python
def to_dict(self) -> Dict[str, Any]:
    return {
        "pid": self.pid,
        "name": self.name,
        "cpu_percent": self.cpu_percent,
        "memory_percent": self.memory_percent,
        "memory_rss_bytes": self.memory_rss_bytes,
        "disk_read_bytes_sec": self.disk_read_bytes_sec,
        "disk_write_bytes_sec": self.disk_write_bytes_sec,
    }
```
Or use Python's built-in `vars(self)` / `__dict__`!

