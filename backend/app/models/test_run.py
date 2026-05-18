from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TestResult(BaseModel):
    id: str
    name: str
    file: str
    status: str  # passed | failed | error
    duration_ms: int
    error_message: Optional[str] = None
    fix_suggestion: Optional[str] = None


class TestRunOut(BaseModel):
    id: str
    repo_id: str
    status: str  # running | passed | failed
    created_at: datetime
    duration_ms: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_total: int = 0
    results: list[TestResult] = []
