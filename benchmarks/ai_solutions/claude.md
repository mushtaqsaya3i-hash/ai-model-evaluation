import math


def calculate_constrained_average_v2(numbers, minimum, maximum):
    # 0a. Bounds must be real numbers (int or float, not bool).
    for bound in (minimum, maximum):
        if isinstance(bound, bool) or not isinstance(bound, (int, float)):
            raise TypeError("minimum and maximum must be int or float (not bool)")

    # 0b. NaN bounds or an inverted range.
    if minimum != minimum or maximum != maximum or minimum > maximum:
        raise ValueError("invalid range: NaN bound or minimum > maximum")

    deduped = []
    append = deduped.append

    # 0c + 1 + 2 in a single pass: validate every element (including ones that
    # will be filtered out), filter inclusively, and drop consecutive duplicates
    # of the filtered sequence. NaN fails the comparison, so it is dropped.
    for v in numbers:
        t = type(v)
        if t is not int and t is not float:
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise TypeError(f"non-numeric element: {v!r}")
        if minimum <= v <= maximum:
            if not deduped or v != deduped[-1]:
                append(v)

    if not deduped:
        return None

    # 3. Single-pass outlier trim using the population standard deviation.
    n = len(deduped)
    mean = math.fsum(deduped) / n
    std = math.sqrt(math.fsum([(v - mean) ** 2 for v in deduped]) / n)
    limit = 2 * std
    kept = [v for v in deduped if abs(v - mean) <= limit]

    # 4. Mean of what remains (no re-deduplication after trimming).
    if not kept:  # only reachable with infinite inputs, where std is undefined
        return float(mean)
    return math.fsum(kept) / len(kept)