import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import repos, tests, webhooks, billing, badge
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

app = FastAPI(
    title="Testura API",
    description="Agentic testing for AI-generated code",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repos.router)
app.include_router(tests.router)
app.include_router(webhooks.router)
app.include_router(billing.router)
app.include_router(badge.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats")
async def stats():
    from supabase import create_client
    sb = create_client(settings.supabase_url, settings.supabase_service_key)
    repos_res = sb.table("repos").select("id,full_name,repo_url,tests_passed,tests_total").execute()
    repo_data = repos_res.data or []
    runs = sb.table("test_runs").select("tests_passed,tests_total").neq("tests_total", 0).execute()
    run_data = runs.data or []
    highest_pass_rate = max(
        (round(r["tests_passed"] / r["tests_total"] * 100) for r in run_data if r["tests_total"] > 0),
        default=0,
    )
    total_run = sum(r["tests_total"] for r in run_data)

    # Find repo with highest pass rate
    top_repo = None
    best = -1
    for r in repo_data:
        if r["tests_total"] and r["tests_total"] > 0:
            rate = round(r["tests_passed"] / r["tests_total"] * 100)
            if rate > best:
                best = rate
                top_repo = {
                    "full_name": r["full_name"],
                    "repo_url": r["repo_url"],
                    "pass_rate": rate,
                    "tests_passed": r["tests_passed"],
                    "tests_total": r["tests_total"],
                }

    return {
        "repos": len(repo_data),
        "tests_run": total_run,
        "highest_pass_rate": highest_pass_rate,
        "top_repo": top_repo,
    }
