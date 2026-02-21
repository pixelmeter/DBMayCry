import time
from health_checker import BaseHealthChecker
from model import HealthReport


class SQLHealthChecker(BaseHealthChecker):
    def run_light(self):
        start = time.time()
        self.connector.execute("SELECT 1")
        latency = (time.time() - start) * 1000
        metrics = {
            "latency_ms": round(latency, 2)
        }
        return HealthReport(
            database=self.connector.config.get("database", "unknown"),
            type="light",
            status="healthy",
            metrics=metrics
        )

    def run_deep(self):
        tables = self.connector.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_type = 'BASE TABLE';
        """)
        table_reports = {}

        for (table_name,) in tables:
            # Row count
            row_count = self.connector.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            )[0][0]
            columns = self.connector.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)

            column_stats = {}

            for col_name, data_type in columns:
                # Null %
                null_count = self.connector.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL"
                )[0][0]

                null_pct = (
                    null_count / row_count if row_count > 0 else 0
                )

                stats = {
                    "null_pct": round(null_pct, 4)
                }

                # Numeric statistics
                if data_type.lower() in (
                    "int", "integer", "bigint",
                    "decimal", "float", "double"
                ):
                    result = self.connector.execute(f"""
                        SELECT
                            AVG({col_name}),
                            STDDEV({col_name}),
                            MIN({col_name}),
                            MAX({col_name})
                        FROM {table_name}
                    """)

                    avg, stddev, min_val, max_val = result[0]

                    stats.update({
                        "mean": avg,
                        "stddev": stddev,
                        "min": min_val,
                        "max": max_val
                    })

                column_stats[col_name] = stats

            table_reports[table_name] = {
                "row_count": row_count,
                "columns": column_stats
            }

        return HealthReport(
            database=self.connector.config.get("database", "unknown"),
            type="deep",
            status="healthy",
            metrics={"tables": table_reports}
        )