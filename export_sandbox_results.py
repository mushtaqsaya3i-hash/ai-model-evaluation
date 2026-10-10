
"""Export sandbox evaluation records to CSV."""

import csv
import sqlite3
from pathlib import Path

DB_FILE = Path("evaluation_results.db")
CSV_FILE = Path("sandbox_results.csv")


def export_results(db_path=DB_FILE, csv_path=CSV_FILE):
    """Export sandbox results and return the number of records."""
    with sqlite3.connect(db_path) as connection:
        cursor = connection.execute("""
            SELECT
                id,
                timestamp_utc,
                candidate,
                status,
                passed,
                execution_seconds,
                stdout,
                stderr
            FROM sandbox_results
            ORDER BY id
        """)

        rows = cursor.fetchall()
        headers = [column[0] for column in cursor.description]

    with Path(csv_path).open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    return len(rows)


def main():
    count = export_results()
    print(f"Records exported: {count}")
    print(f"CSV saved to: {CSV_FILE.resolve()}")


if __name__ == "__main__":
    main()
