import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

POSTMARK_URL = "https://api.postmarkapp.com/email"


async def send_test_failure_email(to_email: str, repo_name: str, run_id: str,
                                   tests_passed: int, tests_failed: int, tests_total: int) -> None:
    if not settings.postmark_api_key:
        logger.warning("POSTMARK_API_KEY not set — skipping email")
        return

    pass_rate = round(tests_passed / tests_total * 100) if tests_total > 0 else 0
    repo_url = f"https://testura.dev/repos/{run_id}"

    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:24px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:24px">
        <span style="font-size:20px">⚡</span>
        <span style="font-weight:700;font-size:18px">Testura</span>
      </div>

      <h2 style="margin:0 0 8px;font-size:20px;color:#111">Tests failed on <code>{repo_name}</code></h2>
      <p style="color:#555;margin:0 0 24px">A new test run completed with failures.</p>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:24px">
        <div style="background:#f9fafb;border-radius:12px;padding:16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#16a34a">{tests_passed}</div>
          <div style="font-size:12px;color:#6b7280">Passed</div>
        </div>
        <div style="background:#f9fafb;border-radius:12px;padding:16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#dc2626">{tests_failed}</div>
          <div style="font-size:12px;color:#6b7280">Failed</div>
        </div>
        <div style="background:#f9fafb;border-radius:12px;padding:16px;text-align:center">
          <div style="font-size:24px;font-weight:700;color:#2563eb">{pass_rate}%</div>
          <div style="font-size:12px;color:#6b7280">Pass rate</div>
        </div>
      </div>

      <a href="{repo_url}" style="display:inline-block;background:#2563eb;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">
        View Results →
      </a>

      <p style="color:#9ca3af;font-size:12px;margin-top:24px">
        You're receiving this because you connected {repo_name} to Testura.
      </p>
    </div>
    """

    text = (
        f"Tests failed on {repo_name}\n\n"
        f"Passed: {tests_passed} | Failed: {tests_failed} | Pass rate: {pass_rate}%\n\n"
        f"View results: {repo_url}"
    )

    async with httpx.AsyncClient() as client:
        res = await client.post(
            POSTMARK_URL,
            headers={
                "X-Postmark-Server-Token": settings.postmark_api_key,
                "Content-Type": "application/json",
            },
            json={
                "From": f"{settings.from_name} <{settings.from_email}>",
                "To": to_email,
                "Subject": f"❌ {tests_failed} tests failed on {repo_name} ({pass_rate}% passing)",
                "HtmlBody": html,
                "TextBody": text,
                "MessageStream": "outbound",
            },
        )
    if res.status_code == 200:
        logger.info("Email sent to %s for %s", to_email, repo_name)
    else:
        logger.error("Postmark error %d: %s", res.status_code, res.text)
