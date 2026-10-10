
"""Run multiple candidate solutions against the same benchmark."""

from src.sandbox import run_in_sandbox
from src.sandbox_results import save_sandbox_result


TEST_CODE = """
assert calculate_average([2, 4, 6]) == 4
assert calculate_average([-2, -4, -6]) == -4
assert calculate_average([1.5, 2.5]) == 2.0
assert calculate_average([7]) == 7

try:
    calculate_average([])
except ValueError:
    pass
else:
    raise AssertionError("Empty list should raise ValueError")
"""

CANDIDATES = {
    "candidate_correct": """
def calculate_average(numbers):
    if not numbers:
        raise ValueError("numbers must not be empty")
    return sum(numbers) / len(numbers)
""",
    "candidate_wrong": """
def calculate_average(numbers):
    return sum(numbers)
""",
    "candidate_runtime_error": """
def calculate_average(numbers):
    return unknown_function(numbers)
""",
}


def main():
    results = []

    print("\\n=== BATCH EVALUATION REPORT ===")

    for name, code in CANDIDATES.items():
        report = run_in_sandbox(
            code=code,
            tests=TEST_CODE,
            timeout=10,
        )

        record_id = save_sandbox_result(name, report)

        results.append((name, report, record_id))

        print(
            f"{name}: {report['status'].upper()} | "
            f"{report['seconds']:.2f}s | "
            f"DB record: {record_id}"
        )

    passed = sum(report["passed"] for _, report, _ in results)
    total = len(results)
    pass_rate = passed / total * 100 if total else 0

    print("\\n=== SUMMARY ===")
    print(f"Candidates evaluated: {total}")
    print(f"Candidates passed: {passed}")
    print(f"Candidates failed: {total - passed}")
    print(f"Pass rate: {pass_rate:.2f}%")
    print("\\n=== BATCH COMPLETE ===")


if __name__ == "__main__":
    main()
