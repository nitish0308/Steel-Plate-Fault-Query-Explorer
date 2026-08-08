"""SQLite database setup: loads faults.csv into a queryable table on first run."""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "steel_faults.db"
CSV_PATH = BASE_DIR / "data" / "faults.csv"
TABLE_NAME = "plate_faults"

FAULT_COLUMNS = [
    "Pastry",
    "Z_Scratch",
    "K_Scatch",
    "Stains",
    "Dirtiness",
    "Bumps",
    "Other_Faults",
]


def _collapse_fault_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse the 7 one-hot fault columns into a single `fault_type` text column."""
    one_hot = df[FAULT_COLUMNS]
    df["fault_type"] = one_hot.idxmax(axis=1)
    return df.drop(columns=FAULT_COLUMNS)


def _build_database() -> None:
    df = pd.read_csv(CSV_PATH)
    df = _collapse_fault_columns(df)

    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_fault_type ON {TABLE_NAME}(fault_type);"
        )
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the SQLite database from the CSV if it doesn't already exist."""
    if not DB_PATH.exists():
        _build_database()

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

