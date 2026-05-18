import ast
import os
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}
IGNORE_DIRS = {"node_modules", ".git", "__pycache__", ".next", "dist", "build", "venv", ".venv"}


def analyze_repo(repo_path: str) -> dict[str, Any]:
    """
    Walk the repo and extract a structured map of all
    functions, classes, and API routes for test generation.
    """
    repo = Path(repo_path)
    files = []

    for path in repo.rglob("*"):
        if path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        rel = path.relative_to(repo)
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            info = _extract_file_info(str(path), source)
            if info["symbols"]:
                files.append({"path": str(rel), "language": _lang(path.suffix), **info})
        except Exception:
            continue

    return {
        "total_files": len(files),
        "files": files,
        "languages": list({f["language"] for f in files}),
    }


def _lang(suffix: str) -> str:
    return "python" if suffix == ".py" else "javascript"


def _extract_file_info(path: str, source: str) -> dict[str, Any]:
    if path.endswith(".py"):
        return _parse_python(source)
    return _parse_js_basic(source)


def _parse_python(source: str) -> dict[str, Any]:
    symbols = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"symbols": [], "imports": []}

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            docstring = ast.get_docstring(node) or ""
            symbols.append({
                "type": "function",
                "name": node.name,
                "args": args,
                "docstring": docstring,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            })
        elif isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            symbols.append({
                "type": "class",
                "name": node.name,
                "methods": methods,
                "line": node.lineno,
            })

    imports = [
        ast.dump(n) for n in ast.walk(tree)
        if isinstance(n, (ast.Import, ast.ImportFrom))
    ]

    return {"symbols": symbols, "imports": imports[:20]}


def _parse_js_basic(source: str) -> dict[str, Any]:
    """
    Simple regex-free heuristic extraction for JS/TS.
    Good enough for test generation context.
    """
    import re
    symbols = []

    fn_patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:\w+\s*=>|\([^)]*\)\s*=>)",
    ]
    class_pattern = r"(?:export\s+)?class\s+(\w+)"
    route_pattern = r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]"

    for pattern in fn_patterns:
        for m in re.finditer(pattern, source):
            symbols.append({"type": "function", "name": m.group(1), "line": source[:m.start()].count("\n") + 1})

    for m in re.finditer(class_pattern, source):
        symbols.append({"type": "class", "name": m.group(1), "line": source[:m.start()].count("\n") + 1})

    for m in re.finditer(route_pattern, source):
        symbols.append({"type": "route", "method": m.group(1).upper(), "path": m.group(2), "line": source[:m.start()].count("\n") + 1})

    return {"symbols": symbols, "imports": []}
