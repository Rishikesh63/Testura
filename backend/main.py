import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import repos, tests, webhooks, billing
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


@app.get("/health")
async def health():
    return {"status": "ok"}
