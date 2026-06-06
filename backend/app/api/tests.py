import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.api.repos import get_current_user
from app.core.analyzer import analyze_repo
from app.core.generator import generate_tests_for_file, generate_fix_suggestion, fix_failing_tests
from app.services.email import send_test_failure_email
from app.core.runner import run_tests
from app.services.github import clone_repo, detect_language
from app.core.config import settings
from supabase import create_client
from pathlib import Path
import uuid
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["tests"])

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/{repo_id}/runs")
async def start_run(repo_id: str, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    res = supabase.table("repos").select("*").eq("id", repo_id).eq("user_id", user_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Repo not found")

    run_id = str(uuid.uuid4())
    supabase.table("test_runs").insert({
        "id": run_id,
        "repo_id": repo_id,
        "status": "running",
        "tests_passed": 0,
        "tests_failed": 0,
        "tests_total": 0,
    }).execute()

    background_tasks.add_task(_run_pipeline, repo_id, run_id, res.data)
    return {"run_id": run_id, "status": "running"}


async def _run_pipeline(repo_id: str, run_id: str, repo_data: dict):
    start = time.time()
    try:
        repo_path = clone_repo(repo_data["repo_url"], repo_id)
        language = repo_data.get("language") or detect_language(repo_path)
        logger.info("Cloned repo to %s, language=%s", repo_path, language)

        analysis = analyze_repo(repo_path)
        logger.info("Analysis: %d files with symbols", len(analysis["files"]))

        # Generate tests in parallel (5x faster than sequential)
        def _gen(file_info):
            try:
                source = Path(repo_path, file_info["path"]).read_text(encoding="utf-8", errors="ignore")
                content = generate_tests_for_file(file_info, source)
                if content:
                    return {"path": _test_path(file_info["path"], language), "content": content}
            except Exception as e:
                logger.warning("Failed to generate tests for %s: %s", file_info["path"], e)
            return None

        candidate_files = _select_best_files(analysis["files"], n=5)
        test_files = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            futures = {pool.submit(_gen, fi): fi for fi in candidate_files}
            for future in as_completed(futures):
                result_file = future.result()
                if result_file:
                    test_files.append(result_file)
                    logger.info("Generated tests for %s", futures[future]["path"])

        logger.info("Generated %d test files", len(test_files))
        if not test_files:
            _mark_run(run_id, repo_id, "failed", 0, 0, 0, int((time.time() - start) * 1000), [])
            return

        result = run_tests(repo_path, test_files, language)
        logger.info("=== JEST RESULTS COUNT: %d", len(result.get("results", [])))

        # Multi-turn: fix failing tests and re-run once
        if result.get("tests_failed", 0) > 0:
            result = _fix_and_rerun(repo_path, test_files, result, language)

        # Generate fix suggestions in parallel
        def _fix(r):
            if r.get("error_message"):
                try:
                    src_path = Path(repo_path, r["file"])
                    snippet = src_path.read_text(encoding="utf-8", errors="ignore")[:500] if src_path.exists() else ""
                    r["fix_suggestion"] = generate_fix_suggestion(r["name"], r["error_message"], snippet)
                except Exception:
                    pass
            return r

        enriched = []
        with ThreadPoolExecutor(max_workers=5) as pool:
            enriched = list(pool.map(_fix, result["results"]))

        duration = int((time.time() - start) * 1000)
        status = "passed" if result["tests_total"] > 0 and result["tests_failed"] == 0 else "failed"
        _mark_run(run_id, repo_id, status,
                  result["tests_passed"], result["tests_failed"],
                  result["tests_total"], duration, enriched)

        # Email notification on failure
        if status == "failed" and result["tests_total"] > 0:
            try:
                user_res = supabase.table("repos").select("user_email").eq("id", repo_id).maybe_single().execute()
                to_email = (user_res.data or {}).get("user_email") or settings.admin_email
                if to_email:
                    await send_test_failure_email(
                        to_email, repo_data.get("full_name", repo_id), run_id,
                        result["tests_passed"], result["tests_failed"], result["tests_total"],
                    )
            except Exception as e:
                logger.warning("Could not send failure email: %s", e)

    except Exception as e:
        logger.error("Pipeline failed for run %s: %s", run_id, e, exc_info=True)
        duration = int((time.time() - start) * 1000)
        _mark_run(run_id, repo_id, "failed", 0, 0, 0, duration, [])


def _mark_run(run_id, repo_id, status, passed, failed, total, duration_ms, results):
    supabase.table("test_runs").update({
        "status": status,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_total": total,
        "duration_ms": duration_ms,
        "results": results,
    }).eq("id", run_id).execute()

    supabase.table("repos").update({
        "last_run_status": status,
        "last_run_at": "now()",
        "tests_passed": passed,
        "tests_total": total,
    }).eq("id", repo_id).execute()


@router.get("/{repo_id}/runs")
async def list_runs(repo_id: str, user_id: str = Depends(get_current_user)):
    # Verify repo belongs to user
    repo = supabase.table("repos").select("id").eq("id", repo_id).eq("user_id", user_id).single().execute()
    if not repo.data:
        raise HTTPException(404, "Repo not found")
    res = supabase.table("test_runs").select("*").eq("repo_id", repo_id).order("created_at", desc=True).execute()
    return {"runs": res.data}


@router.get("/{repo_id}/runs/{run_id}")
async def get_run(repo_id: str, run_id: str, user_id: str = Depends(get_current_user)):
    repo = supabase.table("repos").select("id").eq("id", repo_id).eq("user_id", user_id).single().execute()
    if not repo.data:
        raise HTTPException(404, "Repo not found")
    res = supabase.table("test_runs").select("*").eq("id", run_id).eq("repo_id", repo_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Run not found")
    return res.data


def _test_path(source_path: str, language: str) -> str:
    p = Path(source_path)
    if language == "python":
        return str(p.parent / f"test_{p.stem}.py")
    return str(p.parent / f"{p.stem}.test.js")


def _score_file(file_info: dict) -> int:
    path = file_info["path"].lower().replace("\\", "/")
    score = len(file_info.get("symbols", []))  # more symbols = higher priority

    # Boost pure-logic directories
    for boost in ["util", "helper", "lib/", "hook", "service", "store", "format", "parse", "calc", "math", "common"]:
        if boost in path:
            score += 8

    # Lightly penalise hard-to-test files (don't exclude them entirely)
    for penalty in ["types.", ".d.ts", "test", "spec", "mock", "fixture"]:
        if penalty in path:
            score -= 15

    return score


def _select_best_files(files: list, n: int = 5) -> list:
    with_symbols = [f for f in files if f.get("symbols")]
    return sorted(with_symbols, key=_score_file, reverse=True)[:n]


def _fix_and_rerun(repo_path: str, test_files: list, first_result: dict, language: str) -> dict:
    # Collect errors per test file
    errors_by_file: dict = {}
    for r in first_result.get("results", []):
        if r.get("error_message"):
            errors_by_file.setdefault(r["file"], []).append(r["error_message"])

    fixed_any = False
    for tf in test_files:
        tf_name = Path(tf["path"]).name
        if tf_name in errors_by_file:
            try:
                fixed = fix_failing_tests(tf["content"], errors_by_file[tf_name])
                if fixed and fixed != tf["content"]:
                    tf["content"] = fixed
                    fixed_any = True
                    logger.info("Fixed failing tests in %s", tf_name)
            except Exception as e:
                logger.warning("Could not fix %s: %s", tf_name, e)

    if not fixed_any:
        return first_result

    logger.info("Re-running tests after multi-turn fix")
    return run_tests(repo_path, test_files, language)
