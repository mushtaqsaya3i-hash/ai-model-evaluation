
"""Run model-generated Python code in a restricted Docker container."""

import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

IMAGE = "python:3.12-slim"
MAX_OUTPUT_BYTES = 64 * 1024


def classify(returncode: int, stderr: str) -> str:
    """Convert execution results into benchmark status labels."""
    if returncode == 0:
        return "pass"
    if "SyntaxError" in stderr or "IndentationError" in stderr:
        return "syntax_error"
    if "AssertionError" in stderr:
        return "wrong_output"
    return "runtime_error"


def run_in_sandbox(
    code: str,
    tests: str,
    timeout: int = 10,
) -> dict:
    """Execute candidate code and plain assert tests inside Docker."""
    if not isinstance(code, str) or not isinstance(tests, str):
        raise TypeError("code and tests must be strings")
    if timeout <= 0:
        raise ValueError("timeout must be positive")

    name = f"sandbox-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code + "\n\n" + tests + "\n", encoding="utf-8")

        cmd = [
            "docker", "run", "--rm",
            "--name", name,
            "--network", "none",
            "--memory", "256m",
            "--memory-swap", "256m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--user", "65534:65534",
            "--log-driver", "none",
            "-v", f"{tmp}:/sandbox:ro",
            "-w", "/sandbox",
            IMAGE,
            "python", "-I", "main.py",
        ]

        start = time.monotonic()

        try:
            # Limit captured output while the process is running.
            with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
                try:
                    result = subprocess.run(
                        cmd,
                        stdout=out,
                        stderr=err,
                        timeout=timeout,
                        check=False,
                    )
                    returncode = result.returncode
                    timed_out = False
                except subprocess.TimeoutExpired:
                    timed_out = True
                    subprocess.run(
                        ["docker", "kill", name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                        check=False,
                    )
                    returncode = -1

                out.seek(0, os.SEEK_END)
                out_size = out.tell()
                out.seek(max(0, out_size - MAX_OUTPUT_BYTES))
                stdout = out.read(MAX_OUTPUT_BYTES).decode(
                    "utf-8", errors="replace"
                )

                err.seek(0, os.SEEK_END)
                err_size = err.tell()
                err.seek(max(0, err_size - MAX_OUTPUT_BYTES))
                stderr = err.read(MAX_OUTPUT_BYTES).decode(
                    "utf-8", errors="replace"
                )

            if timed_out:
                status = "timeout"
                stderr = f"Execution exceeded {timeout} seconds"
            elif returncode == 137:
                status = "resource_limit"
            else:
                status = classify(returncode, stderr)

            return {
                "status": status,
                "passed": status == "pass",
                "seconds": round(time.monotonic() - start, 2),
                "stdout": stdout,
                "stderr": stderr,
                "output_truncated": (
                    out_size > MAX_OUTPUT_BYTES
                    or err_size > MAX_OUTPUT_BYTES
                ),
            }

        except OSError as exc:
            return {
                "status": "sandbox_error",
                "passed": False,
                "seconds": round(time.monotonic() - start, 2),
                "stdout": "",
                "stderr": str(exc),
                "output_truncated": False,
            }
