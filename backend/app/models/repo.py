from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RepoConnect(BaseModel):
    repo_url: str
    github_token: Optional[str] = None
    user_email: Optional[str] = None


class RepoOut(BaseModel):
    id: str
    full_name: str
    repo_url: str
    language: Optional[str] = None
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    tests_passed: int = 0
    tests_total: int = 0
    created_at: datetime
