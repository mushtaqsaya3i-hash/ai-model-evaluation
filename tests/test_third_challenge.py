
import pytest

from benchmarks.third_challenge import merge_intervals_v1
from benchmarks.third_challenge_cases import (
    ALL_THIRD_CHALLENGE_CASES,
    run_case,
)


@pytest.mark.parametrize(
    "case",
    ALL_THIRD_CHALLENGE_CASES,
    ids=lambda case: case.name,
)
def test_third_challenge_cases(case):
    outcome = run_case(merge_intervals_v1, case)
    assert outcome.passed, f"{case.name}: {outcome.reason}"


def test_input_is_not_mutated():
    intervals = [[5, 6], [1, 2], [1.5, 4]]
    snapshot = [item[:] for item in intervals]

    result = merge_intervals_v1(intervals)

    assert intervals == snapshot
    assert result == [[1, 4], [5, 6]]
    assert result is not intervals


def test_output_contains_new_interval_lists():
    intervals = [[1, 3], [2, 5]]
    result = merge_intervals_v1(intervals)

    assert result == [[1, 5]]
    assert result[0] is not intervals[0]
    assert result[0] is not intervals[1]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1, [[1, 3]]),
        (0, [[1, 2], [2, 3]]),
        (None, [[1, 2], [2, 3]]),
        ("yes", [[1, 3]]),
        ([], [[1, 2], [2, 3]]),
        ({}, [[1, 2], [2, 3]]),
    ],
)
def test_merge_flag_uses_truthiness(value, expected):
    assert merge_intervals_v1(
        [[1, 2], [2, 3]],
        merge_adjacent=value,
    ) == expected
