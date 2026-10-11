
"""Test cases for Challenge 3: merge_intervals_v1."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Case:
    name: str
    tier: str
    args: tuple
    kwargs: dict
    expected: Any
    expected_exception: type | None = None
    notes: str = ""
    weight: int = field(init=False)

    def __post_init__(self):
        self.weight = {"A": 1, "B": 3, "C": 5}[self.tier]


def _one_shot(items):
    yield from items


HAPPY_CASES = [
    Case("single_interval", "A", ([[1, 3]],), {}, [[1, 3]]),
    Case("two_disjoint", "A", ([[1, 2], [5, 6]],), {},
         [[1, 2], [5, 6]]),
    Case("two_overlapping", "A", ([[1, 4], [2, 5]],), {},
         [[1, 5]]),
    Case("already_sorted_merged", "A", ([[1, 5], [2, 3]],), {},
         [[1, 5]]),
    Case("empty_list", "A", ([],), {}, []),
]

ORDERING_CASES = [
    Case("unsorted_input", "B", ([[5, 6], [1, 2], [3, 4]],), {},
         [[1, 2], [3, 4], [5, 6]]),
    Case("nested_inside", "B", ([[1, 10], [3, 4], [5, 6]],), {},
         [[1, 10]]),
    Case("partially_nested", "B", ([[1, 4], [2, 3], [5, 7]],), {},
         [[1, 4], [5, 7]]),
    Case("touching_default", "B", ([[1, 2], [2, 3]],), {},
         [[1, 2], [2, 3]]),
    Case("touching_with_flag", "B", ([[1, 2], [2, 3]],),
         {"merge_adjacent": True}, [[1, 3]]),
    Case("identical_intervals", "B", ([[1, 3], [1, 3], [1, 3]],), {},
         [[1, 3]]),
    Case("tuple_intervals", "B", ([(1, 2), (3, 4)],), {},
         [[1, 2], [3, 4]]),
    Case("mixed_interval_types", "B", ([[1, 2], (2, 3), [4, 5]],), {},
         [[1, 2], [2, 3], [4, 5]]),
    Case("point_intervals", "B", ([[1, 1], [1, 1], [5, 5]],), {},
     [[1, 1], [1, 1], [5, 5]]),
    Case("negative_intervals", "B", ([[-5, -3], [-4, -1]],), {},
         [[-5, -1]]),
    Case("float_intervals", "B", ([[1.5, 2.5], [2.0, 3.0]],), {},
         [[1.5, 3.0]]),
]

VALIDATION_CASES = [
    Case("non_iterable", "B", (42,), {}, None, TypeError),
    Case("interval_not_sequence", "B", ([1, 2, 3],), {}, None, TypeError),
    Case("interval_too_short", "B", ([[1]],), {}, None, ValueError),
    Case("interval_too_long", "B", ([[1, 2, 3]],), {}, None, ValueError),
    Case("reversed_interval", "B", ([[5, 1]],), {}, None, ValueError),
    Case("string_elements", "B", ([["a", "b"]],), {}, None, TypeError),
    Case("none_element", "B", ([[None, 3]],), {}, None, TypeError),
]

ADVERSARIAL_CASES = [
    Case("bool_start", "C", ([[True, 3]],), {}, None, TypeError),
    Case("bool_end", "C", ([[1, False]],), {}, None, TypeError),
    Case("nan_start", "C", ([[float("nan"), 3]],), {}, None, ValueError),
    Case("nan_end", "C", ([[1, float("nan")]],), {}, None, ValueError),
    Case("infinite_start", "C", ([[float("-inf"), 3]],), {},
         None, ValueError),
    Case("infinite_end", "C", ([[1, float("inf")]],), {},
         None, ValueError),
    Case("one_shot_generator", "C",
         (_one_shot([[1, 2], [3, 4]]),), {}, [[1, 2], [3, 4]]),
    Case("merge_adjacent_chain", "C",
         ([[1, 2], [2, 3], [3, 4], [4, 5]],),
         {"merge_adjacent": True}, [[1, 5]]),
    Case("merge_adjacent_with_gap", "C",
         ([[1, 2], [2, 3], [4, 5]],),
         {"merge_adjacent": True}, [[1, 3], [4, 5]]),
    Case("exact_float_touching", "C",
         ([[0.1, 0.2], [0.2, 0.3]],),
         {"merge_adjacent": True}, [[0.1, 0.3]]),
    Case("long_overlap_chain", "C",
         ([[1, 3], [2, 6], [5, 9], [8, 10]],), {}, [[1, 10]]),
    Case("interleaved_sorting", "C",
         ([[5, 8], [1, 4], [2, 3], [6, 7]],), {},
         [[1, 4], [5, 8]]),
    Case("invalid_merge_flag", "C", ([[1, 2]],),
         {"merge_adjacent": 1}, None, TypeError),
]

ALL_THIRD_CHALLENGE_CASES = (
    HAPPY_CASES + ORDERING_CASES + VALIDATION_CASES + ADVERSARIAL_CASES
)


def assert_input_not_mutated(func, case):
    """Return True if a list input remains unchanged after the call."""
    if not case.args or not isinstance(case.args[0], list):
        return True

    original = case.args[0]
    snapshot = [
        list(item) if isinstance(item, (list, tuple)) else item
        for item in original
    ]

    try:
        func(*case.args, **case.kwargs)
    except Exception:
        pass

    return original == snapshot
