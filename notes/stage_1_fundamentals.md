# Stage 1: Python Fundamentals for TypeScript Developers

A reference notebook summarizing core Python concepts, syntax differences, data structures, and mental models compared against TypeScript.

---

## 1. Environment & Package Management

| Concept | TypeScript / Node.js | Python |
| :--- | :--- | :--- |
| **Package Manifest** | `package.json` | `requirements.txt` or `pyproject.toml` |
| **Local Dependencies** | `node_modules/` | `.venv/Lib/site-packages/` |
| **Environment Isolation** | Automatic per directory | Must create & activate a virtual environment (`venv`) |
| **Package Installer** | `npm` / `pnpm` / `yarn` | `pip` |
| **Module / Package Marker** | Any file with `export` | Folders with `__init__.py` are Python packages |

### Key Commands (PowerShell)
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install packages (Always prefer 'python -m pip' over bare 'pip')
python -m pip install <package-name>
python -m pip install -r requirements.txt

# Save installed dependencies
python -m pip freeze > requirements.txt
```

> **Take Notice: Why `python -m pip` instead of bare `pip`?**
> Unlike `npm` (which always resolves to `./node_modules` in your current folder), running bare `pip` on Windows may resolve to a global Python installation in your system `PATH` (e.g. Python 3.14) instead of your virtual environment (`.venv` running Python 3.13).
> Running **`python -m pip install`** explicitly tells the currently active Python interpreter to run its own pip module, guaranteeing packages land in your `.venv/Lib/site-packages`.


---

## 2. Core Syntax Differences

### 2.1 Casing Conventions (PEP 8)
- **Variables & Functions**: `snake_case` (e.g. `cpu_percent`, `get_process_info`) — *not `camelCase`*.
- **Classes**: `PascalCase` (e.g. `ProcessSnapshot`, `SystemSnapshot`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g. `DEFAULT_THRESHOLD = 85.0`).

### 2.2 Blocks & Indentation
- Python does **not** use curly braces `{}` for code blocks.
- Blocks are defined strictly by **indentation** (standard: 4 spaces, never tabs).
- A colon `:` signals the start of an indented block (functions, classes, if statements, loops).

### 2.3 Booleans, Nullability, and Logic
| Feature | TypeScript | Python |
| :--- | :--- | :--- |
| **Booleans** | `true`, `false` | `True`, `False` *(Capitalized)* |
| **Null Value** | `null` and `undefined` | `None` *(There is only one null type in Python)* |
| **Logical AND** | `&&` | `and` |
| **Logical OR** | `\|\|` | `or` |
| **Logical NOT** | `!` | `not` |
| **Value Equality** | `===` | `==` *(Checks if values are equal)* |
| **Identity / Pointer** | Object reference check | `is` *(Checks if two variables point to the exact same object in memory)* |

> **Take Notice**: Never use `== None`. Always use `if value is None:` or `if value is not None:`.

### 2.4 String Formatting
- **TypeScript**: Template literals `` `Hello ${name}, CPU: ${cpu}%` ``.
- **Python**: **F-Strings** `f"Hello {name}, CPU: {cpu}%"`.
  ```python
  name = "python.exe"
  cpu = 14.256
  # Basic interpolation
  text = f"Process: {name}"
  
  # Format specifiers (e.g., round to 1 decimal place)
  formatted = f"CPU: {cpu:.1f}%"  # Output: 'CPU: 14.3%'
  ```

---

## 3. Data Structures

### 3.1 Dictionaries (`dict`) vs JavaScript Objects / Record
In TypeScript, objects `{}` serve as both dictionaries and struct-like objects:
```typescript
const process = { name: "node.exe", pid: 1024 };
console.log(process.name);      // "node.exe"
console.log(process.missing);   // undefined (silent!)
```

In Python, a `dict` is strictly a key-value hash map:
```python
process = {"name": "python.exe", "pid": 1024}

# 1. Bracket Access:
process["name"]        # "python.exe"
# process["missing"]   # CRASHES! Raises KeyError (Python does not silently return undefined)

# 2. Safe Access with .get():
process.get("missing")          # Returns None (like undefined)
process.get("missing", "N/A")   # Returns fallback default "N/A"

# 3. Dot notation DOES NOT WORK for dict keys:
# process.name         # CRASHES! Raises AttributeError. Dicts are not objects with properties.
```

### 3.2 Lists (`list`) vs Arrays
Python `list` is equivalent to a JavaScript Array:
```python
items = [1, 2, 3]
items.append(4)        # Like items.push(4)
items.pop()            # Like items.pop() (removes and returns 4)
items.insert(0, 99)    # Insert at index 0
length = len(items)    # Like items.length
```

### 3.3 Tuples (`tuple`) — Immutable Lists
Tuples are fixed-size, immutable sequences created with parentheses `()`:
```python
point = (10, 20)
# point[0] = 15       # CRASHES! TypeError: 'tuple' object does not support item assignment
x, y = point          # Destructuring works just like in TS: const [x, y] = point;
```

---

## 4. Classes & Object-Oriented Programming (OOP)

### 4.1 Class Structure & The `self` Parameter
In TypeScript:
```typescript
class ProcessSnapshot {
  pid: number;
  name: string;

  constructor(pid: number, name: string) {
    this.pid = pid;
    this.name = name;
  }

  isChrome(): boolean {
    return this.name === "chrome.exe";
  }
}
```

In Python:
```python
class ProcessSnapshot:
    def __init__(self, pid: int, name: str) -> None:
        self.pid = pid
        self.name = name

    def is_chrome(self) -> bool:
        return self.name == "chrome.exe"
```

> **Take Notice: What is `self`?**
> - In TypeScript, `this` is an implicit context bound by the runtime.
> - In Python, **`self` must be explicitly declared as the first parameter** in every instance method.
> - When you call `p.is_chrome()`, Python translates it behind the scenes to `ProcessSnapshot.is_chrome(p)`.

---

## 5. Dunder (Magic) Methods

Methods surrounded by double underscores `__method__` are called **Dunder methods** (or Special Methods). They allow Python classes to hook into language operators and built-in functions (Operator Overloading).

| Dunder Method | Purpose | TS Equivalent / Analogy |
| :--- | :--- | :--- |
| `__init__(self, ...)` | Constructor called when creating an instance | `constructor(...)` |
| `__repr__(self) -> str` | Developer-facing debug representation (used in console & errors) | Custom inspection / `toString()` |
| `__str__(self) -> str` | User-facing formatted string (called by `print(obj)` or `str(obj)`) | `toString()` |
| `__lt__(self, other) -> bool` | Defines behavior for `<` (Less Than). Enables `sorted(items)` | `(a, b) => a - b` comparator |
| `__eq__(self, other) -> bool` | Defines behavior for `==` (Equality) | Deep equality helper |
| `__len__(self) -> int` | Called by `len(obj)` | `.length` property |

### Example: Implementing `__lt__` for Sorting
In TypeScript:
```typescript
const sortedProcesses = processes.sort((a, b) => a.cpuPercent - b.cpuPercent);
```

In Python:
```python
class ProcessSnapshot:
    def __init__(self, name: str, cpu_percent: float):
        self.name = name
        self.cpu_percent = cpu_percent

    def __lt__(self, other: "ProcessSnapshot") -> bool:
        return self.cpu_percent < other.cpu_percent

# Now Python knows how to sort them directly using `<`!
sorted_list = sorted(processes)                 # Ascending order
sorted_list_desc = sorted(processes, reverse=True) # Descending order
```

---

## 6. Crucial Python Gotchas for TS Developers

1. **Missing Dict Keys Crash**: Accessing a non-existent key with `dict["key"]` raises `KeyError`. Use `dict.get("key")` if the key might be absent.
2. **Never Use Mutable Default Arguments**:
   ```python
   # BUG IN PYTHON: The list is created once at function definition time, not call time!
   def add_process(proc, proc_list=[]):  # BAD!
       proc_list.append(proc)
       return proc_list

   # CORRECT PATTERN:
   def add_process(proc, proc_list=None):
       if proc_list is None:
           proc_list = []
       proc_list.append(proc)
       return proc_list
   ```
3. **No Block Scope for `if` or `for`**:
   In TypeScript, `let` and `const` are block-scoped to `{}`. In Python, variables declared inside an `if` block or `for` loop leak into the enclosing function scope.
4. **Truthy / Falsy in Python**:
   - `0`, `0.0`, `""`, `[]` (empty list), `{}` (empty dict), `set()` (empty set), `None`, `False` are all **Falsy**.
   - You can simply write: `if not processes:` to check if a list is empty!

---

## 7. Exception Handling (`try...except` vs `try...catch`)

| Concept | TypeScript | Python |
| :--- | :--- | :--- |
| **Block Keyword** | `try { ... } catch (err) { ... }` | `try: ... except Exception as err: ...` |
| **Specific Errors** | `if (err instanceof CustomError)` | `except CustomError:` *(directly in the syntax)* |
| **Multiple Errors** | Check multiple `if` conditions | `except (ErrorA, ErrorB):` *(tuple of errors)* |
| **Empty Block / No-op** | `{}` | `pass` *(Required! Python cannot have empty blocks)* |
| **Finally Block** | `finally { ... }` | `finally: ...` |
| **Else Block** | *(None)* | `else:` *(Runs ONLY if NO exception was raised)* |

```python
try:
    proc = psutil.Process(pid)
    cpu = proc.cpu_percent()
except psutil.NoSuchProcess:
    # Process already exited while we were checking it
    pass
except (psutil.AccessDenied, psutil.ZombieProcess):
    # Windows system process or defunct process
    pass
```

---

## 8. List Comprehensions vs `.map()` & `.filter()`

In TypeScript, functional array transformations are chained:
```typescript
// TypeScript: Filter active processes and extract their names
const activeNames = processes
    .filter(p => p.cpuPercent > 0.5)
    .map(p => p.name.toLowerCase());
```

In Python, **List Comprehensions** are the idiomatic, highly optimized standard:
```python
# Python Syntax:
# [ <transform_expression> for <item> in <iterable> if <condition> ]

active_names = [p.name.lower() for p in processes if p.cpu_percent > 0.5]
```

### Breaking Down the Syntax:
1. `p.name.lower()`: What goes into the new list (the `.map()` projection).
2. `for p in processes`: Loop iteration.
3. `if p.cpu_percent > 0.5`: Optional filter (the `.filter()` predicate).

### Dict Comprehensions:
Just like lists, you can build dictionaries on the fly:
```python
# TS: Object.fromEntries(processes.map(p => [p.pid, p.name]))
pid_to_name = {p.pid: p.name for p in processes}
```

---

## 9. Lambdas vs Arrow Functions

- **TypeScript Arrow Function**: `(p) => p.cpuPercent`
- **Python Lambda**: `lambda p: p.cpu_percent`

Lambdas in Python are **single-expression anonymous functions**. They cannot contain statements or multiple lines:
```python
# Sorting top 10 processes by memory usage descending:
top_memory = sorted(processes, key=lambda p: p.memory_percent, reverse=True)[:10]
```

---

## 10. List Slicing (`[start:stop:step]`) vs `.slice()`

Python has native slicing syntax on any sequence:

| Operation | TypeScript | Python |
| :--- | :--- | :--- |
| First 10 items | `arr.slice(0, 10)` | `arr[:10]` |
| Items from index 5 to end | `arr.slice(5)` | `arr[5:]` |
| Last 5 items | `arr.slice(-5)` | `arr[-5:]` |
| Every 2nd item | *(Needs reduce/filter)* | `arr[::2]` |
| Reverse an array | `[...arr].reverse()` | `arr[::-1]` |

---

## 11. How `psutil` Works & Process Safety

`psutil` (Python System and Process Utilities) interfaces with Windows/Linux system calls:

1. **CPU Percent Calculation**:
   - CPU usage is a **rate over time** ($\Delta \text{CPU time} / \Delta \text{wall clock time}$).
   - First call: `psutil.cpu_percent()` returns `0.0` (it establishes the baseline).
   - Subsequent calls: Returns the CPU utilization percentage since the previous call.
2. **Process Lifecycle Race Conditions**:
   - Processes terminate, spawn, or elevate permissions continuously.
   - Calling `psutil.process_iter(['pid', 'name', 'cpu_percent'])` fetches attributes in batch for high performance.
   - Always wrap individual process attribute lookups in `try...except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess)`.

