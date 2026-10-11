"""
Independent oracle for merge_intervals_v1.

The oracle shares NO logic with the reference: no sorting, no sweep. It
builds a pairwise "linked" relation straight from the written spec (rules
a-d) and takes connected components with union-find. Then:

  1. every valid hand-written case's expected value must match the oracle;
  2. the reference must match the oracle on ALL small integer inputs (exhaustive)
     and on many seeded random inputs, in shuffled order, for both flag values;
  3. the reference passes every case and every mutant fails at least one.

Works under pytest and as plain functions (see scripts/check_third_challenge.py).
"""

import itertools
import random

from benchmarks.third_challenge import merge_intervals_v1 as reference
from benchmarks.third_challenge_cases import ALL_THIRD_CHALLENGE_CASES, run_case
from benchmarks.third_challenge_candidates import CLEAN_REBUILD, MUTANTS


def _linked(a, b, adjacent):
    lo, hi = max(a[0], b[0]), min(a[1], b[1])
    if lo < hi:                                   # rule (a)
        return True
    if lo > hi:                                   # disjoint
        return False
    if a == b:                                    # rule (b), equal points
        return True
    if adjacent:                                  # rule (d), touching
        return True
    for p, other in ((a, b), (b, a)):             # rule (c), point in [s, e)
        if p[0] == p[1] and other[0] <= p[0] < other[1]:
            return True
    return False


def oracle_merge(intervals, adjacent=False):
    items = [list(iv) for iv in intervals]
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in itertools.combinations(range(len(items)), 2):
        if _linked(items[i], items[j], adjacent):
            parent[find(i)] = find(j)

    groups = {}
    for i, iv in enumerate(items):
        groups.setdefault(find(i), []).append(iv)
    out = [[min(g[0] for g in grp), max(g[1] for g in grp)]
           for grp in groups.values()]
    out.sort()
    return out


def test_valid_cases_match_oracle():
    checked = 0
    for case in ALL_THIRD_CHALLENGE_CASES:
        if case.expected_exception is not None:
            continue
        args = case.make_args()
        adj = bool(case.kwargs.get("merge_adjacent", False))
        want = oracle_merge(list(args[0]), adj)
        assert want == case.expected, (
            f"{case.name}: hand-written expectation {case.expected!r} "
            f"disagrees with oracle {want!r}")
        checked += 1
    assert checked > 30


def test_reference_matches_oracle_exhaustively():
    grid = [[s, e] for s in range(5) for e in range(s, 5)]       # 15 intervals
    total = 0
    for n in range(0, 4):
        for combo in itertools.product(grid, repeat=n):
            for adj in (False, True):
                got = reference([list(iv) for iv in combo], merge_adjacent=adj)
                assert got == oracle_merge(combo, adj), (combo, adj, got)
                total += 1
    assert total > 7000


def test_reference_matches_oracle_random_and_shuffled():
    rng = random.Random(20261011)
    for _ in range(6000):
        n = rng.randint(0, 9)
        data = []
        for _ in range(n):
            s = rng.randint(0, 10)
            data.append([s, s + rng.randint(0, 4)])
        adj = rng.random() < 0.5
        want = oracle_merge(data, adj)
        shuffled = data[:]
        rng.shuffle(shuffled)
        assert reference([list(iv) for iv in data], merge_adjacent=adj) == want
        assert reference([list(iv) for iv in shuffled], merge_adjacent=adj) == want


def test_reference_output_invariants_random():
    rng = random.Random(7)
    for _ in range(3000):
        data = [[s, s + rng.randint(0, 3)]
                for s in (rng.randint(0, 8) for _ in range(rng.randint(0, 8)))]
        adj = rng.random() < 0.5
        out = reference(data, merge_adjacent=adj)
        assert out == sorted(out)
        assert reference(out, merge_adjacent=adj) == out          # idempotent
        for a, b in zip(out, out[1:]):                           # no overlap
            assert a[1] < b[0] or (a[1] == b[0] and not adj), (a, b, adj)


def test_clean_rebuild_equals_reference():
    rng = random.Random(3)
    for _ in range(3000):
        data = [[s, s + rng.randint(0, 3)]
                for s in (rng.randint(0, 8) for _ in range(rng.randint(0, 8)))]
        adj = rng.random() < 0.5
        assert (CLEAN_REBUILD([list(i) for i in data], merge_adjacent=adj)
                == reference([list(i) for i in data], merge_adjacent=adj))


def test_reference_passes_every_case():
    failures = [(c.name, run_case(reference, c).reason)
                for c in ALL_THIRD_CHALLENGE_CASES
                if not run_case(reference, c).passed]
    assert not failures, failures


def test_every_mutant_is_caught():
    survivors = [name for name, fn in MUTANTS.items()
                 if all(run_case(fn, c).passed for c in ALL_THIRD_CHALLENGE_CASES)]
    assert not survivors, f"mutants that pass every case: {survivors}"


def test_case_inputs_are_fresh_per_call():
    for case in ALL_THIRD_CHALLENGE_CASES:
        a, b = case.make_args(), case.make_args()
        if a[0] is None or isinstance(a[0], (int, str, tuple)):
            continue                       # immutable, safe to share
        assert a[0] is not b[0], f"{case.name} shares input between calls"
