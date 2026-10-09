
# AI Model Evaluation Benchmark

A Python project for evaluating candidate coding solutions using
automated tests, scoring, candidate comparison, CSV exports, and SQL analytics.

## Project Goals

- Evaluate candidate implementations against defined test cases.
- Measure functional correctness using pass rates.
- Compare correct, incorrect, and crashing candidates.
- Export evaluation records to CSV.
- Store and analyse results using SQLite.

## Current Benchmark

The first challenge evaluates a function that calculates the arithmetic
mean of a non-empty list of numbers.

The test suite covers:
- Positive and negative numbers
- Decimal values
- A single number
- Zero and duplicate values
- Empty lists and tuples

## Project Structure

```text
ai-model-evaluation/
├── benchmarks/
│   └── first_challenge.py
├── src/
│   └── evaluator.py
├── tests/
│   ├── test_evaluator.py
│   └── test_first_challenge.py
├── run_evaluation.py
├── compare_candidates.py
├── export_results.py
├── load_results.py
├── evaluation_results.csv
└── evaluation_results.db
```

## Setup

Create and activate a Python virtual environment, then install pytest:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pytest
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Run an Evaluation

```powershell
.\.venv\Scripts\python.exe run_evaluation.py
```

## Compare Candidates

```powershell
.\.venv\Scripts\python.exe compare_candidates.py
```

## Export and Analyse Results

```powershell
.\.venv\Scripts\python.exe export_results.py
.\.venv\Scripts\python.exe load_results.py
```

## Scoring Method

The current score is:

`Score = (Passed test cases / Total test cases) × 100`

The current evaluator uses five cases for one coding challenge.

## Limitations

This is an early prototype, not a validated general-purpose AI reasoning
benchmark. Results measure performance on the current test cases only.

Candidate functions currently run in-process. Do not use this evaluator
to execute untrusted code. Secure isolated execution, broader challenges,
and systematic benchmark validation remain future work.

## Future Improvements

- Add multiple independent coding challenges.
- Improve edge-case and failure analysis.
- Record benchmark versions and candidate metadata.
- Add secure execution for untrusted submissions.
- Develop visual analytics using SQL and Power BI.
