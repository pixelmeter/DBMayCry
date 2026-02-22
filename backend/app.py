import os
from connectors.sqlite import SQLiteConnector
from monitoring.sql_health import SQLHealthChecker
from monitoring.scheduler import HealthMonitor
from monitoring.storage import FileHealthStorage
from exporters import json_exp, markdown_exp, llm_exp, diagram_exp
from exporters.ai_summary import generate_ai_summaries
from dotenv import load_dotenv
load_dotenv()


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

    # ── Build output directory ──────────────────────────────────────
    db_name = os.path.splitext(os.path.basename(DB_PATH))[0]  # "bike_store"
    out_dir = os.path.join("artifacts", db_name)  # "artifacts/bike_store"
    os.makedirs(out_dir, exist_ok=True)
    # ───────────────────────────────────────────────────────────────

    json_exp.export_schema(schema, os.path.join(out_dir, f"{db_name}_schema.json"))
    markdown_exp.export_schema(schema, os.path.join(out_dir, f"{db_name}_schema.md"))
    llm_exp.export_llm_schema(
        schema, os.path.join(out_dir, f"{db_name}_llm_schema.txt")
    )
    diagram_exp.export_diagram(schema, os.path.join(out_dir, f"{db_name}_er_diagram"))


    # --------------------------------------------
    # 3. HEALTH CHECK SETUP
    # --------------------------------------------
    print("[STEP 3] Running initial health checks...\n")

    checker = SQLHealthChecker(connector)

    # ── One-time exports (light + deep) ────────────────────────────
    light = checker.run_light()
    json_exp.export_health(light, os.path.join(out_dir, f"{db_name}_health_light.json"))
    markdown_exp.export_health(light, os.path.join(out_dir, f"{db_name}_health_light.md"))

    deep = checker.run_deep()
    json_exp.export_health(deep, os.path.join(out_dir, f"{db_name}_health_deep.json"))
    markdown_exp.export_health(deep, os.path.join(out_dir, f"{db_name}_health_deep.md"))
    
    # --------------------------------------------
    # 4. AI SUMMARIES
    # --------------------------------------------
    # print("[STEP 4] Generating AI summaries...\n")

    # summaries = generate_ai_summaries(schema, quality=deep.metrics["tables"])

    # json_exp.export_ai_summary(summaries, os.path.join(out_dir, f"{db_name}_ai_summary.json"))
    # markdown_exp.export_ai_summary(summaries, os.path.join(out_dir, f"{db_name}_ai_summary.md"))
    # markdown_exp.append_ai_summaries_to_schema_md(summaries, os.path.join(out_dir, f"{db_name}_schema_with_ai.md"))

    # ── 5. Continuous background monitor ──────────────────────────────
    # storage = FileHealthStorage(LOG_FILE)

    # monitor = HealthMonitor(
    #     checker=checker,
    #     storage=storage,
    #     light_interval=10,     # 10 sec for demo
    #     deep_interval=30       # 30 sec for demo
    # )

    # monitor.start()
    
    # print("Health monitor running.")
    # print("Light check → every 10s")
    # print("Deep check  → every 30s")
    # print("Logs written to:", LOG_FILE)
    # print("\nPress Ctrl+C to stop.\n")

    # --------------------------------------------
    # 6. KEEP PROCESS ALIVE
    # --------------------------------------------
    # try:
    #     while True:
    #         time.sleep(1)

    # except KeyboardInterrupt:
    #     print("\nStopping monitor...")

    #     monitor.stop()
    #     connector.close()

    #     print("Shutdown complete.")
    
    connector.close()
    print("\nDone.")


# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------
if __name__ == "__main__":
    main()