
"""Reference and deliberately faulty candidates for Challenge 3."""

import math

from benchmarks.third_challenge import (
    merge_intervals_v1 as reference,
)


def mutant_no_adjacent_flag(intervals, *, merge_adjacent=False):
    """Bug: ignores merge_adjacent=True."""
    return reference(intervals, merge_adjacent=False)


def mutant_always_adjacent(intervals, *, merge_adjacent=False):
    """Bug: always merges intervals that touch."""
    return reference(intervals, merge_adjacent=True)


def mutant_mutates_input(intervals, *, merge_adjacent=False):
    """Bug: sorts a caller-provided list in place."""
    if isinstance(intervals, list):
        intervals.sort(key=lambda item: item[0])

    return reference(intervals, merge_adjacent=merge_adjacent)


def mutant_loose_validation(intervals, *, merge_adjacent=False):
    """Bug: skips strict scalar validation."""
    parsed = []

    for pair in intervals:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise TypeError("invalid interval")

        start, end = pair

        if start > end:
            raise ValueError("start > end")

        parsed.append([start, end])

    parsed.sort(key=lambda item: (item[0], item[1]))

    merged = []

    for start, end in parsed:
        if not merged:
            merged.append([start, end])
            continue

        last = merged[-1]
        overlaps = (
            start <= last[1]
            if merge_adjacent
            else start < last[1]
        )

        if overlaps:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])

    return merged


def mutant_accepts_any_length(intervals, *, merge_adjacent=False):
    """Bug: accepts intervals containing more than two elements."""
    parsed = []

    for pair in intervals:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            raise ValueError("invalid interval")

        start, end = pair[0], pair[1]

        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, (int, float))
            or not isinstance(end, (int, float))
        ):
            raise TypeError("invalid interval values")

        if (
            (isinstance(start, float) and not math.isfinite(start))
            or (isinstance(end, float) and not math.isfinite(end))
        ):
            raise ValueError("non-finite interval value")

        if start > end:
            raise ValueError("start > end")

        parsed.append([start, end])

    parsed.sort(key=lambda item: (item[0], item[1]))
    merged = []

    for start, end in parsed:
        if not merged:
            merged.append([start, end])
            continue

        last = merged[-1]
        overlaps = (
            start <= last[1]
            if merge_adjacent
            else start < last[1]
        )

        if overlaps:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])

    return merged


CANDIDATES = {
    "reference": reference,
    "mutant_no_adjacent_flag": mutant_no_adjacent_flag,
    "mutant_always_adjacent": mutant_always_adjacent,
    "mutant_mutates_input": mutant_mutates_input,
    "mutant_loose_validation": mutant_loose_validation,
    "mutant_accepts_any_length": mutant_accepts_any_length,
}
