from __future__ import annotations



def _insert_conflicts(connection: sqlite3.Connection, conflicts: Iterable[Mapping[str, Any]]) -> None:
    for conflict in conflicts:
        connection.execute(
            """
            INSERT INTO conflicts(
                conflict_id, object_id, field, conflict_type, status, event_ids_json, details_json, detected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conflict["conflict_id"],
                conflict["object_id"],
                conflict["field"],
                conflict["conflict_type"],
                conflict["status"],
                conflict["event_ids_json"],
                conflict["details_json"],
                conflict["detected_at"],
            ),
        )


def _count_rows(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row is not None else 0
