
import csv
import sqlite3

from export_sandbox_results import export_results


def test_csv_export_writes_headers_and_records(tmp_path):
    db_path = tmp_path / "results.db"
    csv_path = tmp_path / "sandbox_results.csv"

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE sandbox_results (
                id INTEGER PRIMARY KEY,
                timestamp_utc TEXT NOT NULL,
                candidate TEXT NOT NULL,
                status TEXT NOT NULL,
                passed INTEGER NOT NULL,
                execution_seconds REAL NOT NULL,
                stdout TEXT NOT NULL,
                stderr TEXT NOT NULL
            )
        """)
        connection.execute("""
            INSERT INTO sandbox_results VALUES
            (1, '2026-10-10T12:00:00+00:00',
             'candidate_a', 'pass', 1, 0.4, '', '')
        """)

    count = export_results(db_path, csv_path)

    assert count == 1
    assert csv_path.exists()

    with csv_path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["candidate"] == "candidate_a"
    assert rows[0]["status"] == "pass"
    assert rows[0]["passed"] == "1"
