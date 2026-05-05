# Singleton Pattern

## Intent

Ensure a class has **only one instance** and provide a global access point to it.

---

## When to Use

- Game board, logger, configuration, thread pool, database connection pool
- When shared mutable state truly must be global

---

## Python Object Creation Flow

When you write `ClassName(args)`, Python internally does:

```
ClassName(args)
       │
       ▼
Python calls:  ClassName.__new__(ClassName, args)
       │              returns an instance (obj)
       ▼
Python checks: is obj an instance of ClassName?
       │              YES
       ▼
Python calls:  obj.__init__(args)
       │
       ▼
     returns obj to you
```

- `__new__` and `__init__` **don't talk to each other**
- Python passes the **same args** to both automatically
- `__new__` creates/returns the object, `__init__` configures it

---

## How Singleton Works

Override `__new__` to cache and return a single instance. Guard `__init__` to prevent re-initialization on subsequent calls.

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ...):
        if not hasattr(self, '_initialized'):
            # set attributes here
            self._initialized = True
```

---

## Key Details

| Aspect | `__new__` | `__init__` |
|--------|-----------|------------|
| Called by | Python automatically | Python automatically (after `__new__`) |
| Receives | `cls` + same args you passed | `self` + same args you passed |
| Job | Create/return the instance | Initialize the instance |
| Returns | Must return an object | Must return `None` |

---

## With Constructor Arguments

Make args **optional** so subsequent calls don't have to pass them. Validate in `__new__` only on first creation.

```python
class DatabaseConnection:
    _instance = None

    def __new__(cls, host=None, port=None):
        if cls._instance is None:
            if host is None or port is None:
                raise ValueError("First call must provide host and port")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host=None, port=None):
        if not hasattr(self, '_initialized'):
            self.host = host
            self.port = port
            self._initialized = True
```

```
# First call — creates and initializes
db1 = DatabaseConnection("localhost", 5432)

# Subsequent calls — returns same instance, args ignored
db2 = DatabaseConnection()
db3 = DatabaseConnection("other", 3306)

db1 is db2 is db3  # True
db3.host           # "localhost"
```

---

## Without Constructor Arguments

When no args are needed (e.g. a game board), it's simpler:

```python
class Board:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

## Common Gotcha: `__init__` Runs Every Time

Even with `__new__` returning the same instance, `__init__` still executes on every call. Without the `_initialized` guard, it will **reset your state**:

```python
# BAD — re-initializes on every call
def __init__(self, host, port):
    self.host = host
    self.port = port

# GOOD — initializes only once
def __init__(self, host=None, port=None):
    if not hasattr(self, '_initialized'):
        self.host = host
        self.port = port
        self._initialized = True
```

---

## `get_instance()` — Optional Convenience

A `get_instance()` classmethod is a readability layer, but on its own it does NOT prevent direct instantiation via `ClassName()`. Always pair it with `__new__` override for bulletproof enforcement.
