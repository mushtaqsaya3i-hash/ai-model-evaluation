
"""Export a comparison report for AI-generated benchmark solutions."""

import csv
import sqlite3
from pathlib import Path
from statistics import mean

DB_FILE = Path("evaluation_results.db")
OUTPUT_FILE = Path("ai_model_comparison.csv")
MODELS = ("ai:claude", "ai:gemini", "ai:gpt")


def export_comparison(db_path=DB_FILE, output_path=OUTPUT_FILE):
    db_path = Path(db_path)
    output_path = Path(output_path)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT candidate, score, passed, total, correctness,
                   performance_seconds, error_type, timestamp_utc
            FROM benchmark_runs
            WHERE candidate IN (?, ?, ?)
              AND challenge = 'challenge_02_v2'
            ORDER BY id
            """,
            MODELS,
        ).fetchall()

    if not rows:
        raise ValueError("No matching AI benchmark results found.")

    grouped = {model: [] for model in MODELS}
    for row in rows:
        grouped[row[0]].append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "model",
        "recorded_runs",
        "latest_score_percent",
        "latest_passed",
        "latest_total",
        "latest_correctness_percent",
        "latest_execution_seconds",
        "average_execution_seconds",
        "latest_error_type",
        "latest_timestamp_utc",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for model in MODELS:
            model_rows = grouped[model]
            if not model_rows:
                continue

            latest = model_rows[-1]
            times = [
                row[5] for row in model_rows
                if row[5] is not None
            ]

            writer.writerow({
                "model": model.removeprefix("ai:"),
                "recorded_runs": len(model_rows),
                "latest_score_percent": round(latest[1], 2),
                "latest_passed": latest[2],
                "latest_total": latest[3],
                "latest_correctness_percent": (
                    None if latest[4] is None
                    else round(latest[4] * 100, 2)
                ),
                "latest_execution_seconds": latest[5],
                "average_execution_seconds": (
                    round(mean(times), 4) if times else None
                ),
                "latest_error_type": latest[6],
                "latest_timestamp_utc": latest[7],
            })

    print(f"Report created: {output_path.resolve()}")
    print(f"Models exported: {sum(bool(grouped[m]) for m in MODELS)}")
    print(f"Database records included: {len(rows)}")


if __name__ == "__main__":
    export_comparison()
