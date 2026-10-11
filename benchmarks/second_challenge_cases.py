"""Shared weighted cases for Challenge 2 v2."""

import random

CASES = [

     ("basic", [1, 2, 3], 0, 10, 2.0, 1),
     ("infinite_bound", [1, 2, 3], 0, float("inf"), 2.0, 2),
     ("empty_generator", [], 0, 10, None, 1),
     ("filter_then_dedup", [5, 100, 5, 7], 0, 50, 6.0, 3),
    ("nonconsecutive_dups_kept", [1, 2, 1], 0, 10, 4 / 3, 2),
    ("inclusive_bounds", [0, 10], 0, 10, 5.0, 2),
    ("single_value_range", [3, 3, 3], 3, 3, 3.0, 2),
    ("negatives", [-5, -5, -1], -10, 0, -3.0, 2),
    ("int_float_equal", [1, 1.0], 0, 5, 1.0, 2),
    ("empty", [], 0, 10, None, 1),
    ("all_filtered", [20, 30], 0, 10, None, 1),
    ("nan_dropped", [float("nan"), 2], 0, 10, 2.0, 2),
    ("nan_between_equal", [2, float("nan"), 2], 0, 10, 2.0, 3),
    ("filtered_gap_makes_dups", [4, 99, 4], 0, 10, 4.0, 3),
    ("float_accuracy", [0.1, 0.2, 0.3], 0, 1, 0.2, 2),
    ("generator_input", [1, 2, 2, 3], 0, 5, 2.0, 2),
    ("outlier_dropped", [1, 2, 1, 2, 1, 2, 1, 2, 100], 0, 1000, 1.5, 3),
    ("no_redup_after_trim", [2, 100, 2, 1, 2, 1, 2, 1, 2, 1], 0, 1000, 14 / 9, 3),
    ("small_list_no_trim", [1, 100], 0, 1000, 50.5, 3),
]

ERROR_CASES = [
    ("min_gt_max", [1], 5, 1, ValueError),
    ("nan_bound", [1], float("nan"), 5, ValueError),
    ("bool_bound", [1], True, 5, TypeError),
    ("str_bound", [1], "0", 5, TypeError),
    ("str_element", [1, "a"], 0, 10, TypeError),
    ("str_element_out_of_range", [100, "x"], 0, 10, TypeError),
    ("bool_element", [True, 2], 0, 10, TypeError),
    ("none_element", [None], 0, 10, TypeError),
]
GENERATOR_CASES = {"generator_input", "empty_generator"}
PERF_LIMIT_SECONDS = 3.0
PERF_WEIGHT = 3
ERROR_CASE_WEIGHT = 2


def make_perf_input():
    """Generate the deterministic million-item performance workload."""
    rng = random.Random(12345)
    return [rng.randint(0, 50) for _ in range(1_000_000)]
