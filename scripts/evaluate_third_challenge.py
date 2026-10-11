
"""Evaluate trusted Challenge 3 reference and mutant candidates."""

from benchmarks.third_challenge_cases import (
    ALL_THIRD_CHALLENGE_CASES,
    run_case,
)
from benchmarks.third_challenge_candidates import CANDIDATES


def evaluate_candidate(func, cases):
    passed = 0
    passed_weight = 0
    failures = []
    total_weight = sum(case.weight for case in cases)

    for case in cases:
        outcome = run_case(func, case)

        if outcome.passed:
            passed += 1
            passed_weight += case.weight
        else:
            failures.append((case.name, outcome.reason))

    return {
        "passed": passed,
        "total": len(cases),
        "weighted_passed": passed_weight,
        "weighted_total": total_weight,
        "raw_score": round(100 * passed / len(cases), 2) if cases else 0,
        "weighted_score": (
            round(100 * passed_weight / total_weight, 2)
            if total_weight else 0
        ),
        "failures": failures,
    }


def main():
    cases = ALL_THIRD_CHALLENGE_CASES

    for name, func in CANDIDATES.items():
        report = evaluate_candidate(func, cases)

        print(
            f"\n{name}: "
            f"{report['passed']}/{report['total']} passed | "
            f"raw={report['raw_score']:.2f}% | "
            f"weighted={report['weighted_score']:.2f}% "
            f"({report['weighted_passed']}/{report['weighted_total']} points)"
        )

        for case_name, reason in report["failures"]:
            print(f"  - {case_name}: {reason}")


if __name__ == "__main__":
    main()
