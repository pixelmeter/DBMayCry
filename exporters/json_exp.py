import json
from decimal import Decimal


def _safe(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


def export_schema(schema: dict, path: str):
    with open(path, "w") as f:
        json.dump(schema, f, indent=4)
    print(f"Schema JSON      → {path}")
    
    
def export_health(report, path: str):
    """Accepts a HealthReport instance or dict."""
    data = report.to_dict() if hasattr(report, "to_dict") else report
    with open(path, "w") as f:
        json.dump(data, f, indent=4, default=_safe)
    print(f"Health JSON      → {path}")
    
    
def export_ai_summary(summaries: dict, path: str):
    with open(path, "w") as f:
        json.dump(summaries, f, indent=4)
    print(f"AI Summary JSON  → {path}")