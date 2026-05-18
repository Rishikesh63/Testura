from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import repos, tests, webhooks
from app.core.config import settings

app = FastAPI(
    title="TestPilot API",
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


@app.get("/health")
async def health():
    return {"status": "ok"}
