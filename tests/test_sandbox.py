
import pytest

from src.sandbox import run_in_sandbox


@pytest.fixture(scope="module", autouse=True)
def verify_docker_image():
    """Confirm Docker can run the configured Python image."""
    import subprocess

    result = subprocess.run(
        [
            "docker", "image", "inspect", "python:3.12-slim",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, (
        "Docker image python:3.12-slim is unavailable: "
        + result.stderr
    )


def test_correct_solution_passes():
    result = run_in_sandbox(
        "def add(a, b):\n    return a + b",
        "assert add(2, 3) == 5\nassert add(-1, 1) == 0",
    )
    assert result["status"] == "pass"
    assert result["passed"] is True


def test_wrong_solution_fails():
    result = run_in_sandbox(
        "def add(a, b):\n    return a - b",
        "assert add(2, 3) == 5",
    )
    assert result["status"] == "wrong_output"
    assert result["passed"] is False


def test_syntax_error_is_classified():
    result = run_in_sandbox(
        "def add(a, b)\n    return a + b",
        "assert True",
    )
    assert result["status"] == "syntax_error"


def test_infinite_loop_times_out():
    result = run_in_sandbox(
        "while True:\n    pass",
        "assert True",
        timeout=3,
    )
    assert result["status"] == "timeout"


def test_runtime_error_is_classified():
    result = run_in_sandbox(
        "raise ValueError('intentional test error')",
        "assert True",
    )
    assert result["status"] == "runtime_error"


def test_invalid_timeout_is_rejected():
    with pytest.raises(ValueError):
        run_in_sandbox("pass", "pass", timeout=0)


def test_non_string_code_is_rejected():
    with pytest.raises(TypeError):
        run_in_sandbox(None, "assert True")
