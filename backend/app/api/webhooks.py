from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.core.config import settings
from supabase import create_client
import hmac
import hashlib

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
supabase = create_client(settings.supabase_url, settings.supabase_service_key)


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")

    # Verify webhook signature
    expected = "sha256=" + hmac.new(
        settings.github_client_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(sig, expected):
        raise HTTPException(401, "Invalid signature")

    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "push":
        repo_full_name = payload.get("repository", {}).get("full_name")
        if repo_full_name:
            res = supabase.table("repos").select("id").eq("full_name", repo_full_name).execute()
            if res.data:
                from app.api.tests import _run_pipeline
                repo = res.data[0]
                repo_res = supabase.table("repos").select("*").eq("id", repo["id"]).single().execute()
                import uuid
                run_id = str(uuid.uuid4())
                supabase.table("test_runs").insert({
                    "id": run_id, "repo_id": repo["id"], "status": "running",
                    "tests_passed": 0, "tests_failed": 0, "tests_total": 0,
                }).execute()
                background_tasks.add_task(_run_pipeline, repo["id"], run_id, repo_res.data)

    return {"ok": True}
