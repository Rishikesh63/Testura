import subprocess
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_tests(repo_path: str, test_files: list[dict[str, str]], language: str) -> dict[str, Any]:
    for test_file in test_files:
        test_path = os.path.join(repo_path, test_file["path"])
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        Path(test_path).write_text(test_file["content"], encoding="utf-8")

    raw = _run_pytest(repo_path) if language == "python" else _run_jest(repo_path)
    results = _parse_results(raw, language)
    passed = sum(1 for r in results if r["status"] == "passed")

    return {
        "results": results,
        "tests_passed": passed,
        "tests_failed": len(results) - passed,
        "tests_total": len(results),
        "raw_output": raw.get("stdout", "") or raw.get("stderr", ""),
    }


def _run_pytest(repo_path: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            "python -m pytest --tb=short --json-report --json-report-file=- -q",
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            shell=True,
        )
        report = _extract_json(proc.stdout)
        return {"stdout": proc.stdout, "stderr": proc.stderr, "report": report, "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timed out after 120s", "returncode": -1}


def _write_jest_config(repo_path: str) -> None:
    """Write a minimal jest.config.js so jest runs .test.js files in node mode."""
    config_path = Path(repo_path) / "testura.jest.config.js"
    if not config_path.exists():
        config_path.write_text(
            "module.exports = { testEnvironment: 'node', testMatch: ['**/*.test.js'] };\n",
            encoding="utf-8"
        )


def _run_jest(repo_path: str) -> dict[str, Any]:
    _write_jest_config(repo_path)

    jest_local = Path(repo_path) / "node_modules" / ".bin" / "jest"
    jest_global = shutil.which("jest") or shutil.which("jest.cmd")

    if jest_local.exists():
        jest_exe = str(jest_local)
    elif jest_global:
        jest_exe = jest_global
    else:
        logger.error("jest not found in PATH — run: npm install -g jest")
        return {"stdout": "", "stderr": "jest not found", "report": {}, "returncode": -1}

    logger.info("=== Using jest at: %s", jest_exe)
    cmd = f'"{jest_exe}" --config testura.jest.config.js --json --no-coverage --passWithNoTests'

    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            shell=True,
        )
        logger.info("=== JEST returncode: %d", proc.returncode)
        logger.info("=== JEST stderr: %s", (proc.stderr or "")[:600])
        logger.info("=== JEST stdout: %s", (proc.stdout or "")[:600])
        report = _extract_json(proc.stdout)
        return {"stdout": proc.stdout, "stderr": proc.stderr, "report": report, "returncode": proc.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timed out after 60s", "returncode": -1}


def _extract_json(text: str) -> dict:
    """Extract the first valid JSON object from text (handles npm noise before JSON)."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass
    # Find the first '{' and try to parse from there
    idx = text.find('{')
    if idx != -1:
        try:
            return json.loads(text[idx:])
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


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
            file_name = suite.get("testFilePath", "").replace("\\", "/").split("/")[-1]
            for t in suite.get("assertionResults", []):
                results.append({
                    "id": t.get("fullName", ""),
                    "name": t.get("title", ""),
                    "file": file_name,
                    "status": "passed" if t.get("status") == "passed" else "failed",
                    "duration_ms": t.get("duration", 0),
                    "error_message": "\n".join(t.get("failureMessages", [])) or None,
                })
    else:
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
