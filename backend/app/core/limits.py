from fastapi import HTTPException

# Plan limits — controls Claude API cost and compute usage
PLAN_LIMITS = {
    "free":    {"repos": 1,   "runs_per_month": 50,  "files_per_run": 10, "max_file_kb": 50},
    "starter": {"repos": 3,   "runs_per_month": 500, "files_per_run": 20, "max_file_kb": 100},
    "pro":     {"repos": 10,  "runs_per_month": 9999,"files_per_run": 50, "max_file_kb": 200},
    "team":    {"repos": 999, "runs_per_month": 9999,"files_per_run": 100,"max_file_kb": 500},
}

DEFAULT_PLAN = "free"


def get_limits(plan: str) -> dict:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[DEFAULT_PLAN])


def check_repo_limit(current_count: int, plan: str) -> None:
    limit = get_limits(plan)["repos"]
    if current_count >= limit:
        raise HTTPException(
            403,
            f"Repo limit reached for {plan} plan ({limit} repos). "
            "Upgrade at testura.dev/billing"
        )


def check_run_limit(runs_this_month: int, plan: str) -> None:
    limit = get_limits(plan)["runs_per_month"]
    if runs_this_month >= limit:
        raise HTTPException(
            403,
            f"Monthly run limit reached ({limit} runs). "
            "Upgrade at testura.dev/billing"
        )


def cap_files(files: list, plan: str) -> list:
    limit = get_limits(plan)["files_per_run"]
    return files[:limit]


def filter_large_files(files: list, plan: str) -> list:
    max_kb = get_limits(plan)["max_file_kb"]
    return [f for f in files if f.get("size_kb", 0) <= max_kb]
