
"""Store Docker sandbox evaluation results in SQLite."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_FILE = Path("evaluation_results.db")


def initialize_database(db_path=DB_FILE):
    """Create the sandbox results table if it does not exist."""
    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                candidate TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                execution_seconds REAL NOT NULL,
                stdout TEXT NOT NULL,
                stderr TEXT NOT NULL
            )
        """)


def save_sandbox_result(candidate, result, db_path=DB_FILE):
    """Save one result returned by run_in_sandbox."""
    timestamp = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                candidate TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                execution_seconds REAL NOT NULL,
                stdout TEXT NOT NULL,
                stderr TEXT NOT NULL
            )
        """)

        cursor = connection.execute("""
            INSERT INTO sandbox_results (
                timestamp_utc,
                candidate,
                status,
                passed,
                execution_seconds,
                stdout,
                stderr
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            candidate,
            result["status"],
            int(result["passed"]),
            result["seconds"],
            result.get("stdout", ""),
            result.get("stderr", ""),
        ))

        return cursor.lastrowid


def list_sandbox_results(db_path=DB_FILE):
    """Return saved results, newest first."""
    with sqlite3.connect(db_path) as connection:
        return connection.execute("""
            SELECT
                id,
                timestamp_utc,
                candidate,
                status,
                passed,
                execution_seconds
            FROM sandbox_results
            ORDER BY id DESC
        """).fetchall()
