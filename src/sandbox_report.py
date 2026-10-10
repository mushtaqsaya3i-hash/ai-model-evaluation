
"""Summarize stored sandbox evaluation results."""

import sqlite3
from pathlib import Path

DB_FILE = Path("evaluation_results.db")


def get_summary(db_path=DB_FILE):
    """Return overall and per-candidate sandbox statistics."""
    with sqlite3.connect(db_path) as connection:
        overall = connection.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(passed), 0) AS passed,
                COALESCE(ROUND(AVG(passed) * 100, 2), 0)
                    AS pass_rate,
                COALESCE(ROUND(AVG(execution_seconds), 3), 0)
                    AS average_seconds
            FROM sandbox_results
        """).fetchone()

        candidates = connection.execute("""
            SELECT
                candidate,
                COUNT(*) AS evaluations,
                SUM(passed) AS passed,
                ROUND(AVG(passed) * 100, 2) AS pass_rate,
                ROUND(AVG(execution_seconds), 3) AS average_seconds
            FROM sandbox_results
            GROUP BY candidate
            ORDER BY pass_rate DESC, candidate
        """).fetchall()

        failures = connection.execute("""
            SELECT status, COUNT(*)
            FROM sandbox_results
            WHERE passed = 0
            GROUP BY status
            ORDER BY status
        """).fetchall()

    return {
        "overall": overall,
        "candidates": candidates,
        "failures": failures,
    }


def main():
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    report = get_summary()

    total, passed, pass_rate, average_seconds = report["overall"]

    print("\n=== SANDBOX PERFORMANCE REPORT ===")
    print(f"Total evaluations: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Overall pass rate: {pass_rate:.2f}%")
    print(f"Average execution time: {average_seconds:.3f}s")

    print("\n=== CANDIDATE COMPARISON ===")
    for candidate, count, successes, rate, avg_seconds in report["candidates"]:
        print(
            f"{candidate}: {successes}/{count} passed | "
            f"{rate:.2f}% | Average: {avg_seconds:.3f}s"
        )

    print("\n=== FAILURE BREAKDOWN ===")
    if report["failures"]:
        for status, count in report["failures"]:
            print(f"{status}: {count}")
    else:
        print("No failures recorded.")

    print("\n=== REPORT COMPLETE ===")


if __name__ == "__main__":
    main()
