from contextlib import closing
import sqlite3
import tempfile
import time
from pathlib import Path

from benchmarks.second_challenge import calculate_constrained_average_v2 as reference
from src.weighted_evaluator import evaluate_second_challenge_candidate, save_weighted_result


def _dedup(seq):
    out = []
    for x in seq:
        if not out or out[-1] != x:
            out.append(x)
    return out


def test_reference_scores_100_percent():
    r = evaluate_second_challenge_candidate(reference)
    assert r["score"] == 100.0
    assert r["passed"] == r["total"] == 25
    assert r["weighted_total"] == 53
    assert r["error_type"] == "none"
    assert r["performance_ok"] is True


def test_crashing_candidate_scores_zero():
    def crashing(numbers, lo, hi):
        raise RuntimeError("boom")
    r = evaluate_second_challenge_candidate(crashing)
    assert r["score"] == 0.0
    assert r["passed"] == 0
    assert r["error_type"] == "crash"


def test_no_trim_candidate_is_wrong_output():
    def no_trim(numbers, lo, hi):
        seq = _dedup([x for x in numbers if lo <= x <= hi])
        return sum(seq) / len(seq) if seq else None
    r = evaluate_second_challenge_candidate(no_trim)
    assert 0 < r["score"] < 100
    assert r["error_type"] == "wrong_output"
    assert r["case_results"]["outlier_dropped"] == "wrong_output"


def test_candidate_without_validation_is_classified():
    def swallow_errors(numbers, lo, hi):
        try:
            return reference(numbers, lo, hi)
        except (TypeError, ValueError):
            return None
    r = evaluate_second_challenge_candidate(swallow_errors)
    assert r["error_type"] == "validation_failure"
    assert r["correctness"] < 1.0


def test_slow_candidate_is_correct_but_too_slow():
    def slow(numbers, lo, hi):
        if hasattr(numbers, "__len__") and len(numbers) > 100_000:
            time.sleep(3.2)
        return reference(numbers, lo, hi)
    r = evaluate_second_challenge_candidate(slow)
    assert r["correctness"] == 1.0
    assert r["performance_ok"] is False
    assert r["error_type"] == "too_slow"
    assert r["score"] == 100.0  # correctness is scored separately from speed


def test_save_weighted_result_keeps_existing_tables():
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "results.db")
        with closing(sqlite3.connect(db)) as conn:
            with conn:
                conn.execute("CREATE TABLE evaluation_results (id INTEGER)")
        report = evaluate_second_challenge_candidate(reference)
        save_weighted_result(db, "reference_solution", report)
        with closing(sqlite3.connect(db)) as conn:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            row = conn.execute("SELECT candidate, score, error_type FROM weighted_results").fetchone()
        assert {"evaluation_results", "weighted_results"} <= tables
        assert row == ("reference_solution", 100.0, "none")
