from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any
import json

@dataclass
class HealthReport:
    database: str
    type: str  # light / deep
    status: str
    metrics: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())