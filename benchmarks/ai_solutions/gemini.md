import math


def calculate_constrained_average_v2(numbers, minimum, maximum):
    # Rule 0.a: minimum and maximum must be real numbers (int or float, but NOT bool)
    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
        raise TypeError("minimum must be an int or float, not bool")
    if isinstance(maximum, bool) or not isinstance(maximum, (int, float)):
        raise TypeError("maximum must be an int or float, not bool")

    # Rule 0.b: neither bound can be NaN, and minimum <= maximum
    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("Bounds must not be NaN, and minimum must be <= maximum")

    # Steps 0.c, 1, and 2: Validate all elements, filter bounds, and consecutive dedup
    # Processed iteratively in a single loop for O(N) performance and minimal allocations.
    deduped = []
    has_prev = False
    prev_val = None

    for x in numbers:
        # Check rule 0.c
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("All elements must be real numbers (int or float, not bool)")

        # Step 1: Filter (NaN comparisons evaluate to False)
        if minimum <= x <= maximum:
            # Step 2: Consecutive dedup
            if not has_prev or x != prev_val:
                deduped.append(float(x))
                prev_val = x
                has_prev = True

    # Rule 4: Return None if nothing remained after step 1 (deduped is also empty in this case)
    n = len(deduped)
    if n == 0:
        return None

    # Step 3: Outlier trim
    # Compute mean (m) and population standard deviation (s)
    m = sum(deduped) / n
    variance = sum((x - m) ** 2 for x in deduped) / n
    s = math.sqrt(variance)
    threshold = 2.0 * s

    # Drop every value whose distance from m is strictly greater than 2 * s
    remaining = [x for x in deduped if abs(x - m) <= threshold]

    # Step 4: Return the arithmetic mean of remaining values
    return sum(remaining) / len(remaining)