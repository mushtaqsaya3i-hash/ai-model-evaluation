"""
Reference plus single-fault mutants for merge_intervals_v1.

Every mutant is built from one parametric implementation with exactly one
flag switched on, so each differs from the reference in a single way.
`_build()` with no flags must behave identically to the reference; the test
suite checks that, and checks that every mutant fails at least one case.
"""

import math

from benchmarks.third_challenge import merge_intervals_v1 as reference


def _check_scalar(x, allow_non_finite):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise TypeError("endpoint must be a real number")
    if isinstance(x, float) and not allow_non_finite and not math.isfinite(x):
        raise ValueError("endpoint must be finite")


def _build(*, ignore_flag=False, always_adjacent=False, mutate_input=False,
           loose_validation=False, any_length=False, allow_inf=False,
           overwrite_end=False, no_sort=False, no_point_rule=False,
           eager=False, tuple_output=False):
    def candidate(intervals, *, merge_adjacent=False):
        adj = merge_adjacent
        if ignore_flag:
            adj = False
        if always_adjacent:
            adj = True

        try:
            it = iter(intervals)
        except TypeError:
            raise TypeError("intervals must be iterable") from None
        if eager:
            it = iter(list(it))      # materialises before validating

        parsed = []
        for pair in it:
            if not isinstance(pair, (list, tuple)):
                raise TypeError("interval must be list or tuple")
            if len(pair) != 2 and not (any_length and len(pair) > 2):
                raise ValueError("interval must have 2 elements")
            s, e = pair[0], pair[1]
            if not loose_validation:
                _check_scalar(s, allow_inf)
                _check_scalar(e, allow_inf)
            if s > e:
                raise ValueError("start > end")
            parsed.append([s, e])

        if mutate_input and isinstance(intervals, list):
            intervals.sort(key=lambda iv: iv[0])     # bug: caller's list

        if not parsed:
            return []
        if not no_sort:
            parsed.sort(key=lambda iv: (iv[0], iv[1]))

        merged = [list(parsed[0])]
        for s, e in parsed[1:]:
            block = merged[-1]
            if s < block[1]:
                linked = True
            elif s == block[1]:
                linked = bool(adj) or (not no_point_rule and block[0] == block[1])
            else:
                linked = False
            if linked:
                if overwrite_end or e > block[1]:
                    block[1] = e
            else:
                merged.append([s, e])
        if tuple_output:
            return [tuple(iv) for iv in merged]
        return merged

    return candidate


MUTANTS = {
    "mutant_ignores_merge_adjacent": _build(ignore_flag=True),
    "mutant_always_merges_adjacent": _build(always_adjacent=True),
    "mutant_sorts_input_in_place": _build(mutate_input=True),
    "mutant_no_endpoint_validation": _build(loose_validation=True),
    "mutant_accepts_long_intervals": _build(any_length=True),
    "mutant_accepts_infinity": _build(allow_inf=True),
    "mutant_end_overwrite_not_max": _build(overwrite_end=True),
    "mutant_no_sort": _build(no_sort=True),
    "mutant_no_point_rule": _build(no_point_rule=True),
    "mutant_eager_materialise": _build(eager=True),
    "mutant_tuple_output": _build(tuple_output=True),
}

# Behaviourally identical to the reference; used for differential testing.
CLEAN_REBUILD = _build()

CANDIDATES = {"reference": reference, **MUTANTS}
