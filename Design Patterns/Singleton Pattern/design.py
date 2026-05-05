# ──────────────────────────────────────────────
# Singleton Pattern — Without Constructor Args
# ──────────────────────────────────────────────


class Board:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.grid = [[None] * 8 for _ in range(8)]
            self._initialized = True


# ──────────────────────────────────────────────
# Singleton Pattern — With Constructor Args
# ──────────────────────────────────────────────


class DatabaseConnection:
    _instance = None

    def __new__(cls, host=None, port=None):
        if cls._instance is None:
            if host is None or port is None:
                raise ValueError("First call must provide host and port")
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host=None, port=None):
        if not hasattr(self, "_initialized"):
            self.host = host
            self.port = port
            self._initialized = True

    def __repr__(self):
        return f"DatabaseConnection(host={self.host}, port={self.port})"


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":

    # --- Board (no args) ---
    print("=== Board Singleton (no args) ===")
    b1 = Board()
    b2 = Board()
    print(f"b1 is b2: {b1 is b2}")  # True

    # --- DatabaseConnection (with args) ---
    print("\n=== DatabaseConnection Singleton (with args) ===")

    db1 = DatabaseConnection("localhost", 5432)
    print(f"db1: {db1}")  # DatabaseConnection(host=localhost, port=5432)

    db2 = DatabaseConnection()  # returns same instance, args ignored
    print(f"db2: {db2}")  # DatabaseConnection(host=localhost, port=5432)

    db3 = DatabaseConnection("other-host", 3306)  # returns same instance, args ignored
    print(f"db3: {db3}")  # DatabaseConnection(host=localhost, port=5432)

    print(f"db1 is db2: {db1 is db2}")  # True
    print(f"db1 is db3: {db1 is db3}")  # True
