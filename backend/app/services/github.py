import os
import shutil
from pathlib import Path
import git
from app.core.config import settings


def clone_repo(repo_url: str, repo_id: str) -> str:
    dest = os.path.join(settings.repos_base_path, repo_id)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest, exist_ok=True)
    git.Repo.clone_from(repo_url, dest, depth=1)
    return dest


def pull_repo(repo_path: str) -> None:
    repo = git.Repo(repo_path)
    repo.remotes.origin.pull()


def cleanup_repo(repo_id: str) -> None:
    dest = os.path.join(settings.repos_base_path, repo_id)
    if os.path.exists(dest):
        shutil.rmtree(dest)


def detect_language(repo_path: str) -> str:
    p = Path(repo_path)
    py_files = list(p.rglob("*.py"))
    js_files = list(p.rglob("*.js")) + list(p.rglob("*.ts"))
    return "python" if len(py_files) >= len(js_files) else "javascript"


def detect_test_framework(repo_path: str, language: str) -> str:
    p = Path(repo_path)
    if language == "python":
        req = p / "requirements.txt"
        if req.exists() and "pytest" in req.read_text():
            return "pytest"
        return "pytest"
    package_json = p / "package.json"
    if package_json.exists():
        content = package_json.read_text()
        if "vitest" in content:
            return "vitest"
        if "mocha" in content:
            return "mocha"
    return "jest"
