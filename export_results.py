
import csv
from datetime import datetime, timezone
from pathlib import Path

from benchmarks.first_challenge import calculate_average
from src.evaluator import evaluate_average_candidate


def incorrect_average(numbers):
    """Deliberately incorrect candidate for comparison."""
    return numbers[0]


def main():
    candidates = {
        "reference_solution": calculate_average,
        "incorrect_solution": incorrect_average,
    }

    output_file = Path("evaluation_results.csv")
    file_exists = output_file.exists() and output_file.stat().st_size > 0

    with output_file.open("a", newline="", encoding="utf-8") as file:
        fields = [
            "timestamp_utc",
            "candidate",
            "score",
            "passed",
            "total",
        ]

        writer = csv.DictWriter(file, fieldnames=fields)

        if not file_exists:
            writer.writeheader()

        for name, candidate in candidates.items():
            report = evaluate_average_candidate(candidate)

            writer.writerow({
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": name,
                "score": report["score"],
                "passed": report["passed"],
                "total": report["total"],
            })

            print(
                f"{name}: {report['score']:.2f}% "
                f"({report['passed']}/{report['total']})"
            )

    print(f"\nResults saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
