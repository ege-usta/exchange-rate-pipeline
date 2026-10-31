"""Step 3 - Load: save the clean rows into a SQLite database."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS rates (
    date    TEXT NOT NULL,
    code    TEXT NOT NULL,
    name    TEXT NOT NULL,
    buying  REAL NOT NULL,
    selling REAL,
    PRIMARY KEY (date, code)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute(SCHEMA)
    return connection


def load(connection: sqlite3.Connection, rows: list[dict]) -> int:
    # INSERT OR REPLACE: running the pipeline twice never creates duplicate rows.
    connection.executemany(
        "INSERT OR REPLACE INTO rates (date, code, name, buying, selling) "
        "VALUES (:date, :code, :name, :buying, :selling)",
        rows,
    )
    connection.commit()
    return len(rows)
