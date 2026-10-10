# AI Model Evaluation Benchmark

A Python-based project for evaluating coding solutions against predefined test cases, measuring functional correctness, running candidate code in a Docker sandbox, and storing evaluation results for analysis and visualization.

## Project Overview

The AI Model Evaluation Benchmark is a personal portfolio project exploring automated evaluation of coding solutions. It combines benchmark challenges, test-driven evaluation, sandbox execution, structured result storage, and reporting.

The project is designed to demonstrate practical skills in Python development, software testing, execution controls, data processing, SQL, and dashboard development.

The current implementation is an evolving prototype. Its evaluation results depend on the benchmark tasks, test cases, and scoring logic configured in the project.

## Features

- **Benchmark challenges:** Define coding problems and expected behavior.
- **Automated evaluation:** Run candidate implementations against predefined test cases.
- **Scoring and reporting:** Display evaluation scores, pass counts, and individual test outcomes.
- **Candidate comparison:** Compare candidate evaluation results.
- **Batch evaluation:** Run evaluations using the project's batch-evaluation script.
- **Docker sandbox:** Execute sample candidate code with configured execution restrictions.
- **Result storage:** Store evaluation records in CSV files and a local SQLite database.
- **Result export:** Export evaluation data for further analysis.
- **Power BI dashboard:** Visualize available evaluation data and metrics.
- **Automated testing:** Use pytest to validate evaluation, sandbox, reporting, and result-handling components.

## Technology Stack

- Python
- pytest
- Docker
- SQLite
- CSV
- Power BI
- Git and GitHub

## Project Structure

```text
ai-model-evaluation/
├── benchmarks/
│   └── first_challenge.py
├── src/
│   ├── evaluator.py
│   ├── sandbox.py
│   ├── sandbox_report.py
│   └── sandbox_results.py
├── tests/
│   ├── test_evaluator.py
│   ├── test_export_sandbox_results.py
│   ├── test_first_challenge.py
│   ├── test_sandbox.py
│   ├── test_sandbox_report.py
│   └── test_sandbox_results.py
├── AI_Evaluation_Dashboard.pbix
├── compare_candidates.py
├── export_results.py
├── export_sandbox_results.py
├── load_results.py
├── run_batch_evaluation.py
├── run_evaluation.py
├── run_sandbox_evaluation.py
├── README.md
└── .gitignore
```

Generated files, local databases, and additional development files may also be present when the project is run.

## Getting Started

### Prerequisites

- Python installed on your system
- Git, if cloning the repository
- Docker Desktop, for sandbox evaluation
- Power BI Desktop, to open the dashboard

### Clone the Repository

```powershell
git clone https://github.com/mushtaqsaya3i-hash/ai-model-evaluation.git
cd ai-model-evaluation
```

### Create a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install the Testing Dependency

```powershell
python -m pip install pytest
```

Install any additional dependencies required by the specific scripts you intend to use.

## Run the Evaluation

From the project root, execute:

```powershell
python .\run_evaluation.py
```

This runs the configured benchmark challenge against the candidate implementation and displays the evaluation score, the number of passed tests, and the individual test results.

## Run the Sandbox Evaluation

Make sure Docker Desktop is running and the required Docker image and configuration are available.

Execute:

```powershell
python .\run_sandbox_evaluation.py
```

The script submits the sample candidate code and test code to the sandbox, displays the execution status and available output, and records the result in the local SQLite database.

The sandbox applies configured execution restrictions intended to reduce risk when running candidate code. These controls should not be considered a guarantee of security.

## Run the Automated Tests

From the project root, run:

```powershell
python -m pytest -v
```

Pytest reports which tests pass or fail. The tests cover core evaluation behavior, benchmark functionality, sandbox execution, reporting, and result handling.

## Additional Evaluation and Data Scripts

The repository includes scripts for additional workflows:

| Script | Purpose |
|---|---|
| `compare_candidates.py` | Compare candidate evaluation results |
| `run_batch_evaluation.py` | Run batch evaluations |
| `export_results.py` | Export evaluation results |
| `export_sandbox_results.py` | Export sandbox results |
| `load_results.py` | Load results for data analysis |

Review the relevant script before running it to understand its inputs, dependencies, and output locations.

## Data Storage and Reporting

The project uses structured results to support inspection and analysis.

- **CSV:** Export evaluation results for review and further processing.
- **SQLite:** Store structured evaluation records locally.
- **Power BI:** Explore the available results through the `AI_Evaluation_Dashboard.pbix` dashboard.

The dashboard's findings depend on the data loaded into the project. Results from a small or limited benchmark should not be treated as a general measure of a model's overall coding ability.

## Security Considerations

Executing candidate code can introduce security risks. The Docker sandbox uses configured restrictions to help limit execution, but the implementation has not been independently security-audited.

Do not assume that the sandbox provides complete isolation. Further security testing, hardening, and validation are required before considering the system for production or high-risk workloads.

## Current Limitations

- The benchmark currently covers a limited set of coding tasks.
- Evaluation quality depends on the quality and diversity of the test cases.
- Scores from a small benchmark may not generalize to other programming tasks.
- Sandbox restrictions require further independent validation.
- Dependency management and automated CI/CD can be improved.
- Broader benchmark coverage and reproducibility remain areas for development.
## Future Improvements

- Expand the benchmark with more diverse coding challenges.
- Improve test-case coverage and evaluation reliability.
- Strengthen and independently validate sandbox security.
- Add automated continuous integration.
- Improve dependency management and environment reproducibility.
- Expand reporting, candidate comparisons, and dashboard metrics.
- Document evaluation methodology and known limitations in greater detail.

## Author and Repository

**GitHub repository:** [mushtaqsaya3i-hash/ai-model-evaluation](https://github.com/mushtaqsaya3i-hash/ai-model-evaluation)

This project is an ongoing exploration of automated coding evaluation, Python testing, sandbox execution, and data-driven reporting.