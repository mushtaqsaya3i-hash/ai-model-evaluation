
import pytest

from benchmarks.first_challenge import calculate_average


def test_average_of_positive_numbers():
    assert calculate_average([2, 4, 6]) == 4


def test_average_of_negative_numbers():
    assert calculate_average([-2, -4, -6]) == -4


def test_average_of_decimal_numbers():
    assert calculate_average([1.5, 2.5]) == 2.0


def test_average_of_single_number():
    assert calculate_average([7]) == 7


def test_empty_list_raises_error():
    with pytest.raises(ValueError):
        calculate_average([])


def test_average_of_zero_values():
    assert calculate_average([0, 0, 0]) == 0


def test_average_of_duplicate_values():
    assert calculate_average([5, 5, 5, 5]) == 5


def test_empty_tuple_raises_error():
    with pytest.raises(ValueError):
        calculate_average(())
