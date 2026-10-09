
import csv
import sqlite3
from pathlib import Path

CSV_FILE = Path("evaluation_results.csv")
DB_FILE = Path("evaluation_results.db")


def main():
    if not CSV_FILE.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_FILE}")

    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                candidate TEXT NOT NULL,
                score REAL NOT NULL,
                passed INTEGER NOT NULL,
                total INTEGER NOT NULL,
                UNIQUE(timestamp_utc, candidate)
            )
        """)

        with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = [
                (
                    row["timestamp_utc"],
                    row["candidate"],
                    float(row["score"]),
                    int(row["passed"]),
                    int(row["total"]),
                )
                for row in reader
            ]

        before = connection.total_changes

        connection.executemany("""
            INSERT OR IGNORE INTO evaluation_results
                (timestamp_utc, candidate, score, passed, total)
            VALUES (?, ?, ?, ?, ?)
        """, rows)

        inserted = connection.total_changes - before

        print(f"New records imported: {inserted}")
        print("\n=== AVERAGE SCORE BY CANDIDATE ===")

        results = connection.execute("""
            SELECT
                candidate,
                ROUND(AVG(score), 2) AS average_score,
                COUNT(*) AS evaluations
            FROM evaluation_results
            GROUP BY candidate
            ORDER BY average_score DESC
        """).fetchall()

        for candidate, score, count in results:
            print(
                f"{candidate}: {score:.2f}% "
                f"across {count} evaluations"
            )

        total_records = connection.execute(
            "SELECT COUNT(*) FROM evaluation_results"
        ).fetchone()[0]

        print(f"\nTotal records in database: {total_records}")
        print(f"Database saved to: {DB_FILE.resolve()}")


if __name__ == "__main__":
    main()
