import json
import time
import os
from google import genai
from dotenv import load_dotenv
load_dotenv()


def _build_table_prompt(table_name: str, table: dict, quality: dict | None) -> str:
    lines = []

    lines.append(f"Table: {table_name}")
    lines.append(f"Primary Key: {', '.join(table['primary_key']) or 'None'}")

    lines.append("Columns:")
    for col in table["columns"]:
        lines.append(f"  - {col['name']} ({col['type']})")

    if table["foreign_keys"]:
        lines.append("Relationships:")
        for fk in table["foreign_keys"]:
            lines.append(
                f"  - {', '.join(fk['column'])} → {fk['referred_table']}({', '.join(fk['referred_columns'])})"
            )

    if quality:
        tq = quality.get(table_name)
        if tq:
            lines.append(f"Row Count: {tq['row_count']}")
            low = [col for col, m in tq["columns"].items() if m["null_pct"] > 0.0]  # ← only this line
            if low:
                lines.append(f"Columns with missing values: {', '.join(low)}")
            else:
                lines.append("All columns fully complete (no nulls).")

    return "\n".join(lines)


def _build_prompt(table_context: str) -> str:
    return f"""You are a data dictionary assistant. Given the following database table metadata, generate a concise business-friendly summary.

{table_context}

Respond in this exact JSON format (no markdown, no extra text):
{{
  "description": "Plain English description of what this table represents and its business purpose.",
  "column_descriptions": {{
    "column_name": "Business meaning of this column"
  }},
  "relationships_summary": "How this table relates to others in plain English. Write None if no foreign keys.",
  "data_quality_notes": "Any notable observations about data quality, freshness, or completeness. Write None if no quality data."
}}"""


def generate_ai_summaries(schema: dict, quality: dict | None = None) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    summaries = {}
    total = len(schema["tables"])

    for i, (table_name, table) in enumerate(schema["tables"].items(), 1):
        print(f"  Summarizing {table_name}... ({i}/{total})")

        context = _build_table_prompt(table_name, table, quality)
        prompt = _build_prompt(context)

        # Retry loop — handles rate limits automatically
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
                    contents=prompt,
                )
                raw = response.text.strip()

                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                raw = raw.strip()

                summaries[table_name] = json.loads(raw)
                break  # success — move to next table

            except Exception as e:
                err = str(e)
                if "429" in err and attempt < 2:
                    wait = 60  # wait 60s and retry
                    print(
                        f"    Rate limited. Waiting {wait}s before retry ({attempt + 1}/3)..."
                    )
                    time.sleep(wait)
                else:
                    print(f"    Warning: failed to summarize {table_name} — {e}")
                    summaries[table_name] = {
                        "description": "Summary unavailable.",
                        "column_descriptions": {},
                        "relationships_summary": "None",
                        "data_quality_notes": "None",
                    }
                    break

        # Throttle — 13s between calls stays under 5/min limit
        if i < total:
            time.sleep(13)

    return summaries






