"""Evaluate saved AI-generated solutions for Challenge 2 v2.

Put each model's raw reply in benchmarks/ai_solutions/<label>.md (or .py/.txt),
e.g. claude_sonnet.md, gpt_x.md. Markdown code fences are stripped automatically,
so the model output is evaluated exactly as produced (no hand edits).
Results are stored as candidate "ai:<label>" in the benchmark_runs table.

Usage (repo root):  python -m scripts.run_ai_solutions [--runs 5] [--timeout 90]
"""
import argparse
import re
from pathlib import Path

from src.sandbox import run_in_sandbox
from src.sandbox_evaluator import FUNC_NAME, evaluate_in_sandbox, save_benchmark_run

SOLUTIONS_DIR = Path("benchmarks/ai_solutions")
DB_FILE = Path("evaluation_results.db")
SUFFIXES = {".py", ".md", ".txt"}
_FENCE = re.compile(r"```[a-zA-Z0-9_+-]*[ \t]*\r?\n(.*?)```", re.DOTALL)


def extract_code(text):
    """Return the code block that defines the target function, else the raw text."""
    blocks = [b for b in _FENCE.findall(text) if FUNC_NAME in b]
    if blocks:
        return max(blocks, key=len)
    return text




def load_solutions(directory=SOLUTIONS_DIR):
    directory = Path(directory)
    solutions = {}

    if not directory.exists():
        return solutions

    for p in sorted(directory.iterdir()):
        if not p.is_file() or p.suffix not in SUFFIXES or p.name == "__init__.py":
            continue

        label = p.stem

        if label in solutions:
            raise ValueError(
                f"Duplicate solution label '{label}': "
                f"multiple files share the same name."
            )

        solutions[label] = extract_code(p.read_text(encoding="utf-8"))

    return solutions


def format_table(rows):
    lines = ["| Model | Score | Passed | Correctness | Median time (s) | Error type |",
             "|---|---:|---:|---:|---:|---|"]
    for label, r in rows:
        corr = "unknown" if r["correctness"] is None else f"{r['correctness'] * 100:.2f}%"
        secs = "-" if r["performance_seconds"] is None else f"{r['performance_seconds']:.2f}"
        lines.append(f"| {label} | {r['score']:.2f}% | {r['passed']}/{r['total']} "
                     f"| {corr} | {secs} | {r['error_type']} |")
    return "\n".join(lines)


def run_solutions(directory=SOLUTIONS_DIR, runner=run_in_sandbox, db_path=DB_FILE,
                  runs=5, timeout=90, runner_label="docker", progress=print):
    rows = []
    solutions = load_solutions(directory)
    for i, (label, code) in enumerate(solutions.items(), 1):
        progress(f"[{i}/{len(solutions)}] evaluating {label} ...")
        report = evaluate_in_sandbox(code, runs=runs, timeout=timeout, runner=runner)
        save_benchmark_run(db_path, f"ai:{label}", report, runner=runner_label)
        progress(f"    -> {report['score']:.2f}% | {report['error_type']}")
        rows.append((label, report))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    if not SOLUTIONS_DIR.exists() or not load_solutions():
        raise SystemExit(f"No solutions found in {SOLUTIONS_DIR}. Save model replies there first.")
    print(format_table(run_solutions(runs=args.runs, timeout=args.timeout)))


if __name__ == "__main__":
    main()
