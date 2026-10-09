
from benchmarks.first_challenge import calculate_average
from src.evaluator import evaluate_average_candidate


def main():
    report = evaluate_average_candidate(calculate_average)

    print("\n=== AI MODEL EVALUATION REPORT ===")
    print(f"Score: {report['score']:.2f}%")
    print(f"Passed: {report['passed']}/{report['total']}")
    print("\nIndividual test results:")

    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        print(f"[{status}] {result['test']}")

    print("\n=== EVALUATION COMPLETE ===")


if __name__ == "__main__":
    main()
