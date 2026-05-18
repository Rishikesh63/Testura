from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.analyzer import analyze_repo
from app.core.generator import generate_tests_for_file, generate_fix_suggestion
from app.core.runner import run_tests
from app.services.github import clone_repo, detect_language
from app.core.config import settings
from supabase import create_client
from pathlib import Path
import uuid
import time

router = APIRouter(prefix="/repos", tags=["tests"])

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/{repo_id}/runs")
async def start_run(repo_id: str, background_tasks: BackgroundTasks):
    res = supabase.table("repos").select("*").eq("id", repo_id).single().execute()
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

        analysis = analyze_repo(repo_path)

        # Generate tests for each file
        test_files = []
        for file_info in analysis["files"][:15]:  # cap at 15 files per run
            source = Path(repo_path, file_info["path"]).read_text(encoding="utf-8", errors="ignore")
            test_content = generate_tests_for_file(file_info, source)
            if test_content:
                test_path = _test_path(file_info["path"], language)
                test_files.append({"path": test_path, "content": test_content})

        if not test_files:
            _mark_run(run_id, repo_id, "failed", 0, 0, 0, int((time.time() - start) * 1000), [])
            return

        result = run_tests(repo_path, test_files, language)

        # Generate fix suggestions for failed tests
        enriched = []
        for r in result["results"]:
            if r.get("error_message"):
                try:
                    src_path = Path(repo_path, r["file"])
                    snippet = src_path.read_text(encoding="utf-8", errors="ignore")[:500] if src_path.exists() else ""
                    r["fix_suggestion"] = generate_fix_suggestion(r["name"], r["error_message"], snippet)
                except Exception:
                    pass
            enriched.append(r)

        duration = int((time.time() - start) * 1000)
        status = "passed" if result["tests_failed"] == 0 else "failed"
        _mark_run(run_id, repo_id, status,
                  result["tests_passed"], result["tests_failed"],
                  result["tests_total"], duration, enriched)

    except Exception as e:
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
async def list_runs(repo_id: str):
    res = supabase.table("test_runs").select("*").eq("repo_id", repo_id).order("created_at", desc=True).execute()
    return {"runs": res.data}


@router.get("/{repo_id}/runs/{run_id}")
async def get_run(repo_id: str, run_id: str):
    res = supabase.table("test_runs").select("*").eq("id", run_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Run not found")
    return res.data


def _test_path(source_path: str, language: str) -> str:
    p = Path(source_path)
    if language == "python":
        return str(p.parent / f"test_{p.name}")
    return str(p.parent / f"{p.stem}.test{p.suffix}")
