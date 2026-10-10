
"""Evaluate model-generated code and persist the result."""

from src.sandbox import run_in_sandbox
from src.sandbox_results import save_sandbox_result


CANDIDATE_NAME = "average_candidate_v1"

CANDIDATE_CODE = """
def calculate_average(numbers):
    if not numbers:
        raise ValueError("numbers must not be empty")
    return sum(numbers) / len(numbers)
"""

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


def main():
    report = run_in_sandbox(
        code=CANDIDATE_CODE,
        tests=TEST_CODE,
        timeout=10,
    )

    record_id = save_sandbox_result(CANDIDATE_NAME, report)

    print("\n=== SANDBOX EVALUATION REPORT ===")
    print(f"Candidate: {CANDIDATE_NAME}")
    print(f"Status: {report['status'].upper()}")
    print(f"Passed: {report['passed']}")
    print(f"Execution time: {report['seconds']} seconds")
    print(f"Database record ID: {record_id}")

    if report["stdout"]:
        print("\nOutput:")
        print(report["stdout"])

    if report["stderr"]:
        print("\nErrors:")
        print(report["stderr"])

    print("\n=== EVALUATION COMPLETE ===")


if __name__ == "__main__":
    main()
