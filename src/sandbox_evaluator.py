"""Score Challenge 2 v2 candidates inside the Docker sandbox.

How it works
------------
run_in_sandbox() only returns a status plus raw output, so we append a harness
to the candidate code. The harness runs every case and prints one tagged JSON
line per result (flush=True). The host parses whatever arrived, so partial
results survive a timeout. That is what separates:

  timeout   killed by the wall-clock limit; correctness is None unless every
            correctness case finished before the kill
  too_slow  finished, answers are right, median time over the limit

The harness is built from the SAME sources the in-process evaluator uses
(benchmarks.second_challenge_cases and weighted_evaluator._run_*), so the two
paths cannot drift apart.

score / passed / total cover correctness only (53 weighted points); performance is
reported separately (performance_ok, performance_status, performance_seconds).

error_type values: none | crash | wrong_output | validation_failure | too_slow
                   | timeout | syntax_error | resource_limit | sandbox_error

Limitation: candidate code and harness share one process. The per-run nonce
stops accidental stdout collisions, not a deliberately hostile candidate that
reads main.py. Treat this as a benchmark runner, not a security boundary
beyond Docker's own limits.
"""
import inspect
import json
import sqlite3
import statistics
import uuid
from datetime import datetime, timezone

from benchmarks import second_challenge_cases as cases_mod
from benchmarks.second_challenge_cases import (
    CASES, ERROR_CASES, ERROR_CASE_WEIGHT, PERF_LIMIT_SECONDS,
)
from src import weighted_evaluator as we
from src.sandbox import run_in_sandbox

FUNC_NAME = "calculate_constrained_average_v2"
PERF_ID = "performance_large_input"
PASSTHROUGH_SANDBOX_ERRORS = ("syntax_error", "resource_limit", "sandbox_error")

_HARNESS_BODY = '''
import json, math, statistics, time
__CASES__

__HELPERS__

def emit(kind, **kw):
    print(NONCE + json.dumps(dict(kind=kind, **kw), default=repr), flush=True)

for case in CASES:
    status, expected, actual, error = _run_valid_case(candidate, case)
    emit("case", id=case[0], status=status, expected=expected, actual=actual, error=error)
for case in ERROR_CASES:
    status, expected, actual, error = _run_error_case(candidate, case)
    emit("case", id=case[0], status=status, expected=expected, actual=actual, error=error)

data = make_perf_input()
status, error = "pass", None
for _ in range(RUNS):
    arg = list(data)
    t0 = time.perf_counter()
    try:
        result = candidate(arg, 10, 40)
    except Exception as exc:
        status, error = "crash", str(exc)
        break
    elapsed = time.perf_counter() - t0
    ok = (isinstance(result, (int, float)) and not isinstance(result, bool)
          and 10 <= result <= 40)
    if not ok:
        status = "wrong_output"
        break
    emit("perf_run", seconds=elapsed)
    if elapsed > 2 * PERF_LIMIT_SECONDS:
        break
emit("perf_done", status=status, error=error)
emit("done")
'''


def build_harness(nonce, runs):
    helpers = "\n\n".join(
        inspect.getsource(f) for f in (we._run_valid_case, we._run_error_case)
    )
    body = (_HARNESS_BODY
            .replace("__CASES__", inspect.getsource(cases_mod))
            .replace("__HELPERS__", helpers))
    return (
        f"_HARNESS = {body!r}\n"
        f"_g = {{'candidate': {FUNC_NAME}, 'NONCE': {nonce!r}, 'RUNS': {int(runs)}}}\n"
        "exec(compile(_HARNESS, '<harness>', 'exec'), _g)\n"
    )


def parse_harness_output(stdout, nonce):
    events = []
    for line in stdout.splitlines():
        idx = line.find(nonce)  # tolerate candidate output with no trailing newline
        if idx == -1:
            continue
        try:
            events.append(json.loads(line[idx + len(nonce):]))
        except ValueError:
            continue
    return events


def evaluate_in_sandbox(code, runs=5, timeout=90, runner=run_in_sandbox):
    """Run `code` (must define calculate_constrained_average_v2) and score it."""
    nonce = "@@" + uuid.uuid4().hex + "@@"
    sb = runner(code, build_harness(nonce, runs), timeout=timeout)
    return build_report(sb, parse_harness_output(sb.get("stdout", ""), nonce))


def build_report(sb, events):
    case_events = {e["id"]: e for e in events if e.get("kind") == "case"}
    perf_runs = [e["seconds"] for e in events if e.get("kind") == "perf_run"]
    perf_done = next((e for e in events if e.get("kind") == "perf_done"), None)
    finished = any(e.get("kind") == "done" for e in events)
    timed_out = sb.get("status") == "timeout"

    spec = [(c[0], c[5]) for c in CASES] + [(c[0], ERROR_CASE_WEIGHT) for c in ERROR_CASES]
    all_cases_seen = all(cid in case_events for cid, _ in spec)

    items, results = [], []
    for cid, weight in spec:
        ev = case_events.get(cid)
        status = ev["status"] if ev else "not_run"
        items.append((cid, weight, status))
        results.append({
            "test": cid, "passed": status == "pass", "status": status, "weight": weight,
            "expected": ev["expected"] if ev else None,
            "actual": ev["actual"] if ev else None,
            "error": ev["error"] if ev else None,
        })

    median = statistics.median(perf_runs) if perf_runs else None
    if perf_done is not None:
        pstatus = perf_done["status"]
        if pstatus == "pass" and median is not None and median > PERF_LIMIT_SECONDS:
            pstatus = "too_slow"
    elif timed_out and all_cases_seen:
        pstatus = "timeout"
    else:
        pstatus = "not_run"
    items.append((PERF_ID, 0, pstatus))
    results.append({
        "test": PERF_ID, "passed": pstatus == "pass", "status": pstatus,
        "weight": 0, "expected": f"median <= {PERF_LIMIT_SECONDS}s",
        "actual": round(median, 3) if median is not None else None,
        "error": perf_done["error"] if perf_done else None,
    })

    corr = [i for i in items if i[0] != PERF_ID]
    weighted_total = sum(w for _, w, _ in corr)
    weighted_passed = sum(w for _, w, s in corr if s == "pass")
    correctness = round(weighted_passed / weighted_total, 4) if all_cases_seen else None

    if not finished:
        sstatus = sb.get("status")
        if sstatus == "timeout" or sstatus in PASSTHROUGH_SANDBOX_ERRORS:
            error_type = sstatus
        else:
            error_type = "crash"  # exited or crashed before the harness finished
    else:
        statuses = {s for _, _, s in items}
        error_type = next((e for e in we.PRIORITY if e in statuses), "none")

    provisional_score = round(100.0 * weighted_passed / weighted_total, 2)
    # Do not present a partial score as final when a timeout/crash prevented
    # the full correctness suite from completing. Keep it separately for diagnosis.
    final_score = provisional_score if all_cases_seen else 0.0

    return {
        "score": final_score,
        "provisional_score": provisional_score,
        "passed": sum(1 for _, _, s in corr if s == "pass"),
        "total": len(corr),
        "weighted_passed": weighted_passed,
        "weighted_total": weighted_total,
        "correctness": correctness,
        "performance_ok": pstatus == "pass",
        "performance_status": pstatus,
        "performance_seconds": round(median, 3) if median is not None else None,
        "performance_runs": [round(t, 3) for t in perf_runs],
        "error_type": error_type,
        "sandbox_status": sb.get("status"),
        "sandbox_seconds": sb.get("seconds"),
        "sandbox_stderr": (sb.get("stderr") or "")[-2000:],
        "case_results": {cid: s for cid, _, s in items},
        "results": results,
    }


def save_benchmark_run(db_path, candidate, report, challenge="challenge_02_v2", runner="docker"):
    """Store a run in `benchmark_runs` (correctness/timing may be NULL). Other tables untouched."""
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp_utc TEXT NOT NULL,
                    candidate TEXT NOT NULL,
                    challenge TEXT NOT NULL,
                    runner TEXT NOT NULL,
                    score REAL NOT NULL,
                    passed INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    correctness REAL,
                    performance_ok INTEGER NOT NULL,
                    performance_seconds REAL,
                    performance_runs TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    sandbox_status TEXT,
                    sandbox_seconds REAL,
                    UNIQUE(timestamp_utc, candidate, challenge, runner)
                )""")
            conn.execute(
                "INSERT INTO benchmark_runs (timestamp_utc, candidate, challenge, runner, score,"
                " passed, total, correctness, performance_ok, performance_seconds,"
                " performance_runs, error_type, sandbox_status, sandbox_seconds)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), candidate, challenge, runner,
                 report["score"], report["passed"], report["total"], report["correctness"],
                 int(report["performance_ok"]), report["performance_seconds"],
                 json.dumps(report["performance_runs"]), report["error_type"],
                 report["sandbox_status"], report["sandbox_seconds"]))
    finally:
        conn.close()

