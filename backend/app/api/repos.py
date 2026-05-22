from fastapi import APIRouter, HTTPException, Depends
from app.models.repo import RepoConnect, RepoOut
from app.services.github import clone_repo, detect_language, cleanup_repo
from app.core.analyzer import analyze_repo
from app.core.config import settings
from supabase import create_client
import uuid
import re

router = APIRouter(prefix="/repos", tags=["repos"])

supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def _parse_repo_name(url: str) -> str:
    match = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise HTTPException(400, "Invalid GitHub URL")
    return match.group(1)


async def get_user_id(authorization: str = "") -> str:
    # In production: validate JWT from Supabase auth header
    # Simplified for scaffold — replace with real JWT validation
    return "demo-user-id"


@router.get("")
async def list_repos():
    res = supabase.table("repos").select("*").order("created_at", desc=True).execute()
    return {"repos": res.data}


@router.post("")
async def connect_repo(body: RepoConnect):
    full_name = _parse_repo_name(body.repo_url)
    repo_id = str(uuid.uuid4())

    try:
        repo_path = clone_repo(body.repo_url, repo_id)
        language = detect_language(repo_path)
    except Exception as e:
        raise HTTPException(400, f"Failed to clone repo: {str(e)}")

    data = {
        "id": repo_id,
        "full_name": full_name,
        "repo_url": body.repo_url,
        "language": language,
        "tests_passed": 0,
        "tests_total": 0,
    }
    supabase.table("repos").insert(data).execute()
    return data


@router.get("/{repo_id}")
async def get_repo(repo_id: str):
    res = supabase.table("repos").select("*").eq("id", repo_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Repo not found")
    return res.data


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str):
    supabase.table("test_runs").delete().eq("repo_id", repo_id).execute()
    supabase.table("repos").delete().eq("id", repo_id).execute()
    cleanup_repo(repo_id)
    return {"ok": True}
