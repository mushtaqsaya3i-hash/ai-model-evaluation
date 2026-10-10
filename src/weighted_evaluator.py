
"""Weighted scoring for Challenge 2 v2."""

import math
import time
from collections.abc import Iterable
from numbers import Real

from benchmarks.second_challenge_cases import CASES, ERROR_CASES


def _matches(actual, expected):
    """Compare numeric results while handling None and NaN safely."""
    if expected is None:
        return actual is None

    if actual is None or isinstance(actual, bool):
        return False

    if not isinstance(actual, Real):
        return False

    return math.isclose(
        float(actual),
        float(expected),
        rel_tol=0.0,
        abs_tol=1e-9,
    )


def evaluate_candidate(func, performance_seconds=None):
    """Evaluate a candidate function and calculate its weighted score.

    This function is intended to run inside the Docker sandbox, not directly
    against untrusted candidate code in the main Python process.
    """
    total_weight = sum(case[5] for case in CASES)
    passed_weight = 0
    case_results = []
    error_type = None

    for case_id, numbers, minimum, maximum, expected, weight in CASES:
        # Recreate the generator case for each execution.
        values = (
            iter([1, 2, 2, 3])
            if case_id == "generator_input"
            else list(numbers)
        )

        try:
            actual = func(values, minimum, maximum)
            passed = _matches(actual, expected)
            error = None
        except Exception as exc:
            passed = False
            error = type(exc).__name__
            error_type = error_type or error

        if passed:
            passed_weight += weight

        case_results.append({
            "case_id": case_id,
            "weight": weight,
            "passed": passed,
            "error_type": error,
        })

    error_results = []

    for case_id, numbers, minimum, maximum, expected_exception in ERROR_CASES:
        try:
            func(list(numbers), minimum, maximum)
            passed = False
            error = None
        except Exception as exc:
            passed = isinstance(exc, expected_exception)
            error = type(exc).__name__

        if not passed:
            error_type = error_type or (
                f"expected_{expected_exception.__name__}"
                if error is None
                else error
            )

        error_results.append({
            "case_id": case_id,
            "weight": 2,
            "passed": passed,
            "error_type": error,
        })

    error_weight = sum(item["weight"] for item in error_results)
    passed_error_weight = sum(
        item["weight"] for item in error_results if item["passed"]
    )

    combined_weight = total_weight + error_weight
    combined_passed_weight = passed_weight + passed_error_weight

    correctness = (
        100.0 * combined_passed_weight / combined_weight
        if combined_weight
        else 0.0
    )

    performance_ok = (
        performance_seconds is not None
        and performance_seconds < 3.0
    )

    return {
        "score": round(correctness, 2),
        "correctness": round(correctness, 2),
        "performance": {
            "seconds": performance_seconds,
            "limit_seconds": 3.0,
            "passed": performance_ok,
        },
        "performance_ok": performance_ok,
        "error_type": error_type,
        "passed_weight": combined_passed_weight,
        "total_weight": combined_weight,
        "cases": case_results,
        "error_cases": error_results,
    }
