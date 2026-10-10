
"""Compare Challenge 2 candidates in the restricted Docker sandbox."""

import json
import re

from src.sandbox import run_in_sandbox
from src.sandbox_results import save_sandbox_result


REFERENCE = r'''
import math
from numbers import Real

def calculate_constrained_average_v2(numbers, minimum, maximum):
    def valid(x):
        return isinstance(x, Real) and not isinstance(x, bool)

    if not valid(minimum) or not valid(maximum):
        raise TypeError("bounds must be real numbers")
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid bounds")

    values = list(numbers)
    for x in values:
        if not valid(x):
            raise TypeError("invalid element")

    seq = []
    for x in values:
        if minimum <= x <= maximum and (not seq or x != seq[-1]):
            seq.append(x)

    if not seq:
        return None

    mean = math.fsum(seq) / len(seq)
    std = math.sqrt(math.fsum((x - mean) ** 2 for x in seq) / len(seq))
    kept = [x for x in seq if abs(x - mean) <= 2 * std]
    return math.fsum(kept) / len(kept)
'''

NO_TRIM = r'''
import math
from numbers import Real

def calculate_constrained_average_v2(numbers, minimum, maximum):
    def valid(x):
        return isinstance(x, Real) and not isinstance(x, bool)
    if not valid(minimum) or not valid(maximum):
        raise TypeError("bounds must be real numbers")
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid bounds")
    values = list(numbers)
    for x in values:
        if not valid(x):
            raise TypeError("invalid element")
    seq = []
    for x in values:
        if minimum <= x <= maximum and (not seq or x != seq[-1]):
            seq.append(x)
    return math.fsum(seq) / len(seq) if seq else None
'''

REDUP_AFTER_TRIM = r'''
import math
from numbers import Real

def calculate_constrained_average_v2(numbers, minimum, maximum):
    def valid(x):
        return isinstance(x, Real) and not isinstance(x, bool)
    if not valid(minimum) or not valid(maximum):
        raise TypeError("bounds must be real numbers")
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid bounds")
    values = list(numbers)
    for x in values:
        if not valid(x):
            raise TypeError("invalid element")
    seq = []
    for x in values:
        if minimum <= x <= maximum and (not seq or x != seq[-1]):
            seq.append(x)
    if not seq:
        return None
    mean = math.fsum(seq) / len(seq)
    std = math.sqrt(math.fsum((x - mean) ** 2 for x in seq) / len(seq))
    kept = []
    for x in seq:
        if abs(x - mean) <= 2 * std and (not kept or x != kept[-1]):
            kept.append(x)
    return math.fsum(kept) / len(kept) if kept else None
'''

SLOW = r'''
import math
from numbers import Real

def calculate_constrained_average_v2(numbers, minimum, maximum):
    def valid(x):
        return isinstance(x, Real) and not isinstance(x, bool)
    if not valid(minimum) or not valid(maximum):
        raise TypeError("bounds must be real numbers")
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid bounds")
    values = list(numbers)
    for x in values:
        if not valid(x):
            raise TypeError("invalid element")
    seq = []
    for x in values:
        if minimum <= x <= maximum and (not seq or x != seq[-1]):
            seq.append(x)
    if not seq:
        return None
    mean = math.fsum(seq) / len(seq)
    std = math.sqrt(math.fsum((x - mean) ** 2 for x in seq) / len(seq))
    kept = [x for x in seq if abs(x - mean) <= 2 * std]
    result = math.fsum(kept) / len(kept)

    # Deliberate O(n^2) workload to test performance enforcement.
    count = 0
    for i in range(len(seq)):
        for j in range(i):
            count += 1
    return result
'''

HARNESS = r'''
import json, math, random, time

CASES = [
    ("basic", [1,2,3], 0,10, 2.0,1),
    ("filter_then_dedup", [5,100,5,7], 0,50, 6.0,3),
    ("nonconsecutive_dups_kept", [1,2,1], 0,10, 4/3,2),
    ("inclusive_bounds", [0,10], 0,10, 5.0,2),
    ("single_value_range", [3,3,3], 3,3, 3.0,2),
    ("negatives", [-5,-5,-1], -10,0, -3.0,2),
    ("int_float_equal", [1,1.0], 0,5, 1.0,2),
    ("empty", [], 0,10, None,1),
    ("all_filtered", [20,30], 0,10, None,1),
    ("nan_dropped", [float("nan"),2], 0,10, 2.0,2),
    ("nan_between_equal", [2,float("nan"),2], 0,10, 2.0,3),
    ("filtered_gap_makes_dups", [4,99,4], 0,10, 4.0,3),
    ("float_accuracy", [0.1,0.2,0.3], 0,1, 0.2,2),
    ("generator_input", [1,2,2,3], 0,5, 2.0,2),
    ("outlier_dropped", [1,2,1,2,1,2,1,2,100], 0,1000, 1.5,3),
    ("no_redup_after_trim", [2,100,2,1,2,1,2,1,2,1], 0,1000, 14/9,3),
    ("small_list_no_trim", [1,100], 0,1000, 50.5,3),
]
ERRORS = [
    ("min_gt_max", [1],5,1,ValueError),
    ("nan_bound", [1],float("nan"),5,ValueError),
    ("bool_bound", [1],True,5,TypeError),
    ("str_bound", [1],"0",5,TypeError),
    ("str_element", [1,"a"],0,10,TypeError),
    ("str_element_out_of_range", [100,"x"],0,10,TypeError),
    ("bool_element", [True,2],0,10,TypeError),
    ("none_element", [None],0,10,TypeError),
]

passed_weight = 0
total_weight = sum(c[5] for c in CASES) + 2 * len(ERRORS)
failures = []
error_type = None

for name, values, lo, hi, expected, weight in CASES:
    try:
        data = iter(values) if name == "generator_input" else list(values)
        actual = calculate_constrained_average_v2(data, lo, hi)
        ok = (actual is None) if expected is None else (
            actual is not None and not isinstance(actual, bool)
            and math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9)
        )
        err = None
    except Exception as exc:
        ok, err = False, type(exc).__name__
        error_type = error_type or err
    if ok:
        passed_weight += weight
    else:
        failures.append(name)

for name, values, lo, hi, expected_exc in ERRORS:
    try:
        calculate_constrained_average_v2(list(values), lo, hi)
        ok, err = False, None
    except Exception as exc:
        err = type(exc).__name__
        ok = isinstance(exc, expected_exc)
    if ok:
        passed_weight += 2
    else:
        failures.append(name)
        error_type = error_type or (
            "expected_" + expected_exc.__name__ if err is None else err
        )

correctness = round(100 * passed_weight / total_weight, 2)
print("CORRECTNESS_JSON=" + json.dumps({
    "correctness": correctness,
    "passed_weight": passed_weight,
    "total_weight": total_weight,
    "failed_cases": failures,
    "error_type": error_type,
}), flush=True)

rng = random.Random(12345)
data = [rng.randint(0,50) for _ in range(1_000_000)]
start = time.perf_counter()
result = calculate_constrained_average_v2(data, 10, 40)
elapsed = time.perf_counter() - start
perf_ok = result is not None and 10 <= result <= 40 and elapsed < 3.0
print("PERFORMANCE_JSON=" + json.dumps({
    "seconds": round(elapsed, 4),
    "limit_seconds": 3.0,
    "passed": perf_ok,
}), flush=True)
'''

CANDIDATES = [
    ("reference", REFERENCE),
    ("mutant_no_trim", NO_TRIM),
    ("mutant_redup_after_trim", REDUP_AFTER_TRIM),
    ("slow_quadratic", SLOW),
]


def parse_json_line(output, prefix):
    for line in output.splitlines():
        if line.startswith(prefix):
            return json.loads(line[len(prefix):])
    return None


def main():
    print("Challenge 2 weighted candidate comparison")
    print("Correctness denominator: 53 points")
    print("Performance limit: 3 seconds")
    print("-" * 65)

    for name, code in CANDIDATES:
        # Four seconds of wall-clock protection; the harness has a 3s
        # performance threshold for the million-item candidate workload.
        report = run_in_sandbox(
            code=code,
            tests=HARNESS,
            timeout=15,
        )

        correctness = parse_json_line(report["stdout"], "CORRECTNESS_JSON=")
        performance = parse_json_line(report["stdout"], "PERFORMANCE_JSON=")

        status = report["status"]
        if status == "timeout":
            error_type = "timeout"
        elif status == "resource_limit":
            error_type = "resource_limit"
        elif status in ("syntax_error", "runtime_error", "sandbox_error"):
            error_type = status
        elif correctness and correctness.get("error_type"):
            error_type = correctness["error_type"]
        else:
            error_type = None

        result = {
            "status": status,
            "correctness": correctness,
            "performance": performance or {
                "seconds": None,
                "limit_seconds": 3.0,
                "passed": False,
            },
            "error_type": error_type,
            "sandbox_seconds": report["seconds"],
        }

        print("\nCandidate:", name)
        print(json.dumps(result, indent=2))

        # Store a summary compatible with the existing SQLite schema.
        stored = {
            "status": status,
            "passed": bool(
                correctness
                and correctness["correctness"] == 100.0
                and performance
                and performance["passed"]
                and status == "pass"
            ),
            "seconds": report["seconds"],
            "stdout": json.dumps(result),
            "stderr": report.get("stderr", ""),
        }
        try:
            record_id = save_sandbox_result(
                "challenge2_" + name,
                stored,
            )
            print("Database record ID:", record_id)
        except Exception as exc:
            print("Database save failed:", type(exc).__name__, str(exc))


if __name__ == "__main__":
    main()
