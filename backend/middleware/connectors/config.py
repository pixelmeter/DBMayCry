from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    host: str
    port: Optional[int]
    username: str
    password: str
    db_path: Optional[str] = None
    database: Optional[str] = None
    uri: Optional[str] = None