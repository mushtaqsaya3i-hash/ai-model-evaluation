
def evaluate_average_candidate(candidate):
    """Evaluate a trusted candidate function against benchmark cases."""

    test_cases = [
        ("positive_numbers", [2, 4, 6], 4),
        ("negative_numbers", [-2, -4, -6], -4),
        ("decimal_numbers", [1.5, 2.5], 2.0),
        ("single_number", [7], 7),
    ]

    results = []

    for name, numbers, expected in test_cases:
        try:
            actual = candidate(numbers)
            passed = actual == expected
            error = None
        except Exception as exc:
            passed = False
            actual = None
            error = str(exc)

        results.append({
            "test": name,
            "passed": passed,
            "expected": expected,
            "actual": actual,
            "error": error,
        })

    try:
        candidate([])
        empty_list_passed = False
        empty_list_error = None
    except ValueError:
        empty_list_passed = True
        empty_list_error = None
    except Exception as exc:
        empty_list_passed = False
        empty_list_error = str(exc)

    results.append({
        "test": "empty_list",
        "passed": empty_list_passed,
        "expected": "ValueError",
        "actual": None,
        "error": empty_list_error,
    })

    passed_count = sum(result["passed"] for result in results)
    total_count = len(results)

    return {
        "score": round(passed_count / total_count * 100, 2),
        "passed": passed_count,
        "total": total_count,
        "results": results,
    }
