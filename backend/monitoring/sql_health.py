# import time
# from .health_checker import BaseHealthChecker
# from .model import HealthReport


# class SQLHealthChecker(BaseHealthChecker):

#     def run_light(self):
#         start = time.time()
#         self.connector.run("SELECT 1")
#         latency = (time.time() - start) * 1000

#         return HealthReport(
#             database=self.connector.engine.url.database,
#             type="light",
#             status="healthy",
#             metrics={
#                 "latency_ms": round(latency, 2)
#             }
#         )

#     def run_deep(self):

#         dialect = self.connector.engine.dialect.name
#         table_reports = {}

#         if dialect == "sqlite":

#             tables = self.connector.run(
#                 "SELECT name FROM sqlite_master WHERE type='table';"
#             )

#             for (table_name,) in tables:

#                 if table_name.startswith("sqlite_"):
#                     continue

#                 row_count = self.connector.run(
#                     f'SELECT COUNT(*) FROM "{table_name}"'
#                 )[0][0]

#                 columns = self.connector.run(
#                     f'PRAGMA table_info("{table_name}");'
#                 )

#                 column_stats = {}

#                 for col in columns:
#                     col_name = col[1]
#                     col_type = col[2].lower()

#                     null_count = self.connector.run(
#                         f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NULL'
#                     )[0][0]

#                     null_pct = (
#                         null_count / row_count if row_count > 0 else 0
#                     )

#                     stats = {
#                         "null_pct": round(null_pct, 4)
#                     }

#                     if any(t in col_type for t in ["int", "real", "numeric", "float", "double"]):

#                         result = self.connector.run(f"""
#                             SELECT
#                                 AVG("{col_name}"),
#                                 MIN("{col_name}"),
#                                 MAX("{col_name}")
#                             FROM "{table_name}"
#                         """)

#                         avg, min_val, max_val = result[0]

#                         variance_query = f"""
#                             SELECT AVG((
#                                 "{col_name}" - (
#                                     SELECT AVG("{col_name}") FROM "{table_name}"
#                                 )
#                             ) * (
#                                 "{col_name}" - (
#                                     SELECT AVG("{col_name}") FROM "{table_name}"
#                                 )
#                             ))
#                             FROM "{table_name}"
#                             WHERE "{col_name}" IS NOT NULL
#                         """

#                         variance = self.connector.run(variance_query)[0][0]
#                         stddev = variance ** 0.5 if variance is not None else None

#                         stats.update({
#                             "mean": avg,
#                             "stddev": stddev,
#                             "min": min_val,
#                             "max": max_val
#                         })

#                     column_stats[col_name] = stats

#                 table_reports[table_name] = {
#                     "row_count": row_count,
#                     "columns": column_stats
#                 }

#         elif dialect == "postgresql":

#             tables = self.connector.run("""
#                 SELECT table_name
#                 FROM information_schema.tables
#                 WHERE table_schema = 'public'
#                 AND table_type = 'BASE TABLE';
#             """)

#             for (table_name,) in tables:

#                 row_count = self.connector.run(
#                     f'SELECT COUNT(*) FROM "public"."{table_name}"'
#                 )[0][0]

#                 columns = self.connector.run(f"""
#                     SELECT column_name, data_type
#                     FROM information_schema.columns
#                     WHERE table_schema = 'public'
#                     AND table_name = '{table_name}';
#                 """)

#                 column_stats = {}

#                 for col_name, data_type in columns:

#                     null_count = self.connector.run(
#                         f'SELECT COUNT(*) FROM "public"."{table_name}" WHERE "{col_name}" IS NULL'
#                     )[0][0]

#                     null_pct = (
#                         null_count / row_count if row_count > 0 else 0
#                     )

#                     stats = {
#                         "null_pct": round(null_pct, 4)
#                     }

#                     if data_type.lower() in (
#                         "integer", "bigint", "smallint",
#                         "numeric", "real", "double precision"
#                     ):

#                         result = self.connector.run(f"""
#                             SELECT
#                                 AVG("{col_name}"),
#                                 STDDEV("{col_name}"),
#                                 MIN("{col_name}"),
#                                 MAX("{col_name}")
#                             FROM "public"."{table_name}"
#                         """)

#                         avg, stddev, min_val, max_val = result[0]

#                         stats.update({
#                             "mean": avg,
#                             "stddev": stddev,
#                             "min": min_val,
#                             "max": max_val
#                         })

#                     column_stats[col_name] = stats

#                 table_reports[table_name] = {
#                     "row_count": row_count,
#                     "columns": column_stats
#                 }

#         else:

#             tables = self.connector.run("""
#                 SELECT table_name
#                 FROM information_schema.tables
#                 WHERE table_type = 'BASE TABLE';
#             """)

#             for (table_name,) in tables:

#                 row_count = self.connector.run(
#                     f"SELECT COUNT(*) FROM {table_name}"
#                 )[0][0]

#                 table_reports[table_name] = {
#                     "row_count": row_count
#                 }

#         return HealthReport(
#             database=self.connector.engine.url.database,
#             type="deep",
#             status="healthy",
#             metrics={"tables": table_reports}
#         )


import time
from .health_checker import BaseHealthChecker
from .model import HealthReport


def _is_numeric(col_type: str) -> bool:
    return any(
        k in col_type.lower()
        for k in ["int", "real", "numeric", "float", "double", "decimal"]
    )


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

                # col layout: (cid, name, type, notnull, dflt_value, pk)
                pk_cols = {col[1] for col in columns if col[5] != 0}

                # Collect FK columns
                fk_rows = self.connector.run(
                    f'PRAGMA foreign_key_list("{table_name}");'
                )
                # fk layout: (id, seq, table, from, to, ...)
                fk_cols = {row[3] for row in fk_rows}

                skip_cols = pk_cols | fk_cols

                column_stats = {}

                for col in columns:
                    col_name = col[1]
                    col_type = col[2].lower()

                    # Skip id-named, PK, and FK columns
                    if "id" in col_name.lower():
                        continue
                    if col_name in skip_cols:
                        continue

                    null_count = self.connector.run(
                        f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" IS NULL'
                    )[0][0]

                    null_pct = (
                        null_count / row_count if row_count > 0 else 0
                    )

                    stats = {
                        "null_pct": round(null_pct, 4)
                    }

                    # Only compute numeric stats for numeric column types
                    if _is_numeric(col_type):

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

                # Fetch PK columns
                pk_rows = self.connector.run(f"""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = '{table_name}';
                """)
                pk_cols = {row[0] for row in pk_rows}

                # Fetch FK columns
                fk_rows = self.connector.run(f"""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = '{table_name}';
                """)
                fk_cols = {row[0] for row in fk_rows}

                skip_cols = pk_cols | fk_cols

                column_stats = {}

                for col_name, data_type in columns:

                    # Skip id-named, PK, and FK columns
                    if "id" in col_name.lower():
                        continue
                    if col_name in skip_cols:
                        continue

                    null_count = self.connector.run(
                        f'SELECT COUNT(*) FROM "public"."{table_name}" WHERE "{col_name}" IS NULL'
                    )[0][0]

                    null_pct = (
                        null_count / row_count if row_count > 0 else 0
                    )

                    stats = {
                        "null_pct": round(null_pct, 4)
                    }

                    # Only compute numeric stats for numeric column types
                    if data_type.lower() in (
                        "integer", "bigint", "smallint",
                        "numeric", "real", "double precision", "decimal"
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