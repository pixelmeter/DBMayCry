from dataclasses import dataclass, asdict
from typing import List, Optional
import json

@dataclass
class ColumnSchema:
    name: str
    dtype: str
    nullable: bool
    primary_key: bool = False
    foreign_key: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnSchema]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "columns": [col.to_dict() for col in self.columns]
        }


@dataclass
class DatabaseSchema:
    database: str
    tables: List[TableSchema]

    def to_dict(self) -> dict:
        return {
            "database": self.database,
            "tables": [table.to_dict() for table in self.tables]
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    # def to_markdown(self) -> str:
    #     lines = [f"# Database: {self.database}", ""]
        
    #     for table in self.tables:
    #         lines.append(f"## Table: {table.name}")
    #         lines.append("")
    #         lines.append("| Column | Type | Nullable | PK | FK |")
    #         lines.append("|--------|------|----------|----|----|")

    #         for col in table.columns:
    #             lines.append(
    #                 f"| {col.name} | {col.dtype} | "
    #                 f"{'YES' if col.nullable else 'NO'} | "
    #                 f"{'YES' if col.primary_key else ''} | "
    #                 f"{col.foreign_key or ''} |"
    #             )

    #         lines.append("")

    #     return "\n".join(lines)