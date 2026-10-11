import math
import numbers


def calculate_constrained_average_v2(numbers, minimum, maximum):
    if isinstance(minimum, bool) or not isinstance(minimum, (int, float)):
        raise TypeError("minimum must be an int or float, not bool")
    if isinstance(maximum, bool) or not isinstance(maximum, (int, float)):
        raise TypeError("maximum must be an int or float, not bool")

    if math.isnan(minimum) or math.isnan(maximum) or minimum > maximum:
        raise ValueError("bounds must not be NaN and minimum must not exceed maximum")

    filtered = []
    previous = None
    has_previous = False

    for value in numbers:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("every element must be an int or float, not bool")

        if minimum <= value <= maximum:
            if not has_previous or value != previous:
                filtered.append(value)
                previous = value
                has_previous = True

    if not filtered:
        return None

    count = len(filtered)
    mean = math.fsum(filtered) / count
    variance = math.fsum((value - mean) ** 2 for value in filtered) / count
    stddev = math.sqrt(variance)
    threshold = 2.0 * stddev

    remaining = [
        value for value in filtered
        if abs(value - mean) <= threshold
    ]

    return float(math.fsum(remaining) / len(remaining))