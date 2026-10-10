"""Candidate solutions for Challenge 2 v2, as source strings for the sandbox.

Each mutant is the reference with exactly ONE fault, so its expected score
loss is predictable (e.g. no_trim fails two weight-3 cases = 47/53 = 88.68%).
"""

REFERENCE_SOURCE = '''
import math
from numbers import Real


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
'''

_DEDUP_BLOCK = '''    deduped = []
    for v in values:
        if minimum <= v <= maximum and (not deduped or v != deduped[-1]):
            deduped.append(v)
'''
_TRIM_LINE = "    kept = [v for v in deduped if abs(v - mean) <= 2 * std]\n"


def _mutate(old, new):
    # Fails loudly if the reference text drifts away from the mutation target.
    assert REFERENCE_SOURCE.count(old) == 1, "mutation target not found"
    return REFERENCE_SOURCE.replace(old, new)


CANDIDATES = {
    "reference": REFERENCE_SOURCE,
    # ---- logic mutants: one fault each ---------------------------------
    "no_dedup": _mutate(_DEDUP_BLOCK, '''    deduped = []
    for v in values:
        if minimum <= v <= maximum:
            deduped.append(v)
'''),
    "global_dedup": _mutate(_DEDUP_BLOCK, '''    deduped = []
    for v in values:
        if minimum <= v <= maximum and v not in deduped:
            deduped.append(v)
'''),
    "dedup_before_filter": _mutate(_DEDUP_BLOCK, '''    deduped = []
    prev = object()
    for v in values:
        if v != prev and minimum <= v <= maximum:
            deduped.append(v)
        prev = v
'''),
    "exclusive_bounds": _mutate(_DEDUP_BLOCK, '''    deduped = []
    for v in values:
        if minimum < v < maximum and (not deduped or v != deduped[-1]):
            deduped.append(v)
'''),
    "no_trim": _mutate(_TRIM_LINE, "    kept = deduped\n"),
    "redup_after_trim": _mutate(_TRIM_LINE, '''    kept = []
    for v in deduped:
        if abs(v - mean) <= 2 * std and (not kept or v != kept[-1]):
            kept.append(v)
'''),
    # ---- reliability candidates ----------------------------------------
    # correct answers, but 3.5 s on the 1,000,000-item input -> too_slow
    "slow_correct": _mutate(_DEDUP_BLOCK, '''    if len(values) > 100_000:
        import time
        time.sleep(3.5)
''' + _DEDUP_BLOCK),
    # correct on small inputs, never returns on the large one -> timeout
    "hangs_on_large": _mutate(_DEDUP_BLOCK, '''    if len(values) > 100_000:
        while True:
            pass
''' + _DEDUP_BLOCK),
    # allocates 2 GiB on the large input -> resource_limit in Docker (256 MB cap)
    "memory_bomb": _mutate(_DEDUP_BLOCK, '''    if len(values) > 100_000:
        _hog = bytearray(2 * 1024 ** 3)
''' + _DEDUP_BLOCK),
    "syntax_error": "def calculate_constrained_average_v2(numbers, minimum, maximum)\n    return None\n",
    "always_crashes": "def calculate_constrained_average_v2(numbers, minimum, maximum):\n    raise RuntimeError('boom')\n",
}
