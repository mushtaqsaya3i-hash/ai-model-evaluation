import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from contextlib import closing

from benchmarks.challenge_02_candidates import CANDIDATES
from scripts.run_ai_solutions import extract_code, format_table, load_solutions, run_solutions
from src.sandbox import classify


def local_runner(code, tests, timeout=10):
    """Same interface as run_in_sandbox, local subprocess instead of Docker."""
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code + "\n\n" + tests + "\n", encoding="utf-8")
        start = time.monotonic()
        try:
            r = subprocess.run([sys.executable, "-I", str(script)],
                               capture_output=True, text=True, timeout=timeout)
            status, stdout, stderr = classify(r.returncode, r.stderr), r.stdout, r.stderr
        except subprocess.TimeoutExpired as exc:
            status, stderr = "timeout", "timeout"
            out = exc.stdout or b""
            stdout = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        return {"status": status, "passed": status == "pass",
                "seconds": round(time.monotonic() - start, 2),
                "stdout": stdout, "stderr": stderr, "output_truncated": False}


def test_extract_code_strips_markdown_fence():
    text = "Here you go:\n```python\ndef calculate_constrained_average_v2(a, b, c):\n    return 1\n```\nDone."
    code = extract_code(text)
    assert code.startswith("def calculate_constrained_average_v2")
    assert "Here you go" not in code and "```" not in code


def test_extract_code_prefers_block_with_target_function():
    text = ("```python\nprint('example')\n```\n"
            "```python\ndef calculate_constrained_average_v2(a, b, c):\n    return 1\n```\n")
    assert "calculate_constrained_average_v2" in extract_code(text)


def test_extract_code_leaves_plain_code_unchanged():
    plain = "def calculate_constrained_average_v2(a, b, c):\n    return 1\n"
    assert extract_code(plain) == plain


def test_run_solutions_scores_and_stores_with_ai_prefix():
    with tempfile.TemporaryDirectory() as d:
        sol = Path(d) / "sols"
        sol.mkdir()
        (sol / "good_model.md").write_text(
            "```python\n" + CANDIDATES["reference"] + "\n```\n", encoding="utf-8")
        (sol / "weak_model.py").write_text(CANDIDATES["no_trim"], encoding="utf-8")
        db = Path(d) / "r.db"
        messages = []
        rows = run_solutions(sol, runner=local_runner, db_path=db, runs=1, timeout=60,
                             runner_label="local", progress=messages.append)
        by_label = dict(rows)
        assert by_label["good_model"]["score"] == 100.0
        assert by_label["weak_model"]["score"] == 88.68
        assert by_label["weak_model"]["error_type"] == "wrong_output"
        with closing(sqlite3.connect(db)) as conn:
            names = {r[0] for r in conn.execute("SELECT candidate FROM benchmark_runs")}
        assert names == {"ai:good_model", "ai:weak_model"}
        assert len(messages) == 4
        assert "| good_model | 100.00% |" in format_table(rows)


def test_load_solutions_ignores_other_files():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "notes.json").write_text("{}", encoding="utf-8")
        (Path(d) / "__init__.py").write_text("", encoding="utf-8")
        assert load_solutions(d) == {}

def test_load_solutions_rejects_duplicate_labels():
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        (folder / "gpt.py").write_text(
            "def calculate_constrained_average_v2(a, b, c):\n    return 1\n",
            encoding="utf-8",
        )
        (folder / "gpt.md").write_text(
            "def calculate_constrained_average_v2(a, b, c):\n    return 2\n",
            encoding="utf-8",
        )

        import pytest
        with pytest.raises(ValueError, match="Duplicate solution label 'gpt'"):
            load_solutions(folder)
