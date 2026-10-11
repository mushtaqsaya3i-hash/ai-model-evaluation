
from hypothesis import given, settings, strategies as st

from benchmarks.third_challenge import merge_intervals_v1


finite_number = st.floats(
    allow_nan=False,
    allow_infinity=False,
    width=32,
)

valid_interval = st.tuples(
    finite_number,
    finite_number,
).filter(lambda pair: pair[0] <= pair[1])

interval_lists = st.lists(
    valid_interval,
    min_size=0,
    max_size=20,
)


@settings(max_examples=200, deadline=None)
@given(intervals=interval_lists, adjacent=st.booleans())
def test_output_is_sorted(intervals, adjacent):
    result = merge_intervals_v1(
        [list(item) for item in intervals],
        merge_adjacent=adjacent,
    )

    assert [item[0] for item in result] == sorted(
        item[0] for item in result
    )


@settings(max_examples=200, deadline=None)
@given(intervals=interval_lists, adjacent=st.booleans())
def test_output_intervals_do_not_overlap(intervals, adjacent):
    result = merge_intervals_v1(
        [list(item) for item in intervals],
        merge_adjacent=adjacent,
    )

    for previous, current in zip(result, result[1:]):
        if adjacent:
            assert current[0] > previous[1]
        else:
            assert current[0] >= previous[1]


@settings(max_examples=200, deadline=None)
@given(intervals=interval_lists)
def test_input_is_not_mutated(intervals):
    data = [list(item) for item in intervals]
    snapshot = [item[:] for item in data]

    merge_intervals_v1(data)

    assert data == snapshot


@settings(max_examples=200, deadline=None)
@given(intervals=interval_lists, adjacent=st.booleans())
def test_merging_is_idempotent(intervals, adjacent):
    result = merge_intervals_v1(
        [list(item) for item in intervals],
        merge_adjacent=adjacent,
    )

    result_again = merge_intervals_v1(
        [item[:] for item in result],
        merge_adjacent=adjacent,
    )

    assert result_again == result


@settings(max_examples=200, deadline=None)
@given(intervals=interval_lists, adjacent=st.booleans())
def test_input_order_does_not_change_result(intervals, adjacent):
    data = [list(item) for item in intervals]

    forward = merge_intervals_v1(data, merge_adjacent=adjacent)
    reversed_result = merge_intervals_v1(
        list(reversed(data)),
        merge_adjacent=adjacent,
    )

    assert forward == reversed_result
