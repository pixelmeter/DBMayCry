def export_llm_schema(schema: dict, path: str):
    """
    Compact .txt format for LLM context injection.
    Same information as the JSON schema but ~40% fewer tokens.
    """
    lines = []

    for table_name, table in schema["tables"].items():
        lines.append(f"TABLE {table_name}")
        pk_cols = set(table["primary_key"])

        for col in table["columns"]:
            pk = " (PK)" if col["name"] in pk_cols else ""
            lines.append(f"  - {col['name']}{pk} {col['type']}")

        if table["foreign_keys"]:
            lines.append("  RELATIONSHIPS")
            for fk in table["foreign_keys"]:
                child = ", ".join(fk["column"])
                parent = ", ".join(fk["referred_columns"])
                lines.append(
                    f"    {table_name}.{child} → {fk['referred_table']}.{parent}"
                )

        lines.append("")

    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"LLM Schema TXT   → {path}")