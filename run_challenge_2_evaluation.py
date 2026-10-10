
"""Run the Challenge 2 reference implementation in Docker."""

import json

from benchmarks.second_challenge import calculate_constrained_average_v2
from src.sandbox import run_in_sandbox
from src.sandbox_results import save_sandbox_result


def main():
    # Run the reference implementation and its core behavioral checks
    # inside Docker. This is a smoke test, not the full weighted benchmark.
    candidate_code = """
import math

def calculate_constrained_average_v2(numbers, minimum, maximum):
    from math import fsum, sqrt
    from numbers import Real

    if (
        isinstance(minimum, bool)
        or isinstance(maximum, bool)
        or not isinstance(minimum, Real)
        or not isinstance(maximum, Real)
    ):
        raise TypeError("bounds must be real numbers")

    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid bounds")

    seq = []
    for value in numbers:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("elements must be real numbers")
        if math.isnan(value) or not minimum <= value <= maximum:
            continue
        if not seq or seq[-1] != value:
            seq.append(value)

    if not seq:
        return None

    mean = fsum(seq) / len(seq)
    variance = fsum((x - mean) ** 2 for x in seq) / len(seq)
    std = sqrt(variance)
    kept = [x for x in seq if abs(x - mean) <= 2 * std]

    return fsum(kept) / len(kept) if kept else None
"""

    tests = """
import time
from random import Random

assert calculate_constrained_average_v2([1, 2, 3], 0, 10) == 2.0
assert calculate_constrained_average_v2([5, 100, 5, 7], 0, 50) == 6.0
assert calculate_constrained_average_v2([1, 2, 1], 0, 10) == 4 / 3
assert calculate_constrained_average_v2([], 0, 10) is None

try:
    calculate_constrained_average_v2([True], 0, 10)
except TypeError:
    pass
else:
    raise AssertionError("bool element should raise TypeError")

rng = Random(12345)
data = [rng.randint(0, 50) for _ in range(1_000_000)]
start = time.perf_counter()
result = calculate_constrained_average_v2(data, 10, 40)
elapsed = time.perf_counter() - start
print("PERFORMANCE_SECONDS=" + str(round(elapsed, 4)))
assert result is not None and 10 <= result <= 40
assert elapsed < 3.0, "performance limit exceeded"
"""

    report = run_in_sandbox(
        code=candidate_code,
        tests=tests,
        timeout=10,
    )

    print("=== CHALLENGE 2 DOCKER SMOKE TEST ===")
    print("Status:", report["status"])
    print("Passed:", report["passed"])
    print("Sandbox seconds:", report["seconds"])
    if report["stdout"]:
        print("Output:\n" + report["stdout"])
    if report["stderr"]:
        print("Errors:\n" + report["stderr"])

    # Save using the existing schema; don't alter the database structure yet.
    record_id = save_sandbox_result("challenge_2_reference_smoke_test", report)
    print("Database record ID:", record_id)


if __name__ == "__main__":
    main()
