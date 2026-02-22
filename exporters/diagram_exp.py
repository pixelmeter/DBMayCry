from graphviz import Digraph


def export_diagram(schema: dict, path: str):
    """
    path = base name without extension, e.g. 'fuelagency_er_diagram'
    Outputs a .png file.
    """
    dot = Digraph()
    dot.attr(rankdir="LR", fontname="Helvetica", fontsize="11")

    for table_name, table in schema["tables"].items():
        pk_cols = set(table["primary_key"])
        rows = [f"<TR><TD COLSPAN='2'><B>{table_name}</B></TD></TR>"]

        for col in table["columns"]:
            name = f"<B>{col['name']}</B>" if col["name"] in pk_cols else col["name"]
            rows.append(
                f"<TR><TD ALIGN='LEFT'>{name}</TD>"
                f"<TD ALIGN='LEFT'>{col['type']}</TD></TR>"
            )

        label = (
            f"<<TABLE BORDER='1' CELLBORDER='1' CELLSPACING='0'>"
            f"{''.join(rows)}</TABLE>>"
        )
        dot.node(table_name, shape="plaintext", label=label)

    for table_name, table in schema["tables"].items():
        for fk in table["foreign_keys"]:
            child = ", ".join(fk["column"])
            parent = ", ".join(fk["referred_columns"])
            dot.edge(
                table_name,
                fk["referred_table"],
                label=f"{table_name}.{child} → {fk['referred_table']}.{parent}",
                fontsize="9",
            )

    dot.render(path, format="png", cleanup=True)
    print(f"ER Diagram       → {path}.png")