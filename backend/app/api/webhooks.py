import json
import hmac
import hashlib
import uuid
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.core.config import settings
from supabase import create_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])
supabase = create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()

    # Verify signature using dedicated webhook secret
    secret = (settings.github_webhook_secret or settings.github_client_secret or "").encode()
    if secret:
        sig = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(401, "Invalid webhook signature")

    payload = json.loads(body)
    event = request.headers.get("X-GitHub-Event")
    logger.info("GitHub webhook event=%s", event)

    if event == "push":
        repo_full_name = payload.get("repository", {}).get("full_name")
        if not repo_full_name:
            return {"ok": True}

        res = supabase.table("repos").select("*").eq("full_name", repo_full_name).execute()
        if not res.data:
            logger.info("Push for %s — repo not connected in Testura", repo_full_name)
            return {"ok": True}

        for repo in res.data:
            run_id = str(uuid.uuid4())
            supabase.table("test_runs").insert({
                "id": run_id,
                "repo_id": repo["id"],
                "status": "running",
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_total": 0,
            }).execute()
            from app.api.tests import _run_pipeline
            background_tasks.add_task(_run_pipeline, repo["id"], run_id, repo)
            logger.info("Triggered test run %s for repo %s on push", run_id, repo_full_name)

    return {"ok": True}
