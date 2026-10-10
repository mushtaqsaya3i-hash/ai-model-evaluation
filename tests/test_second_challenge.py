"""Tests for Challenge 2 v2.

Run against the reference:      pytest test_challenge_02_v2.py
Run against a candidate module: CANDIDATE=candidate_module pytest test_challenge_02_v2.py
(the candidate module must expose calculate_constrained_average_v2)
"""
import importlib
import math
import os
import random
import time

import pytest

FUNC = "calculate_constrained_average_v2"
NAN = float("nan")


def _load():
    module = importlib.import_module(os.environ.get("CANDIDATE", "benchmarks.second_challenge"))
    return getattr(module, FUNC)


fn = _load()

# (id, numbers, minimum, maximum, expected, weight)
# weight: 1 = visible/basic, 2 = hidden edge case, 3 = hidden adversarial
CASES = [
    ("basic", [1, 2, 3], 0, 10, 2.0, 1),
    ("filter_then_dedup", [5, 100, 5, 7], 0, 50, 6.0, 3),
    ("nonconsecutive_dups_kept", [1, 2, 1], 0, 10, 4 / 3, 2),
    ("inclusive_bounds", [0, 10], 0, 10, 5.0, 2),
    ("single_value_range", [3, 3, 3], 3, 3, 3.0, 2),
    ("negatives", [-5, -5, -1], -10, 0, -3.0, 2),
    ("int_float_equal", [1, 1.0], 0, 5, 1.0, 2),
    ("empty", [], 0, 10, None, 1),
    ("all_filtered", [20, 30], 0, 10, None, 1),
    ("nan_dropped", [NAN, 2], 0, 10, 2.0, 2),
    ("nan_between_equal", [2, NAN, 2], 0, 10, 2.0, 3),
    ("filtered_gap_makes_dups", [4, 99, 4], 0, 10, 4.0, 3),
    ("float_accuracy", [0.1, 0.2, 0.3], 0, 1, 0.2, 2),
    ("generator_input", iter([1, 2, 2, 3]), 0, 5, 2.0, 2),
    # outlier trimming: 100 is >2 std from the mean and must be dropped
    ("outlier_dropped", [1, 2, 1, 2, 1, 2, 1, 2, 100], 0, 1000, 1.5, 3),
    # after trimming 100 the two 2s become adjacent; they must NOT be re-deduped
    ("no_redup_after_trim", [2, 100, 2, 1, 2, 1, 2, 1, 2, 1], 0, 1000, 14 / 9, 3),
    ("small_list_no_trim", [1, 100], 0, 1000, 50.5, 3),
]

ERROR_CASES = [
    ("min_gt_max", [1], 5, 1, ValueError),
    ("nan_bound", [1], NAN, 5, ValueError),
    ("bool_bound", [1], True, 5, TypeError),
    ("str_bound", [1], "0", 5, TypeError),
    ("str_element", [1, "a"], 0, 10, TypeError),
    ("str_element_out_of_range", [100, "x"], 0, 10, TypeError),
    ("bool_element", [True, 2], 0, 10, TypeError),
    ("none_element", [None], 0, 10, TypeError),
]


def _check(func, case):
    _id, numbers, lo, hi, expected, _w = case
    # generators are single-use, so rebuild per call
    nums = list(numbers) if not hasattr(numbers, "__next__") else iter([1, 2, 2, 3])
    result = func(nums, lo, hi)
    if expected is None:
        return result is None
    return result is not None and math.isclose(result, expected, abs_tol=1e-9)


@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_cases(case):
    assert _check(fn, case), case[0]


@pytest.mark.parametrize("case", ERROR_CASES, ids=[c[0] for c in ERROR_CASES])
def test_errors(case):
    _id, numbers, lo, hi, exc = case
    with pytest.raises(exc):
        fn(numbers, lo, hi)


def test_does_not_mutate_input():
    data = [1, 1, 2, 100]
    fn(data, 0, 1000)
    assert data == [1, 1, 2, 100]


def test_performance_large_input():
    rng = random.Random(12345)
    data = [rng.randint(0, 50) for _ in range(1_000_000)]
    start = time.perf_counter()
    result = fn(data, 10, 40)
    elapsed = time.perf_counter() - start
    assert result is not None and 10 <= result <= 40
    assert elapsed < 3.0, f"too slow: {elapsed:.2f}s"


def test_property_matches_oracle():
    """Random cross-check against an independent, deliberately simple oracle."""
    rng = random.Random(2024)
    for _ in range(500):
        data = [rng.randint(-20, 20) for _ in range(rng.randint(0, 40))]
        lo = rng.randint(-25, 5)
        hi = rng.randint(lo, 25)
        assert _close(fn(data, lo, hi), _oracle(data, lo, hi)), (data, lo, hi)


def _oracle(data, lo, hi):
    seq = []
    for x in data:
        if lo <= x <= hi:
            if not seq or seq[-1] != x:
                seq.append(x)
    if not seq:
        return None
    m = sum(seq) / len(seq)
    var = sum((x - m) ** 2 for x in seq) / len(seq)
    keep = [x for x in seq if (x - m) ** 2 <= 4 * var + 1e-12]
    return sum(keep) / len(keep)


def _close(a, b):
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, abs_tol=1e-6)


# ---- Mutation check: proves the tests catch typical wrong solutions --------
def _mutant_no_dedup(nums, lo, hi):
    seq = [x for x in nums if lo <= x <= hi]
    return _tail(seq)


def _mutant_global_dedup(nums, lo, hi):
    seen, seq = set(), []
    for x in nums:
        if lo <= x <= hi and x not in seen:
            seen.add(x)
            seq.append(x)
    return _tail(seq)


def _mutant_dedup_before_filter(nums, lo, hi):
    d = [x for i, x in enumerate(nums) if i == 0 or x != nums[i - 1]]
    return _tail([x for x in d if lo <= x <= hi])


def _mutant_exclusive_bounds(nums, lo, hi):
    return _tail(_dedup([x for x in nums if lo < x < hi]))


def _mutant_no_trim(nums, lo, hi):
    seq = _dedup([x for x in nums if lo <= x <= hi])
    return sum(seq) / len(seq) if seq else None


def _mutant_redup_after_trim(nums, lo, hi):
    seq = _dedup([x for x in nums if lo <= x <= hi])
    if not seq:
        return None
    m = sum(seq) / len(seq)
    s = math.sqrt(sum((x - m) ** 2 for x in seq) / len(seq))
    kept = _dedup([x for x in seq if abs(x - m) <= 2 * s])
    return sum(kept) / len(kept)


def _dedup(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x:
            out.append(x)
    return out


def _tail(seq):
    """Dedup (unless caller already did) + trim + mean, shared by mutants."""
    if not seq:
        return None
    m = sum(seq) / len(seq)
    s = math.sqrt(sum((x - m) ** 2 for x in seq) / len(seq))
    kept = [x for x in seq if abs(x - m) <= 2 * s]
    return sum(kept) / len(kept)


MUTANTS = [
    _mutant_no_dedup,
    _mutant_global_dedup,
    _mutant_dedup_before_filter,
    _mutant_exclusive_bounds,
    _mutant_no_trim,
    _mutant_redup_after_trim,
]


@pytest.mark.parametrize("mutant", MUTANTS, ids=[m.__name__ for m in MUTANTS])
def test_suite_catches_mutant(mutant):
    failed = False
    for case in CASES:
        try:
            if not _check(mutant, case):
                failed = True
                break
        except Exception:
            failed = True
            break
    assert failed, f"test suite did not detect {mutant.__name__}"
