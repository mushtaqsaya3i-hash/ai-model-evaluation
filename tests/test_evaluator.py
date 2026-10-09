
from benchmarks.first_challenge import calculate_average
from src.evaluator import evaluate_average_candidate


def test_reference_solution_scores_100_percent():
    report = evaluate_average_candidate(calculate_average)

    assert report["score"] == 100.0
    assert report["passed"] == 5
    assert report["total"] == 5


def test_incorrect_solution_gets_lower_score():
    def incorrect_average(numbers):
        return numbers[0]

    report = evaluate_average_candidate(incorrect_average)

    assert report["score"] < 100.0

def test_crashing_candidate_scores_zero():
    def crashing_average(numbers):
        raise RuntimeError("Candidate crashed")

    report = evaluate_average_candidate(crashing_average)

    assert report["score"] == 0.0
    assert report["passed"] == 0
    assert report["total"] == 5
