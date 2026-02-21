import json
from connectors.factory import ConnectionFactory
from extractors.sql_extractor import SQLiteSchemaExtractor


def main():

    # Change this to your actual SQLite file
    DB_PATH = "bike_store.db"

    config = {
        "database": DB_PATH
    }

    # --------------------------------
    # Create and connect connector
    # --------------------------------
    connector = ConnectionFactory.create("sqlite", config)
    connector.connect()

    print(f"Connected to SQLite DB: {DB_PATH}")

    # --------------------------------
    # Run schema extraction
    # --------------------------------
    extractor = SQLiteSchemaExtractor(connector)
    schema = extractor.extract()

    print("\n=== Extracted Schema ===\n")
    print(json.dumps(schema, indent=2))

    # --------------------------------
    # Close connection
    # --------------------------------
    connector.disconnect()
    print("\nConnection closed.")


if __name__ == "__main__":
    main()