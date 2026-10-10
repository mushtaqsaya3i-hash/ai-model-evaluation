
import sqlite3

from src.sandbox_results import (
    initialize_database,
    list_sandbox_results,
    save_sandbox_result,
)


def test_save_and_read_sandbox_result(tmp_path):
    db_path = tmp_path / "test_results.db"

    initialize_database(db_path)

    result = {
        "status": "pass",
        "passed": True,
        "seconds": 0.42,
        "stdout": "",
        "stderr": "",
    }

    record_id = save_sandbox_result(
        "average_candidate_v1",
        result,
        db_path,
    )

    assert record_id == 1

    rows = list_sandbox_results(db_path)

    assert len(rows) == 1
    assert rows[0][2] == "average_candidate_v1"
    assert rows[0][3] == "pass"
    assert rows[0][4] == 1
    assert rows[0][5] == 0.42


def test_existing_database_tables_are_preserved(tmp_path):
    db_path = tmp_path / "existing.db"

    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE evaluation_results (
                id INTEGER PRIMARY KEY,
                candidate TEXT
            )
        """)

    initialize_database(db_path)

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
            """)
        }

    assert "evaluation_results" in tables
    assert "sandbox_results" in tables
