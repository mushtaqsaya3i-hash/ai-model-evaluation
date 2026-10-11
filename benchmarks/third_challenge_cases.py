"""
Test cases for merge_intervals_v1 (spec: see benchmarks/third_challenge.py).

Design rules
  * Inputs are built by a FACTORY (`make_args`) that is called once per
    execution, so one-shot generators and mutable lists are never shared
    between runs, models, or cases.
  * A case either expects a return value (`expected`) or an exception
    (`expected_exception`). `None` is never a valid return value, so there is
    no ambiguity between "returns None" and "raises".
  * `check_mutation=True` snapshots the arguments before the call and fails
    the case if they differ afterwards.
  * Tiers: A=1, B=3, C=5 points. Totals are computed, not hard-coded:
    run `python -m scripts.check_third_challenge`.

`run_case` executes in-process. Use it ONLY for trusted code (the reference
and the mutants). AI-generated code must go through your sandbox evaluator.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

WEIGHTS = {"A": 1, "B": 3, "C": 5}
NAN = float("nan")
INF = float("inf")


@dataclass
class Case:
    name: str
    tier: str
    make_args: Callable[[], tuple]
    kwargs: dict = field(default_factory=dict)
    expected: Any = None
    expected_exception: Optional[type] = None
    check_mutation: bool = False
    notes: str = ""

    @property
    def weight(self) -> int:
        return WEIGHTS[self.tier]


def ok(name, tier, make_args, expected, kwargs=None, check_mutation=False, notes=""):
    return Case(name, tier, make_args, kwargs or {}, expected=expected,
                check_mutation=check_mutation, notes=notes)


def err(name, tier, make_args, exc, kwargs=None, notes=""):
    return Case(name, tier, make_args, kwargs or {}, expected_exception=exc,
                notes=notes)


# --- helpers that build fresh one-shot inputs ---

def _gen(items):
    def g():
        for x in items:
            yield x
    return g()


def _bad_then_boom():
    yield [None, 1]            # invalid: TypeError must win over what follows
    raise RuntimeError("boom")


def _ok_then_boom():
    yield [1, 2]
    yield [3, 4]
    raise RuntimeError("boom")


class _Custom:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)


# --- Tier A: happy path ---

HAPPY_CASES = [
    ok("single_interval", "A", lambda: ([[1, 3]],), [[1, 3]]),
    ok("two_disjoint", "A", lambda: ([[1, 2], [5, 6]],), [[1, 2], [5, 6]]),
    ok("two_overlapping", "A", lambda: ([[1, 4], [2, 5]],), [[1, 5]]),
    ok("already_sorted_nested", "A", lambda: ([[1, 5], [2, 3]],), [[1, 5]]),
    ok("empty_list", "A", lambda: ([],), []),
]

# --- Tier B: ordering, nesting, adjacency, containers ---

ORDERING_CASES = [
    ok("unsorted_input", "B", lambda: ([[5, 6], [1, 2], [3, 4]],),
       [[1, 2], [3, 4], [5, 6]]),
    ok("nested_inside", "B", lambda: ([[1, 10], [3, 4], [5, 6]],), [[1, 10]]),
    ok("partially_nested", "B", lambda: ([[1, 4], [2, 3], [5, 7]],),
       [[1, 4], [5, 7]]),
    ok("touching_default_stays_separate", "B", lambda: ([[1, 2], [2, 3]],),
       [[1, 2], [2, 3]]),
    ok("touching_with_flag_merges", "B", lambda: ([[1, 2], [2, 3]],), [[1, 3]],
       kwargs={"merge_adjacent": True}),
    ok("identical_intervals", "B", lambda: ([[1, 3], [1, 3], [1, 3]],),
       [[1, 3]]),
    ok("tuples_as_intervals", "B", lambda: ([(1, 2), (3, 4)],),
       [[1, 2], [3, 4]], notes="Output intervals are lists, not tuples."),
    ok("mixed_list_tuple", "B", lambda: ([[1, 2], (2, 3), [4, 5]],),
       [[1, 2], [2, 3], [4, 5]]),
    ok("outer_tuple_container", "B", lambda: (((1, 3), (2, 4)),), [[1, 4]]),
    ok("negatives", "B", lambda: ([[-5, -3], [-4, -1]],), [[-5, -1]]),
    ok("floats", "B", lambda: ([[1.5, 2.5], [2.0, 3.0]],), [[1.5, 3.0]]),
    ok("huge_ints_keep_precision", "B",
       lambda: ([[10**30, 10**30 + 5], [10**30 + 3, 10**30 + 9]],),
       [[10**30, 10**30 + 9]],
       notes="Catches solutions that round-trip through float."),
    ok("custom_iterable_class", "B", lambda: (_Custom([[3, 4], [1, 2], [2, 3.5]]),),
       [[1, 2], [2, 4]]),
    ok("point_intervals_duplicates_collapse", "B",
       lambda: ([[1, 1], [1, 1], [5, 5]],), [[1, 1], [5, 5]],
       notes="Rule (b): equal zero-length intervals merge."),
    ok("point_inside_interval", "B", lambda: ([[1, 5], [3, 3]],), [[1, 5]]),
]

# --- Tier B: input validation (single fault each) ---

VALIDATION_CASES = [
    err("non_iterable_int", "B", lambda: (42,), TypeError),
    err("none_input", "B", lambda: (None,), TypeError),
    err("flat_list_not_pairs", "B", lambda: ([1, 2, 3],), TypeError),
    err("string_input", "B", lambda: ("ab",), TypeError,
        notes="Elements are str, not list/tuple."),
    err("length_too_short", "B", lambda: ([[1]],), ValueError),
    err("length_too_long", "B", lambda: ([[1, 2, 3]],), ValueError),
    err("start_greater_than_end", "B", lambda: ([[5, 1]],), ValueError),
    err("string_endpoints", "B", lambda: ([["a", "b"]],), TypeError),
    err("none_endpoint", "B", lambda: ([[None, 3]],), TypeError),
]

# --- Tier C: adversarial ---

ADVERSARIAL_CASES = [
    err("bool_start", "C", lambda: ([[True, 3]],), TypeError),
    err("bool_end", "C", lambda: ([[1, False]],), TypeError),
    err("nan_start", "C", lambda: ([[NAN, 3]],), ValueError),
    err("nan_end", "C", lambda: ([[1, NAN]],), ValueError),
    err("neg_inf_start", "C", lambda: ([[-INF, 3]],), ValueError,
        notes="Spec: all endpoints must be finite."),
    err("pos_inf_end", "C", lambda: ([[1, INF]],), ValueError),
    ok("one_shot_generator", "C", lambda: (_gen([[1, 2], [3, 4]]),),
       [[1, 2], [3, 4]]),
    ok("input_not_mutated", "C", lambda: ([[5, 6], [1, 2]],),
       [[1, 2], [5, 6]], check_mutation=True,
       notes="Snapshot is compared after the call; catches in-place sorting."),
    ok("input_not_mutated_when_merging", "C",
       lambda: ([[4, 6], [1, 5], [2, 3]],), [[1, 6]], check_mutation=True,
       notes="Catches solutions that extend the caller's inner lists."),
    ok("adjacent_chain", "C", lambda: ([[1, 2], [2, 3], [3, 4], [4, 5]],),
       [[1, 5]], kwargs={"merge_adjacent": True}),
    ok("adjacent_with_gap", "C", lambda: ([[1, 2], [2, 3], [4, 5]],),
       [[1, 3], [4, 5]], kwargs={"merge_adjacent": True}),
    ok("float_touching_exact", "C", lambda: ([[0.1, 0.2], [0.2, 0.3]],),
       [[0.1, 0.3]], kwargs={"merge_adjacent": True}),
    ok("long_overlap_chain", "C",
       lambda: ([[1, 3], [2, 6], [5, 9], [8, 10]],), [[1, 10]]),
    ok("interleaved_needs_sort", "C",
       lambda: ([[5, 8], [1, 4], [2, 3], [6, 7]],), [[1, 4], [5, 8]]),
    ok("end_must_be_max_not_last", "C", lambda: ([[1, 10], [2, 3]],),
       [[1, 10]], notes="A later, shorter interval must not shrink the end."),
    ok("distinct_points_never_merge", "C",
       lambda: ([[1, 1], [2, 2], [3, 3]],), [[1, 1], [2, 2], [3, 3]],
       kwargs={"merge_adjacent": True}),
    ok("point_at_end_default_separate", "C", lambda: ([[1, 3], [3, 3]],),
       [[1, 3], [3, 3]], notes="Rule (c) needs s <= p < e; p == e fails."),
    ok("point_at_end_with_flag_merges", "C", lambda: ([[1, 3], [3, 3]],),
       [[1, 3]], kwargs={"merge_adjacent": True}),
    ok("point_before_interval_same_start", "C", lambda: ([[1, 1], [1, 3]],),
       [[1, 3]], notes="Point at the start of an interval is absorbed."),
    ok("point_chain_then_interval", "C",
       lambda: ([[0, 1], [1, 1], [1, 3]],), [[0, 1], [1, 3]],
       notes="[1,1] joins [1,3] (rule c) but not [0,1] (touching only)."),
]

# --- Tier C: validation order and lazy iteration ---

ORDER_CASES = [
    err("first_error_type_beats_later_value", "C",
        lambda: ([["a", 1], [NAN, 2]],), TypeError),
    err("first_error_value_beats_later_type", "C",
        lambda: ([[5, 1], [None, 2]],), ValueError),
    err("start_type_checked_before_end_nan", "C",
        lambda: ([[None, NAN]],), TypeError),
    err("length_checked_before_endpoint_types", "C",
        lambda: ([["a", "b", "c"]],), ValueError),
    err("lazy_validation_beats_iterator_failure", "C",
        lambda: (_bad_then_boom(),), TypeError,
        notes="Solutions that call list() first raise RuntimeError instead."),
    err("iterator_exception_propagates_unchanged", "C",
        lambda: (_ok_then_boom(),), RuntimeError),
]

ALL_THIRD_CHALLENGE_CASES = (
    HAPPY_CASES + ORDERING_CASES + VALIDATION_CASES
    + ADVERSARIAL_CASES + ORDER_CASES
)


@dataclass
class Outcome:
    passed: bool
    reason: str = ""


def run_case(func, case: Case) -> Outcome:
    """Run one case in-process against a TRUSTED callable."""
    args = case.make_args()
    snapshot = copy.deepcopy(args) if case.check_mutation else None
    try:
        result = func(*args, **case.kwargs)
    except Exception as exc:  # KeyboardInterrupt etc. still propagate
        if case.expected_exception and isinstance(exc, case.expected_exception):
            return Outcome(True)
        want = (case.expected_exception.__name__ if case.expected_exception
                else repr(case.expected))
        return Outcome(False, f"expected {want}, raised {type(exc).__name__}: {exc}")

    if case.expected_exception is not None:
        return Outcome(False, f"expected {case.expected_exception.__name__}, "
                              f"returned {result!r}")
    if result != case.expected or type(result) is not type(case.expected):
        return Outcome(False, f"expected {case.expected!r}, got {result!r}")
    if not all(type(iv) is list for iv in result):
        return Outcome(False, f"output intervals must be lists, got {result!r}")
    if case.check_mutation and args != snapshot:
        return Outcome(False, f"input mutated: {snapshot!r} -> {args!r}")
    return Outcome(True)
