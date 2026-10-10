"""Run every Challenge 2 candidate through Docker, store results, print a markdown table.

Usage (from the repo root):  python -m scripts.run_benchmark [--runs 5] [--timeout 90] [--only no_trim hangs_on_large]
"""
import argparse
from pathlib import Path

from benchmarks.challenge_02_candidates import CANDIDATES
from src.sandbox import run_in_sandbox
from src.sandbox_evaluator import evaluate_in_sandbox, save_benchmark_run

DB_FILE = Path("evaluation_results.db")


def format_markdown_table(rows):
    lines = [
        "| Candidate | Score | Passed | Correctness | Median time (s) | Error type |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for name, r in rows:
        corr = "unknown" if r["correctness"] is None else f"{r['correctness'] * 100:.2f}%"
        secs = "-" if r["performance_seconds"] is None else f"{r['performance_seconds']:.2f}"
        lines.append(
            f"| {name} | {r['score']:.2f}% | {r['passed']}/{r['total']} | {corr} | {secs} | {r['error_type']} |"
        )
    return "\n".join(lines)


def run_all(runner=run_in_sandbox, db_path=DB_FILE, runs=5, timeout=90, names=None,
            runner_label="docker"):
    rows = []
    for name in (names or CANDIDATES):
        report = evaluate_in_sandbox(CANDIDATES[name], runs=runs, timeout=timeout, runner=runner)
        save_benchmark_run(db_path, name, report, runner=runner_label)
        rows.append((name, report))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--only", nargs="*", choices=list(CANDIDATES))
    args = parser.parse_args()
    rows = run_all(runs=args.runs, timeout=args.timeout, names=args.only)
    print(format_markdown_table(rows))


if __name__ == "__main__":
    main()
