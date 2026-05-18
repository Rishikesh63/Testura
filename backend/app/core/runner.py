import subprocess
import tempfile
import json
import os
import re
from pathlib import Path
from typing import Any


def run_tests(repo_path: str, test_files: list[dict[str, str]], language: str) -> dict[str, Any]:
    """
    Write generated test files to disk and execute them.
    Returns structured pass/fail results.
    """
    results = []

    for test_file in test_files:
        test_path = os.path.join(repo_path, test_file["path"])
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        Path(test_path).write_text(test_file["content"], encoding="utf-8")

    if language == "python":
        raw = _run_pytest(repo_path)
    else:
        raw = _run_jest(repo_path)

    results = _parse_results(raw, language)
    passed = sum(1 for r in results if r["status"] == "passed")

    return {
        "results": results,
        "tests_passed": passed,
        "tests_failed": len(results) - passed,
        "tests_total": len(results),
        "raw_output": raw.get("stdout", ""),
    }


def _run_pytest(repo_path: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "--json-report", "--json-report-file=-", "-q"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            report = json.loads(proc.stdout)
            return {"stdout": proc.stdout, "report": report, "returncode": proc.returncode}
        except json.JSONDecodeError:
            return {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Test run timed out after 120s", "returncode": -1}


def _run_jest(repo_path: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["npx", "jest", "--json", "--no-coverage"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        try:
            report = json.loads(proc.stdout)
            return {"stdout": proc.stdout, "report": report, "returncode": proc.returncode}
        except json.JSONDecodeError:
            return {"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Test run timed out after 120s", "returncode": -1}


def _parse_results(raw: dict[str, Any], language: str) -> list[dict[str, Any]]:
    results = []
    report = raw.get("report", {})

    if language == "python" and "tests" in report:
        for t in report["tests"]:
            results.append({
                "id": t.get("nodeid", ""),
                "name": t.get("nodeid", "").split("::")[-1],
                "file": t.get("nodeid", "").split("::")[0],
                "status": "passed" if t.get("outcome") == "passed" else "failed",
                "duration_ms": int(t.get("duration", 0) * 1000),
                "error_message": t.get("call", {}).get("longrepr", "") if t.get("outcome") != "passed" else None,
            })
    elif language == "javascript" and "testResults" in report:
        for suite in report["testResults"]:
            for t in suite.get("testResults", []):
                results.append({
                    "id": t.get("fullName", ""),
                    "name": t.get("title", ""),
                    "file": suite.get("testFilePath", "").split("/")[-1],
                    "status": "passed" if t.get("status") == "passed" else "failed",
                    "duration_ms": t.get("duration", 0),
                    "error_message": "\n".join(t.get("failureMessages", [])) or None,
                })
    else:
        # Fallback: parse raw stdout with regex
        for line in raw.get("stdout", "").splitlines():
            m = re.match(r"(PASSED|FAILED|ERROR)\s+(.+)", line)
            if m:
                results.append({
                    "id": m.group(2),
                    "name": m.group(2).split("::")[-1],
                    "file": m.group(2).split("::")[0],
                    "status": "passed" if m.group(1) == "PASSED" else "failed",
                    "duration_ms": 0,
                    "error_message": None,
                })

    return results
