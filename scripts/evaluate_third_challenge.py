
"""Evaluate Challenge 3 candidates, including input-mutation checks."""

from copy import deepcopy

from benchmarks.third_challenge_cases import ALL_THIRD_CHALLENGE_CASES
from benchmarks.third_challenge_candidates import CANDIDATES


def evaluate_candidate(func, cases):
    passed = 0
    failures = []

    for case in cases:
        if case.name == "one_shot_generator":
            args = ((item[:] for item in [[1, 2], [3, 4]]),)
        else:
            args = deepcopy(case.args)

        kwargs = deepcopy(case.kwargs)

        before = (
            deepcopy(args[0])
            if args and isinstance(args[0], list)
            else None
        )

        try:
            result = func(*args, **kwargs)

            if case.expected_exception is not None:
                failures.append(
                    (case.name, "expected exception was not raised")
                )
                continue

            if result != case.expected:
                failures.append((case.name, "wrong result"))
                continue

            if before is not None and args[0] != before:
                failures.append((case.name, "input mutated"))
                continue

            passed += 1

        except Exception as exc:
            if case.expected_exception is not None and isinstance(
                exc, case.expected_exception
            ):
                passed += 1
            else:
                failures.append(
                    (case.name, f"unexpected {type(exc).__name__}")
                )

    return passed, failures


def main():
    cases = ALL_THIRD_CHALLENGE_CASES

    for name, func in CANDIDATES.items():
        passed, failures = evaluate_candidate(func, cases)
        print(f"\n{name}: {passed}/{len(cases)} passed")

        for case_name, reason in failures:
            print(f"  - {case_name}: {reason}")


if __name__ == "__main__":
    main()
