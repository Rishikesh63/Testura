from openai import OpenAI
from app.core.config import settings
from typing import Any

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    if settings.groq_api_key:
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    else:
        raise RuntimeError("GROQ_API_KEY is not set in .env")
    return _client


def _model() -> str:
    return "llama-3.3-70b-versatile"


SYSTEM_PROMPT = """You are an expert software testing engineer.
Given a code file and its symbol map, generate comprehensive tests.
Rules:
- Write tests that actually test behavior, not just that a function exists
- Cover happy path, edge cases, and error cases
- For Python: use pytest. For JS/TS: use Jest with describe/it blocks
- Keep tests concise and readable
- Return ONLY the test file content, no explanation
"""


def generate_tests_for_file(file_info: dict[str, Any], source_code: str) -> str:
    lang = file_info["language"]
    path = file_info["path"]
    symbols = file_info["symbols"]

    if not symbols:
        return ""

    symbol_summary = "\n".join(
        f"- {s['type']} `{s.get('name', s.get('path', ''))}` "
        f"{'args: ' + str(s.get('args', [])) if s.get('args') else ''}"
        f"{'docstring: ' + s['docstring'][:100] if s.get('docstring') else ''}"
        for s in symbols[:20]
    )

    prompt = f"""File: {path}
Language: {lang}
Symbols found:
{symbol_summary}

Source code (truncated to 3000 chars):
```{lang}
{source_code[:3000]}
```

Generate a complete test file for this code."""

    response = _get_client().chat.completions.create(
        model=_model(),
        max_tokens=2048,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return raw


def generate_fix_suggestion(test_name: str, error_message: str, source_snippet: str) -> str:
    prompt = f"""A test failed:
Test: {test_name}
Error:
{error_message[:1000]}

Relevant source code:
```
{source_snippet[:1000]}
```

In 2-3 sentences, explain why this test failed and what change would fix it."""

    response = _get_client().chat.completions.create(
        model=_model(),
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
