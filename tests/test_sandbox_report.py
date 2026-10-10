
import sqlite3

from src.sandbox_results import initialize_database, save_sandbox_result
from src.sandbox_report import get_summary


def test_report_summarizes_passes_and_failures(tmp_path):
    db_path = tmp_path / "report.db"
    initialize_database(db_path)

    save_sandbox_result(
        "candidate_a",
        {
            "status": "pass",
            "passed": True,
            "seconds": 0.4,
            "stdout": "",
            "stderr": "",
        },
        db_path,
    )

    save_sandbox_result(
        "candidate_b",
        {
            "status": "wrong_output",
            "passed": False,
            "seconds": 0.6,
            "stdout": "",
            "stderr": "AssertionError",
        },
        db_path,
    )

    report = get_summary(db_path)

    assert report["overall"] == (2, 1, 50.0, 0.5)
    assert len(report["candidates"]) == 2
    assert report["failures"] == [("wrong_output", 1)]


def test_report_handles_empty_database(tmp_path):
    db_path = tmp_path / "empty.db"
    initialize_database(db_path)

    report = get_summary(db_path)

    assert report["overall"] == (0, 0, 0, 0)
    assert report["candidates"] == []
    assert report["failures"] == []
