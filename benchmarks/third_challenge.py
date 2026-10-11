"""
Challenge 3 reference implementation: merge_intervals_v1.

    merge_intervals_v1(intervals, *, merge_adjacent=False)

SPECIFICATION (this docstring is the spec; give it verbatim to every model)
--------------------------------------------------------------------------
Input
  * `intervals`: any iterable (list, tuple, generator, custom iterable) of
    intervals. Each interval is a list or tuple of exactly two real numbers
    [start, end]. Numbers are int or float, never bool. Both must be FINITE:
    NaN, +inf and -inf are rejected.
  * `merge_adjacent`: keyword-only; treated by truthiness (no type check).

Validation (errors are raised lazily, in iteration order; the FIRST invalid
element encountered decides the exception, and nothing after it is examined)
  1. `intervals` not iterable                        -> TypeError
  Then, for each interval in iteration order, checks run in this order:
  2. interval is not a list or tuple                 -> TypeError
  3. interval length != 2                            -> ValueError
  4. start: bool or non-number                       -> TypeError
            then NaN / +inf / -inf                   -> ValueError
  5. end:   same checks as start (after start passes)
  6. start > end                                     -> ValueError
  Exceptions raised by the iterable itself while iterating propagate
  unchanged. Because validation is lazy, an invalid interval that comes
  BEFORE an iterator failure raises the validation error instead.

Merge semantics
  * Output is a NEW list of NEW [start, end] lists, sorted by start. Output
    intervals never overlap or touch (touching depends on `merge_adjacent`).
  * Two intervals are linked (and therefore merged, transitively) when:
      a) their interiors overlap, i.e. max(starts) < min(ends); or
      b) they are equal (this includes two identical zero-length intervals); or
      c) one is zero-length [p, p] and the other satisfies s <= p < e
         (a point is absorbed by an interval that contains it, treating
         intervals as half-open [s, e) for this purpose); or
      d) merge_adjacent is truthy and they touch: max(starts) == min(ends).
  * Consequences worth noting:
      - [1,2] and [2,3] stay separate by default, merge with merge_adjacent.
      - [1,3] and [3,3] stay separate by default (the point touches the end).
      - Distinct zero-length intervals ([1,1], [2,2]) never merge, even with
        merge_adjacent=True, because they do not touch.
  * Merged end is the maximum end of the group.
  * Empty input returns [].
  * The input (outer iterable and the inner intervals) is never mutated.
"""

import math


def _validate_scalar(x, label):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError(f"{label} must be a real number, got {type(x).__name__}")
    if isinstance(x, float) and not math.isfinite(x):
        raise ValueError(f"{label} must be finite, got {x}")


def merge_intervals_v1(intervals, *, merge_adjacent=False):
    try:
        iterator = iter(intervals)
    except TypeError:
        raise TypeError("intervals must be iterable") from None

    parsed = []
    for idx, pair in enumerate(iterator):
        if not isinstance(pair, (list, tuple)):
            raise TypeError(f"interval #{idx} must be a list or tuple")
        if len(pair) != 2:
            raise ValueError(f"interval #{idx} must have exactly 2 elements")
        start, end = pair
        _validate_scalar(start, f"interval #{idx} start")
        _validate_scalar(end, f"interval #{idx} end")
        if start > end:
            raise ValueError(f"interval #{idx} has start {start} > end {end}")
        parsed.append([start, end])

    if not parsed:
        return []

    parsed.sort(key=lambda iv: (iv[0], iv[1]))

    merged = [list(parsed[0])]
    for start, end in parsed[1:]:
        block = merged[-1]
        if start < block[1]:
            linked = True
        elif start == block[1]:
            # touching; a zero-length block here can only be an equal point
            # or a point sitting at the start of this interval (rules b, c)
            linked = bool(merge_adjacent) or block[0] == block[1]
        else:
            linked = False
        if linked:
            if end > block[1]:
                block[1] = end
        else:
            merged.append([start, end])
    return merged
