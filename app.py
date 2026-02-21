import time
from connectors.factory import ConnectionFactory
from monitoring.sql_health import SQLHealthChecker
from monitoring.scheduler import HealthMonitor
from monitoring.storage import FileHealthStorage

def main():
    # Change this to your actual file
    DB_PATH = "bike_store.db"

    # Create connector
    connector = ConnectionFactory.create(
        "sqlite",
        {"database": DB_PATH}
    )

    connector.connect()

    print(f"Connected to SQLite DB: {DB_PATH}")

    # Create health checker
    checker = SQLHealthChecker(connector)

    # Create storage
    storage = FileHealthStorage("health_logs.jsonl")

    # Create monitor
    monitor = HealthMonitor(
        checker=checker,
        storage=storage,
        light_interval=10,   # 10 sec for testing
        deep_interval=30     # 30 sec for testing
    )

    monitor.start()
    print("Health monitor started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        connector.disconnect()


if __name__ == "__main__":
    main()