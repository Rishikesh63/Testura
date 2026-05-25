import uuid
import re
import logging
import httpx
from fastapi import APIRouter, HTTPException
from app.models.repo import RepoConnect, RepoOut
from app.services.github import clone_repo, detect_language, cleanup_repo
from app.core.analyzer import analyze_repo
from app.core.config import settings
from supabase import create_client

logger = logging.getLogger(__name__)

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

    # Auto-create GitHub webhook so tests run on every push
    if body.github_token and settings.github_webhook_secret:
        await _create_github_webhook(full_name, body.github_token)

    return data


async def _create_github_webhook(full_name: str, token: str) -> None:
    url = f"https://api.github.com/repos/{full_name}/hooks"
    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": f"https://testura-backend.fly.dev/webhooks/github",
            "content_type": "json",
            "secret": settings.github_webhook_secret,
        },
    }
    async with httpx.AsyncClient() as client:
        res = await client.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
    if res.status_code in (201, 422):  # 422 = webhook already exists
        logger.info("Webhook set up for %s (status %d)", full_name, res.status_code)
    else:
        logger.warning("Failed to create webhook for %s: %d %s", full_name, res.status_code, res.text)


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
