from fastapi import APIRouter
from fastapi.responses import Response
from app.core.config import settings
from supabase import create_client

router = APIRouter(prefix="/badge", tags=["badge"])
supabase = create_client(settings.supabase_url, settings.supabase_service_key)


def _svg(label: str, value: str, color: str) -> str:
    lw = len(label) * 6 + 16
    vw = len(value) * 7 + 16
    w = lw + vw
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="{w}" height="20" fill="#555"/>
  <rect rx="3" x="{lw}" width="{vw}" height="20" fill="{color}"/>
  <rect rx="3" width="{w}" height="20" fill="url(#s)"/>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="11">
    <text x="{lw // 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{lw // 2}" y="14">{label}</text>
    <text x="{lw + vw // 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{lw + vw // 2}" y="14">{value}</text>
  </g>
</svg>"""


@router.get("/{owner}/{repo}")
async def get_badge(owner: str, repo: str):
    full_name = f"{owner}/{repo}"
    res = supabase.table("repos").select("tests_passed,tests_total").eq("full_name", full_name).maybe_single().execute()

    if not res.data or res.data["tests_total"] == 0:
        svg = _svg("testura", "unknown", "#9f9f9f")
    else:
        rate = int(res.data["tests_passed"] / res.data["tests_total"] * 100)
        color = "#4c1" if rate >= 80 else "#fe7d37" if rate >= 50 else "#e05d44"
        svg = _svg("testura", f"{rate}% passing", color)

    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "no-cache, max-age=0"})
