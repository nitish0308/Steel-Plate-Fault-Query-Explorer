"""Raw SQL query functions, one per scenario. Every query is parameterized."""

import sqlite3
from typing import Any

from app import cache
from app.database import get_connection


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def faults_by_type() -> list[dict[str, Any]]:
    """Scenario 1: how many defects of each type have we seen?

    Cache-aside: this aggregates the whole table on every call, so the
    result is cached in Redis and only recomputed on a cache miss or after
    a write invalidates it (see update_fault_type / delete_fault below).
    """
    cached = cache.cache_get(cache.FAULTS_BY_TYPE_KEY)
    if cached is not None:
        return cached

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT fault_type, COUNT(*) AS count
            FROM plate_faults
            GROUP BY fault_type
            ORDER BY count DESC;
            """
        )
        result = _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()

    cache.cache_set(cache.FAULTS_BY_TYPE_KEY, result)
    return result


def filter_by_steel_and_thickness(
    steel_type: str, min_thickness: float, max_thickness: float
) -> list[dict[str, Any]]:
    """Scenario 2: defects on a given steel type within a thickness range."""
    if steel_type not in ("A300", "A400"):
        raise ValueError(f"steel_type must be 'A300' or 'A400', got {steel_type!r}")
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT rowid, * FROM plate_faults
            WHERE (TypeOfSteel_A300 = 1 AND ? = 'A300' OR TypeOfSteel_A400 = 1 AND ? = 'A400')
              AND Steel_Plate_Thickness BETWEEN ? AND ?
            LIMIT 50;
            """,
            (steel_type, steel_type, min_thickness, max_thickness),
        )
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def top_defects(n: int) -> list[dict[str, Any]]:
    """Scenario 3: the n largest defects by pixel area.

    Cache-aside, keyed per `n` since the result depends on it (see
    cache.top_defects_key). Invalidated on writes that can change which
    rows/order come back, i.e. deletes (see delete_fault below).
    """
    key = cache.top_defects_key(n)
    cached = cache.cache_get(key)
    if cached is not None:
        return cached

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT fault_type, Pixels_Areas, X_Minimum, X_Maximum, Y_Minimum, Y_Maximum
            FROM plate_faults
            ORDER BY Pixels_Areas DESC
            LIMIT ?;
            """,
            (n,),
        )
        result = _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()

    cache.cache_set(key, result)
    return result


def luminosity_stats() -> list[dict[str, Any]]:
    """Scenario 4: average luminosity readings per fault type."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT fault_type,
                   ROUND(AVG(Minimum_of_Luminosity), 2) AS avg_min_luminosity,
                   ROUND(AVG(Maximum_of_Luminosity), 2) AS avg_max_luminosity,
                   ROUND(AVG(Sum_of_Luminosity), 2)     AS avg_total_luminosity
            FROM plate_faults
            GROUP BY fault_type
            ORDER BY avg_total_luminosity DESC;
            """
        )
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def search_by_fault_types_and_area(
    fault_types: list[str], min_area: float
) -> list[dict[str, Any]]:
    """Scenario 6: defects matching any of several fault types, above a minimum area.

    The IN (...) placeholder count is built from len(fault_types), but every
    value slotted into it is still passed as a bound parameter, never
    interpolated into the SQL string, so this stays injection-safe.
    """
    conn = get_connection()
    try:
        placeholders = ", ".join("?" for _ in fault_types)
        cursor = conn.execute(
            f"""
            SELECT rowid, * FROM plate_faults
            WHERE fault_type IN ({placeholders}) AND Pixels_Areas >= ?
            ORDER BY Pixels_Areas DESC
            LIMIT 50;
            """,
            (*fault_types, min_area),
        )
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def _invalidate_aggregate_caches() -> None:
    """A row's fault_type/area/existence changed, so every cached aggregate
    that could reflect it (faults-by-type counts, every top-defects n) is
    stale and must be dropped rather than served until it's recomputed."""
    cache.cache_invalidate(cache.FAULTS_BY_TYPE_KEY)
    cache.cache_invalidate(f"{cache.TOP_DEFECTS_PREFIX}:*")


def update_fault_type(rowid: int, fault_type: str) -> int:
    """Scenario 7: correct a defect's fault-type classification after inspector review.

    Rows are addressed by SQLite's implicit `rowid` since the table has no
    explicit primary key. Returns the number of rows updated (0 or 1).
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE plate_faults SET fault_type = ? WHERE rowid = ?;",
            (fault_type, rowid),
        )
        conn.commit()
        rowcount = cursor.rowcount
    finally:
        conn.close()

    if rowcount:
        _invalidate_aggregate_caches()
    return rowcount


def delete_fault(rowid: int) -> int:
    """Scenario 8: discard a defect record (e.g. sensor artifact/duplicate scan).

    Returns the number of rows deleted (0 or 1).
    """
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM plate_faults WHERE rowid = ?;", (rowid,))
        conn.commit()
        rowcount = cursor.rowcount
    finally:
        conn.close()

    if rowcount:
        _invalidate_aggregate_caches()
    return rowcount


def search_by_fault_and_area(fault_type: str, min_area: float) -> list[dict[str, Any]]:
    """Scenario 5: defects of a given type above a minimum area, for escalation review.

    NEVER do: f"SELECT * FROM plate_faults WHERE fault_type = '{fault_type}'"
    This would allow SQL injection (e.g. fault_type = "' OR '1'='1"). Always use
    parameterized queries so user input is never concatenated into the SQL string:
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT rowid, * FROM plate_faults
            WHERE fault_type = ? AND Pixels_Areas >= ?
            ORDER BY Pixels_Areas DESC
            LIMIT 50;
            """,
            (fault_type, min_area),
        )
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()
