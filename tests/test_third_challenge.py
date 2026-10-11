
import pytest

from benchmarks.third_challenge import merge_intervals_v1
from benchmarks.third_challenge_cases import (
    ALL_THIRD_CHALLENGE_CASES,
    assert_input_not_mutated,
)


@pytest.mark.parametrize(
    "case",
    ALL_THIRD_CHALLENGE_CASES,
    ids=lambda case: case.name,
)
def test_third_challenge_cases(case):
    if case.expected_exception is not None:
        with pytest.raises(case.expected_exception):
            merge_intervals_v1(*case.args, **case.kwargs)
    else:
        result = merge_intervals_v1(*case.args, **case.kwargs)
        assert result == case.expected



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


def test_invalid_merge_flag():
    for value in (1, 0, None, "yes", [], {}):
        with pytest.raises(TypeError):
            merge_intervals_v1([[1, 2]], merge_adjacent=value)
