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
    repos = sb.table("repos").select("id", count="exact").execute()
    runs = sb.table("test_runs").select("tests_passed,tests_total").neq("tests_total", 0).execute()
    run_data = runs.data or []
    total_passed = sum(r["tests_passed"] for r in run_data)
    total_tests  = sum(r["tests_total"]  for r in run_data)
    avg_pass_rate = round(total_passed / total_tests * 100) if total_tests > 0 else 0
    highest_pass_rate = max(
        (round(r["tests_passed"] / r["tests_total"] * 100) for r in run_data if r["tests_total"] > 0),
        default=0,
    )
    total_run = sum(r["tests_total"] for r in run_data)
    return {
        "repos": repos.count or 0,
        "tests_run": total_run,
        "avg_pass_rate": avg_pass_rate,
        "highest_pass_rate": highest_pass_rate,
    }
