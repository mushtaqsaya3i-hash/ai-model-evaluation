
"""Reference implementation for Challenge 3: merge_intervals_v1."""

import math


def _validate_scalar(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(
            f"{label} must be a real number, got {type(value).__name__}"
        )

    if isinstance(value, float):
        if math.isnan(value):
            raise ValueError(f"{label} must not be NaN")
        if not math.isfinite(value):
            raise ValueError(f"{label} must be finite")


def merge_intervals_v1(intervals, *, merge_adjacent=False):
    """Return sorted, merged intervals without mutating the input."""
    if not isinstance(merge_adjacent, bool):
        raise TypeError("merge_adjacent must be a bool")

    try:
        iterator = iter(intervals)
    except TypeError:
        raise TypeError("intervals must be iterable") from None

    parsed = []

    for idx, pair in enumerate(iterator):
        if not isinstance(pair, (list, tuple)):
            raise TypeError(f"interval #{idx} must be a list or tuple")

        if len(pair) != 2:
            raise ValueError(
                f"interval #{idx} must have exactly 2 elements"
            )

        start, end = pair
        _validate_scalar(start, f"interval #{idx} start")
        _validate_scalar(end, f"interval #{idx} end")

        if start > end:
            raise ValueError(f"interval #{idx} has start > end")

        parsed.append([start, end])

    if not parsed:
        return []

    parsed.sort(key=lambda interval: (interval[0], interval[1]))
    merged = [parsed[0][:]]

    for start, end in parsed[1:]:
        last = merged[-1]

        overlaps = (
            start <= last[1]
            if merge_adjacent
            else start < last[1]
        )

        if overlaps:
            if end > last[1]:
                last[1] = end
        else:
            merged.append([start, end])

    return merged
