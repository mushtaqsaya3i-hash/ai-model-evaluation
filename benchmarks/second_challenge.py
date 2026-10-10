"""Challenge 2 (v2): Constrained average with validation, dedup and outlier trimming.

Difficulty: medium-hard
Categories: filtering, state/ordering, numeric edge cases, validation
Time limit: 3 s for 1,000,000 items (rules out O(n^2) approaches)

Function signature
------------------
    calculate_constrained_average_v2(numbers, minimum, maximum)

Rules (apply in EXACTLY this order)
-----------------------------------
0. Validation
   a. `minimum` and `maximum` must be real numbers (int/float, NOT bool),
      otherwise raise TypeError.
   b. If either bound is NaN, or minimum > maximum, raise ValueError.
   c. `numbers` is any iterable. EVERY element must be a real number
      (int/float, NOT bool), otherwise raise TypeError. This applies to
      all elements, including ones that would later be filtered out.
      NaN elements are valid numbers.
1. Filter: keep values with minimum <= value <= maximum (inclusive).
   NaN fails every comparison, so it is dropped here.
2. Consecutive dedup: on the FILTERED sequence, drop a value if it equals
   the previous kept value (1 == 1.0). Non-consecutive repeats stay.
   Order is preserved.
3. Outlier trim (single pass): let m be the mean and s the POPULATION
   standard deviation of the deduplicated values. Drop every value whose
   distance from m is strictly greater than 2 * s. Do NOT dedup again
   after trimming (values that become adjacent stay as they are).
4. Return the arithmetic mean of the remaining values as a float.
   Return None if nothing remained after step 1 (step 3 never empties a
   non-empty list).

Floating-point: graders compare with abs tolerance 1e-9.
"""
import math
from numbers import Real

FUNC_NAME = "calculate_constrained_average_v2"


def _is_number(x):
    return isinstance(x, Real) and not isinstance(x, bool)


def calculate_constrained_average_v2(numbers, minimum, maximum):
    if not _is_number(minimum) or not _is_number(maximum):
        raise TypeError("minimum and maximum must be real numbers")
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("invalid range")

    values = list(numbers)
    for v in values:
        if not _is_number(v):
            raise TypeError(f"non-numeric element: {v!r}")

    deduped = []
    for v in values:
        if minimum <= v <= maximum and (not deduped or v != deduped[-1]):
            deduped.append(v)

    if not deduped:
        return None

    n = len(deduped)
    mean = math.fsum(deduped) / n
    std = math.sqrt(math.fsum((v - mean) ** 2 for v in deduped) / n)
    kept = [v for v in deduped if abs(v - mean) <= 2 * std]
    return math.fsum(kept) / len(kept)
