"""Raw SQL query functions, one per scenario. Every query is parameterized."""

import sqlite3
from typing import Any

from app.database import get_connection


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def faults_by_type() -> list[dict[str, Any]]:
    """Scenario 1: how many defects of each type have we seen?"""
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
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


def filter_by_steel_and_thickness(
    steel_type: str, min_thickness: float, max_thickness: float
) -> list[dict[str, Any]]:
    """Scenario 2: defects on a given steel type within a thickness range."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT * FROM plate_faults
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
    """Scenario 3: the n largest defects by pixel area."""
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
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()


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
            SELECT * FROM plate_faults
            WHERE fault_type = ? AND Pixels_Areas >= ?
            ORDER BY Pixels_Areas DESC
            LIMIT 50;
            """,
            (fault_type, min_area),
        )
        return _rows_to_dicts(cursor.fetchall())
    finally:
        conn.close()
