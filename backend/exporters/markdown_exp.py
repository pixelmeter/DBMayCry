import os 

def export_schema(schema: dict, path: str):
    lines = [f"# Database Dictionary — {schema['database']}\n"]

    for table_name, table in schema["tables"].items():
        lines.append(f"## Table: {table_name}\n")
        lines.append("| Column | Type |")
        lines.append("|--------|------|")

        for col in table["columns"]:
            lines.append(f"| {col['name']} | {col['type']} |")

        pk = ", ".join(table["primary_key"]) or "None"
        lines.append(f"\n**Primary Key:** {pk}\n")

        if table["foreign_keys"]:
            lines.append("**Foreign Keys:**")
            for fk in table["foreign_keys"]:
                lines.append(
                    f"- {fk['column']} → {fk['referred_table']}({fk['referred_columns']})"
                )

        lines.append("\n---\n")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Schema Markdown  → {path}")


def export_health(report, path: str):
    """Accepts a HealthReport instance or dict."""
    data = report.to_dict() if hasattr(report, "to_dict") else report

    lines = [f"# Health Report — {data['database']}\n"]
    lines.append(f"**Type:** {data['type']}  ")
    lines.append(f"**Status:** {data['status']}  ")
    lines.append(f"**Timestamp:** {data['timestamp']}\n")

    metrics = data["metrics"]

    # Light report
    if "latency_ms" in metrics:
        lines.append(f"**Latency:** {metrics['latency_ms']} ms\n")

    # Deep report
    if "tables" in metrics:
        for table_name, table_data in metrics["tables"].items():
            lines.append(f"## Table: {table_name}\n")
            lines.append(f"Row Count: **{table_data['row_count']}**\n")

            if table_data.get("columns"):
                lines.append("| Column | Null % | Mean | StdDev | Min | Max |")
                lines.append("|--------|--------|------|--------|-----|-----|")
                for col_name, col_stats in table_data["columns"].items():
                    lines.append(
                        f"| {col_name} "
                        f"| {col_stats.get('null_pct', '-')} "
                        f"| {col_stats.get('mean', '-')} "
                        f"| {col_stats.get('stddev', '-')} "
                        f"| {col_stats.get('min', '-')} "
                        f"| {col_stats.get('max', '-')} |"
                    )
            lines.append("\n---\n")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Health Markdown  → {path}")
    
    
def export_ai_summary(summaries: dict, path: str):
    lines = ["# AI-Generated Table Summaries\n"]

    for table_name, s in summaries.items():
        lines.append(f"## {table_name}\n")
        lines.append(f"{s['description']}\n")

        if s.get("column_descriptions"):
            lines.append("### Column Descriptions\n")
            for col, desc in s["column_descriptions"].items():
                lines.append(f"- **{col}**: {desc}")

        if s.get("relationships_summary") and s["relationships_summary"] != "None":
            lines.append(f"\n### Relationships\n{s['relationships_summary']}")

        if s.get("data_quality_notes") and s["data_quality_notes"] != "None":
            lines.append(f"\n### Data Quality Notes\n{s['data_quality_notes']}")

        lines.append("\n---\n")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"AI Summary MD    → {path}")


def append_ai_summaries_to_schema_md(summaries: dict, schema_md_path: str):
    # Read existing schema md content
    base_path = schema_md_path.replace("_with_ai.md", ".md")
    base_content = ""
    if os.path.exists(base_path):
        with open(base_path, "r") as f:
            base_content = f.read()

    lines = ["\n---\n", "# AI-Generated Summaries\n"]

    for table_name, s in summaries.items():
        lines.append(f"## {table_name}\n")
        lines.append(f"> {s['description']}\n")

        if s.get("column_descriptions"):
            for col, desc in s["column_descriptions"].items():
                lines.append(f"- **{col}**: {desc}")
            lines.append("")

        if s.get("relationships_summary") and s["relationships_summary"] != "None":
            lines.append(f"**Relationships:** {s['relationships_summary']}\n")

        if s.get("data_quality_notes") and s["data_quality_notes"] != "None":
            lines.append(f"**Data Quality:** {s['data_quality_notes']}\n")

        lines.append("---\n")

    with open(schema_md_path, "w") as f:
        f.write(base_content)
        f.write("\n".join(lines))
    print(f"AI Summaries     → {schema_md_path}")