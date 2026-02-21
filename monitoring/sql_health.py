import time
from .health_checker import BaseHealthChecker
from .model import HealthReport


class SQLHealthChecker(BaseHealthChecker):

    def run_light(self):
        start = time.time()
        self.connector.run("SELECT 1")
        latency = (time.time() - start) * 1000

        return HealthReport(
            database=self.connector.engine.url.database,
            type="light",
            status="healthy",
            metrics={
                "latency_ms": round(latency, 2)
            }
        )

    def run_deep(self):

        dialect = self.connector.engine.dialect.name
        table_reports = {}

        if dialect == "sqlite":

            tables = self.connector.run(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )

            for (table_name,) in tables:

                if table_name.startswith("sqlite_"):
                    continue

                row_count = self.connector.run(
                    f'SELECT COUNT(*) FROM "{table_name}"'
                )[0][0]

                columns = self.connector.run(
                    f'PRAGMA table_info("{table_name}");'
                )

                column_stats = {}

                for col in columns:
                    col_name = col[1]
                    col_type = col[2].lower()

                    null_count = self.connector.run(
                        f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NULL'
                    )[0][0]

                    null_pct = (
                        null_count / row_count if row_count > 0 else 0
                    )

                    stats = {
                        "null_pct": round(null_pct, 4)
                    }

                    if any(t in col_type for t in ["int", "real", "numeric", "float", "double"]):

                        result = self.connector.run(f"""
                            SELECT
                                AVG("{col_name}"),
                                MIN("{col_name}"),
                                MAX("{col_name}")
                            FROM "{table_name}"
                        """)

                        avg, min_val, max_val = result[0]

                        variance_query = f"""
                            SELECT AVG((
                                "{col_name}" - (
                                    SELECT AVG("{col_name}") FROM "{table_name}"
                                )
                            ) * (
                                "{col_name}" - (
                                    SELECT AVG("{col_name}") FROM "{table_name}"
                                )
                            ))
                            FROM "{table_name}"
                            WHERE "{col_name}" IS NOT NULL
                        """

                        variance = self.connector.run(variance_query)[0][0]
                        stddev = variance ** 0.5 if variance is not None else None

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

        elif dialect == "postgresql":

            tables = self.connector.run("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE';
            """)

            for (table_name,) in tables:

                row_count = self.connector.run(
                    f'SELECT COUNT(*) FROM "public"."{table_name}"'
                )[0][0]

                columns = self.connector.run(f"""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = '{table_name}';
                """)

                column_stats = {}

                for col_name, data_type in columns:

                    null_count = self.connector.run(
                        f'SELECT COUNT(*) FROM "public"."{table_name}" WHERE "{col_name}" IS NULL'
                    )[0][0]

                    null_pct = (
                        null_count / row_count if row_count > 0 else 0
                    )

                    stats = {
                        "null_pct": round(null_pct, 4)
                    }

                    if data_type.lower() in (
                        "integer", "bigint", "smallint",
                        "numeric", "real", "double precision"
                    ):

                        result = self.connector.run(f"""
                            SELECT
                                AVG("{col_name}"),
                                STDDEV("{col_name}"),
                                MIN("{col_name}"),
                                MAX("{col_name}")
                            FROM "public"."{table_name}"
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

        else:

            tables = self.connector.run("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE';
            """)

            for (table_name,) in tables:

                row_count = self.connector.run(
                    f"SELECT COUNT(*) FROM {table_name}"
                )[0][0]

                table_reports[table_name] = {
                    "row_count": row_count
                }

        return HealthReport(
            database=self.connector.engine.url.database,
            type="deep",
            status="healthy",
            metrics={"tables": table_reports}
        )