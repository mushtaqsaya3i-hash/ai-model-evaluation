from contextlib import closing
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from benchmarks.challenge_02_candidates import CANDIDATES
from scripts.run_benchmark import format_markdown_table, run_all
from src.sandbox import classify
from src.sandbox_evaluator import (
    build_harness, evaluate_in_sandbox, parse_harness_output, save_benchmark_run,
)


def local_runner(code, tests, timeout=10):
    """Same interface as run_in_sandbox, but a plain local subprocess (no Docker)."""
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code + "\n\n" + tests + "\n", encoding="utf-8")
        start = time.monotonic()
        try:
            r = subprocess.run([sys.executable, "-I", str(script)],
                               capture_output=True, text=True, timeout=timeout)
            status, stdout, stderr = classify(r.returncode, r.stderr), r.stdout, r.stderr
        except subprocess.TimeoutExpired as exc:
            status, stderr = "timeout", f"Execution exceeded {timeout} seconds"
            out = exc.stdout or b""
            stdout = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        return {"status": status, "passed": status == "pass",
                "seconds": round(time.monotonic() - start, 2),
                "stdout": stdout, "stderr": stderr, "output_truncated": False}


def run_local(name, runs=2, timeout=60):
    return evaluate_in_sandbox(CANDIDATES[name], runs=runs, timeout=timeout, runner=local_runner)


# ------------------------------ scoring ------------------------------------
def test_reference_scores_100_percent():
    r = run_local("reference")
    assert r["score"] == 100.0
    assert r["passed"] == r["total"] == 27
    assert r["weighted_total"] == 56
    assert r["correctness"] == 1.0
    assert r["error_type"] == "none"
    assert r["performance_ok"] is True
    assert len(r["performance_runs"]) == 2


def test_no_trim_scores_50_of_56():
    r = run_local("no_trim", runs=1)
    assert r["score"] == 89.29
    assert r["error_type"] == "wrong_output"
    assert r["case_results"]["outlier_dropped"] == "wrong_output"
    assert r["case_results"]["no_redup_after_trim"] == "wrong_output"


def test_redup_after_trim_scores_53_of_56():
    r = run_local("redup_after_trim", runs=1)
    assert r["score"] == 94.64
    failed = [k for k, v in r["case_results"].items() if v != "pass"]
    assert failed == ["no_redup_after_trim"]


@pytest.mark.parametrize("name", ["no_dedup", "global_dedup", "dedup_before_filter",
                                  "exclusive_bounds"])
def test_logic_mutants_are_detected(name):
    r = run_local(name, runs=1)
    assert r["score"] < 100.0
    assert r["error_type"] == "wrong_output"
    assert r["correctness"] < 1.0


def test_always_crashes_scores_zero():
    r = run_local("always_crashes", runs=1)
    assert r["score"] == 0.0
    assert r["error_type"] == "crash"
    assert r["correctness"] == 0.0


# ----------------------- timeout vs too_slow split ---------------------------
def test_slow_correct_candidate_is_too_slow_not_timeout():
    r = run_local("slow_correct", runs=1)
    assert r["error_type"] == "too_slow"
    assert r["correctness"] == 1.0
    assert r["performance_seconds"] > 3.0
    assert r["sandbox_status"] == "pass"
    assert r["score"] == 100.0   # correctness is scored separately from speed
    assert r["performance_status"] == "too_slow"


def test_hang_in_perf_stage_is_timeout_with_known_correctness():
    r = run_local("hangs_on_large", runs=1, timeout=12)
    assert r["error_type"] == "timeout"
    assert r["sandbox_status"] == "timeout"
    assert r["correctness"] == 1.0           # every correctness case finished
    assert r["score"] == 100.0
    assert r["case_results"]["performance_large_input"] == "timeout"
    assert r["performance_ok"] is False


def test_hang_before_harness_means_correctness_unknown():
    code = "def calculate_constrained_average_v2(n, a, b):\n    return None\nwhile True:\n    pass\n"
    r = evaluate_in_sandbox(code, runs=1, timeout=3, runner=local_runner)
    assert r["error_type"] == "timeout"
    assert r["correctness"] is None
    assert r["score"] == 0.0
    assert set(r["case_results"].values()) == {"not_run"}


def test_syntax_error_has_unknown_correctness():
    r = run_local("syntax_error", runs=1)
    assert r["error_type"] == "syntax_error"
    assert r["correctness"] is None
    assert r["score"] == 0.0


def test_early_exit_is_not_scored_as_pass():
    code = ("import sys\n"
            "def calculate_constrained_average_v2(n, a, b):\n    return None\n"
            "sys.exit(0)\n")
    r = evaluate_in_sandbox(code, runs=1, timeout=10, runner=local_runner)
    assert r["sandbox_status"] == "pass"     # exit code 0 ...
    assert r["error_type"] == "crash"        # ... but the harness never finished
    assert r["score"] == 0.0


# ----------------------------- harness safety --------------------------------
def test_fake_result_lines_from_candidate_are_ignored():
    code = (CANDIDATES["always_crashes"]
            + 'print(\'{"kind": "done"}\')\n'
            + 'print(\'{"kind": "case", "id": "basic", "status": "pass"}\')\n')
    r = evaluate_in_sandbox(code, runs=1, timeout=30, runner=local_runner)
    assert r["score"] == 0.0
    assert r["case_results"]["basic"] == "crash"


def test_candidate_may_shadow_harness_names():
    code = CANDIDATES["reference"] + "\nCASES = []\nRUNS = 0\ndef emit(*a, **k): pass\n"
    r = evaluate_in_sandbox(code, runs=1, timeout=60, runner=local_runner)
    assert r["score"] == 100.0


def test_parse_ignores_garbage_and_handles_glued_lines():
    nonce = "@@abc@@"
    out = ("noise\n" + 'partial print' + nonce + '{"kind": "done"}\n'
           + nonce + "not json\n")
    assert parse_harness_output(out, nonce) == [{"kind": "done"}]


def test_harness_embeds_runs_and_nonce():
    h = build_harness("@@n@@", 3)
    assert "'RUNS': 3" in h and "@@n@@" in h


# ----------------------------- storage / script ------------------------------
def test_save_benchmark_run_allows_null_correctness():
    with tempfile.TemporaryDirectory() as d:
        db = str(Path(d) / "r.db")
        with closing(sqlite3.connect(db)) as conn:
            with conn:
                conn.execute("CREATE TABLE sandbox_results (id INTEGER)")
        r = run_local("syntax_error", runs=1)
        save_benchmark_run(db, "syntax_error", r, runner="local")
        with closing(sqlite3.connect(db)) as conn:
            row = conn.execute("SELECT candidate, score, correctness, error_type, runner"
                               " FROM benchmark_runs").fetchone()
            tables = {t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert row == ("syntax_error", 0.0, None, "syntax_error", "local")
        assert "sandbox_results" in tables


def test_run_all_and_markdown_table():
    with tempfile.TemporaryDirectory() as d:
        rows = run_all(runner=local_runner, db_path=Path(d) / "r.db", runs=1, timeout=60,
                       names=["reference", "no_trim"], runner_label="local")
    table = format_markdown_table(rows)
    assert "| reference | 100.00% | 27/27 | 100.00% |" in table
    assert "| no_trim | 89.29% |" in table


# ------------------------- real Docker (skipped if absent) -------------------
def _docker_ready():
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(["docker", "image", "inspect", "python:3.12-slim"],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return False


docker = pytest.mark.skipif(not _docker_ready(), reason="Docker or python:3.12-slim unavailable")


@docker
def test_docker_reference_passes_within_limit():
    r = evaluate_in_sandbox(CANDIDATES["reference"], runs=3, timeout=90)
    assert r["score"] == 100.0 and r["error_type"] == "none"
    assert r["performance_seconds"] < 3.0


@docker
def test_docker_no_trim_matches_expected_score():
    r = evaluate_in_sandbox(CANDIDATES["no_trim"], runs=1, timeout=90)
    assert r["score"] == 89.29


@docker
def test_docker_hang_is_timeout_with_known_correctness():
    r = evaluate_in_sandbox(CANDIDATES["hangs_on_large"], runs=1, timeout=20)
    assert r["error_type"] == "timeout"
    assert r["correctness"] == 1.0


@docker
def test_docker_memory_bomb_hits_resource_limit():
    r = evaluate_in_sandbox(CANDIDATES["memory_bomb"], runs=1, timeout=60)
    assert r["error_type"] == "resource_limit"
