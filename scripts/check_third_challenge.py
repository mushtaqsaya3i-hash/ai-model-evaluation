"""
Measured sanity check for Challenge 3 (replaces guessed mutant scores).

    python -m scripts.check_third_challenge

Prints case/tier/weight totals, then raw and weighted scores for the
reference and each mutant, with the names of the cases each one fails.
Exits non-zero if the reference is not 100% or any mutant survives.
Trusted in-process execution only; never feed AI-generated code through here.
"""

import sys
from collections import Counter

from benchmarks.third_challenge_cases import ALL_THIRD_CHALLENGE_CASES as CASES
from benchmarks.third_challenge_cases import run_case
from benchmarks.third_challenge_candidates import CANDIDATES


def main() -> int:
    tiers = Counter(c.tier for c in CASES)
    total_w = sum(c.weight for c in CASES)
    print(f"cases={len(CASES)}  tiers={dict(sorted(tiers.items()))}  "
          f"weighted_total={total_w}\n")

    bad = 0
    for name, fn in CANDIDATES.items():
        outcomes = [(c, run_case(fn, c)) for c in CASES]
        failed = [c for c, o in outcomes if not o.passed]
        passed_w = sum(c.weight for c, o in outcomes if o.passed)
        raw = (len(CASES) - len(failed)) / len(CASES)
        print(f"{name:34s} raw={raw:6.1%}  weighted={passed_w / total_w:6.1%}  "
              f"failed={len(failed)}")
        for c in failed[:6]:
            print(f"    - [{c.tier}] {c.name}")
        if len(failed) > 6:
            print(f"    ... and {len(failed) - 6} more")
        if name == "reference" and failed:
            bad += 1
        if name != "reference" and not failed:
            print("    !! SURVIVED: add a case that catches this mutant")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
