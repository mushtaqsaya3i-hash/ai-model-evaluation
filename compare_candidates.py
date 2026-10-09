
from benchmarks.first_challenge import calculate_average
from src.evaluator import evaluate_average_candidate


def incorrect_average(numbers):
    """Deliberately incorrect candidate for testing."""
    return numbers[0]


def main():
    candidates = {
        "Reference solution": calculate_average,
        "Incorrect solution": incorrect_average,
    }

    print("\n=== CANDIDATE COMPARISON ===")
    print(f"{'Candidate':<24} {'Score':>8} {'Passed':>10}")
    print("-" * 44)

    for name, candidate in candidates.items():
        report = evaluate_average_candidate(candidate)
        passed = f"{report['passed']}/{report['total']}"

        print(
            f"{name:<24} "
            f"{report['score']:>7.2f}% "
            f"{passed:>10}"
        )

    print("\n=== COMPARISON COMPLETE ===")


if __name__ == "__main__":
    main()
