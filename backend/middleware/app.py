import json
import time
from connectors.sqlite import SQLiteConnector
from monitoring.sql_health import SQLHealthChecker
from monitoring.scheduler import HealthMonitor
from monitoring.storage import FileHealthStorage


# -----------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------
DB_PATH = "bike_store.db"     # Change to your SQLite file
LOG_FILE = "health_logs.jsonl"


# -----------------------------------------------------
# MAIN EXECUTION
# -----------------------------------------------------
def main():

    print("=== DBMayCry SQLite Test Runner ===\n")

    # --------------------------------------------
    # 1. CONNECT
    # --------------------------------------------
    connector = SQLiteConnector(filepath=DB_PATH)
    connector.connect()

    print("\n[STEP 1] Connected successfully.\n")

    # --------------------------------------------
    # 2. SCHEMA EXTRACTION
    # --------------------------------------------
    print("[STEP 2] Extracting schema...\n")

    schema = connector.extract_schema()

    print("=== Extracted Schema ===\n")
    print(json.dumps(schema, indent=2))

    # Optional: Save schema to file
    with open("schema_output.json", "w") as f:
        json.dump(schema, f, indent=2)

    print("\nSchema saved to schema_output.json\n")

    # --------------------------------------------
    # 3. HEALTH CHECK SETUP
    # --------------------------------------------
    print("[STEP 3] Starting health monitoring...\n")

    checker = SQLHealthChecker(connector)
    storage = FileHealthStorage(LOG_FILE)

    monitor = HealthMonitor(
        checker=checker,
        storage=storage,
        light_interval=10,     # 10 sec for demo
        deep_interval=30       # 30 sec for demo
    )

    monitor.start()

    print("Health monitor running.")
    print("Light check → every 10s")
    print("Deep check  → every 30s")
    print("Logs written to:", LOG_FILE)
    print("\nPress Ctrl+C to stop.\n")

    # --------------------------------------------
    # 4. KEEP PROCESS ALIVE
    # --------------------------------------------
    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping monitor...")

        monitor.stop()
        connector.close()

        print("Shutdown complete.")


# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------
if __name__ == "__main__":
    main()