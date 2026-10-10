"""Weighted evaluator with failure classification for Challenge 2 v2.

Report keys kept compatible with src.evaluator: score (0-100), passed, total.
New keys: weighted_passed, weighted_total, correctness, performance_ok,
performance_seconds, error_type, case_results.

error_type (highest priority first):
  crash               unexpected exception on a valid input
  wrong_output        returned a wrong value
  validation_failure  did not raise the specified exception on invalid input
  too_slow            correct but exceeded the time limit on the large input
  none                everything passed

NOTE: this runs in-process and cannot stop an infinite loop. Run untrusted
candidates through the Docker sandbox, which enforces the hard timeout.
"""
import math
import sqlite3
import time
from datetime import datetime, timezone

from benchmarks.second_challenge_cases import (
    CASES, ERROR_CASES, GENERATOR_CASES, PERF_LIMIT_SECONDS, PERF_WEIGHT,
    ERROR_CASE_WEIGHT, make_perf_input,
)

PRIORITY = ["crash", "wrong_output", "validation_failure", "too_slow"]


def _run_valid_case(func, case):
    cid, numbers, lo, hi, expected, weight = case
    nums = iter(list(numbers)) if cid in GENERATOR_CASES else list(numbers)
    try:
        result = func(nums, lo, hi)
    except Exception as exc:
        return "crash", expected, None, str(exc)
    if expected is None:
        ok = result is None
    else:
        ok = (isinstance(result, (int, float)) and not isinstance(result, bool)
              and math.isclose(result, expected, abs_tol=1e-9))
    return ("pass" if ok else "wrong_output"), expected, result, None


def _run_error_case(func, case):
    _cid, numbers, lo, hi, exc = case
    try:
        actual = func(list(numbers), lo, hi)
    except exc:
        return "pass", exc.__name__, None, None
    except Exception as other:
        return "validation_failure", exc.__name__, None, f"{type(other).__name__}: {other}"
    return "validation_failure", exc.__name__, actual, "no exception raised"


def evaluate_second_challenge_candidate(func):
    items = []  # (id, weight, status)
    results = []  # same row format as src.evaluator

    def record(cid, weight, outcome):
        status, expected, actual, error = outcome
        items.append((cid, weight, status))
        results.append({"test": cid, "passed": status == "pass", "expected": expected,
                        "actual": actual, "error": error, "status": status, "weight": weight})

    for case in CASES:
        record(case[0], case[5], _run_valid_case(func, case))
    for case in ERROR_CASES:
        record(case[0], ERROR_CASE_WEIGHT, _run_error_case(func, case))

    data = list(make_perf_input())
    start = time.perf_counter()
    try:
        result = func(data, 10, 40)
        elapsed = time.perf_counter() - start
        if result is None or not (10 <= result <= 40):
            perf_status = "wrong_output"
        elif elapsed > PERF_LIMIT_SECONDS:
            perf_status = "too_slow"
        else:
            perf_status = "pass"
    except Exception:
        elapsed = time.perf_counter() - start
        perf_status = "crash"
    record("performance_large_input", PERF_WEIGHT,
           (perf_status, f"<= {PERF_LIMIT_SECONDS}s", round(elapsed, 3), None))

    # Correctness is scored independently from performance. The correctness
    # cases total 53 weighted points; the performance check is a separate gate.
    corr_items = [i for i in items if i[0] != "performance_large_input"]
    weighted_total = sum(w for _, w, _ in corr_items)
    weighted_passed = sum(w for _, w, s in corr_items if s == "pass")
    statuses = {s for _, _, s in items}
    error_type = next((e for e in PRIORITY if e in statuses), "none")
    correctness = weighted_passed / weighted_total if weighted_total else 0.0

    return {
        "score": round(100.0 * weighted_passed / weighted_total, 2) if weighted_total else 0.0,
        # `passed` and `total` count correctness cases only; performance is separate.
        "passed": sum(1 for _, _, s in corr_items if s == "pass"),
        "total": len(corr_items),
        "weighted_passed": weighted_passed,
        "weighted_total": weighted_total,
        "correctness": round(correctness, 4),
        "performance_ok": perf_status == "pass",
        "performance_seconds": round(elapsed, 3),
        "error_type": error_type,
        "case_results": {cid: s for cid, _, s in items},
        "results": results,
    }


def save_weighted_result(db_path, candidate, report, challenge="challenge_02_v2"):
    """Store a report in its own table; existing tables are untouched."""
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weighted_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    challenge TEXT NOT NULL,
                    score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    correctness REAL NOT NULL,
                    performance_ok INTEGER NOT NULL,
                    performance_seconds REAL NOT NULL,
                    error_type TEXT NOT NULL,
                    UNIQUE(timestamp_utc, candidate, challenge)
                )""")
            conn.execute(
                "INSERT INTO weighted_results (timestamp_utc, candidate, challenge, score,"
                " passed, total, correctness, performance_ok, performance_seconds, error_type)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), candidate, challenge,
                 report["score"], report["passed"], report["total"], report["correctness"],
                 int(report["performance_ok"]), report["performance_seconds"],
                 report["error_type"]))
    finally:
        conn.close()


# Backward-compatible API used by the earlier Challenge 2 runner.
def evaluate_candidate(func, performance_seconds=None):
    """Compatibility wrapper; correctness is always evaluated from the cases.

    If performance_seconds is supplied by an external benchmark, it overrides
    the local performance measurement in the returned report.
    """
    report = evaluate_second_challenge_candidate(func)
    if performance_seconds is not None:
        seconds = float(performance_seconds)
        report["performance_seconds"] = round(seconds, 3)
        report["performance_ok"] = seconds <= PERF_LIMIT_SECONDS
        report["case_results"]["performance_large_input"] = (
            "pass" if report["performance_ok"] else "too_slow"
        )
        for row in report["results"]:
            if row["test"] == "performance_large_input":
                row["actual"] = round(seconds, 3)
                row["status"] = report["case_results"]["performance_large_input"]
                row["passed"] = report["performance_ok"]
        if not report["performance_ok"] and report["error_type"] == "none":
            report["error_type"] = "too_slow"
        elif report["performance_ok"] and report["error_type"] == "too_slow":
            report["error_type"] = next(
                (e for e in PRIORITY[:-1] if e in {r["status"] for r in report["results"]}),
                "none",
            )
    return report
