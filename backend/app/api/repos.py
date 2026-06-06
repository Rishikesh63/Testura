import uuid
import re
import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends, Header
from app.models.repo import RepoConnect
from app.services.github import clone_repo, detect_language, cleanup_repo
from app.core.config import settings
from supabase import create_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["repos"])
supabase = create_client(settings.supabase_url, settings.supabase_service_key)


async def get_current_user(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        res = supabase.auth.get_user(token)
        return res.user.id
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def _parse_repo_name(url: str) -> str:
    match = re.search(r"github\.com/([^/]+/[^/]+?)(?:\.git)?$", url)
    if not match:
        raise HTTPException(400, "Invalid GitHub URL")
    return match.group(1)


@router.get("")
async def list_repos(user_id: str = Depends(get_current_user)):
    res = (
        supabase.table("repos")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"repos": res.data}


@router.post("")
async def connect_repo(body: RepoConnect, user_id: str = Depends(get_current_user)):
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
        "user_id": user_id,
        "user_email": body.user_email,
    }
    supabase.table("repos").insert(data).execute()

    if body.github_token and settings.github_webhook_secret:
        await _create_github_webhook(full_name, body.github_token)

    return data


@router.get("/{repo_id}")
async def get_repo(repo_id: str, user_id: str = Depends(get_current_user)):
    res = (
        supabase.table("repos")
        .select("*")
        .eq("id", repo_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(404, "Repo not found")
    return res.data


@router.delete("/{repo_id}")
async def delete_repo(repo_id: str, user_id: str = Depends(get_current_user)):
    # Verify ownership before deleting
    res = supabase.table("repos").select("id").eq("id", repo_id).eq("user_id", user_id).single().execute()
    if not res.data:
        raise HTTPException(404, "Repo not found")
    supabase.table("test_runs").delete().eq("repo_id", repo_id).execute()
    supabase.table("repos").delete().eq("id", repo_id).execute()
    cleanup_repo(repo_id)
    return {"ok": True}


async def _create_github_webhook(full_name: str, token: str) -> None:
    url = f"https://api.github.com/repos/{full_name}/hooks"
    payload = {
        "name": "web",
        "active": True,
        "events": ["push"],
        "config": {
            "url": "https://testura-backend.fly.dev/webhooks/github",
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
    if res.status_code in (201, 422):
        logger.info("Webhook set up for %s (status %d)", full_name, res.status_code)
    else:
        logger.warning("Failed to create webhook for %s: %d %s", full_name, res.status_code, res.text)
