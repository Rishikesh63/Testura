from openai import OpenAI
from app.core.config import settings
from typing import Any

_client: OpenAI | None = None

def _get_client() -> OpenAI:
    global _client
    if _client is not None:
        return _client
    if settings.nvidia_api_key:
        _client = OpenAI(
            api_key=settings.nvidia_api_key,
            base_url="https://integrate.api.nvidia.com/v1",
        )
    elif settings.groq_api_key:
        _client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    else:
        raise RuntimeError("Set NVIDIA_API_KEY or GROQ_API_KEY in .env")
    return _client


def _model() -> str:
    if settings.nvidia_api_key:
        return "meta/llama-3.3-70b-instruct"
    return "llama-3.1-8b-instant"


SYSTEM_PROMPT = """You are an expert software testing engineer.
Given a code file and its symbol map, generate tests.

Rules:
- Return ONLY the test file content, no explanation, no markdown fences
- Cover happy path, edge cases, and error cases

For Python files: use pytest, plain functions, no imports of the source file needed if mocking.

For JavaScript/TypeScript files:
- Output CommonJS JavaScript (.js), NOT TypeScript
- Do NOT use import/export statements — ONLY use jest.fn() and describe/it/expect
- Do NOT require() or mock() any source files — write fully self-contained tests
- All values and functions must be defined inline in the test file itself
- Tests should describe expected behavior using only jest built-ins

Example JS test structure (fully self-contained, no imports):
describe('calculateTotal', () => {
  const calculateTotal = (items) => items.reduce((sum, i) => sum + i.price, 0);

  it('returns 0 for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });
  it('sums item prices', () => {
    expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
  });
});
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

Source code (truncated to 1500 chars):
```{lang}
{source_code[:1500]}
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
