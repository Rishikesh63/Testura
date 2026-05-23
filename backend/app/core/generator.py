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
Given a code file and its symbol map, generate tests that WILL PASS.

Rules:
- Return ONLY the test file content, no explanation, no markdown fences
- Every test you write MUST pass — do not test unknown external behavior
- Focus ONLY on pure logic: math, string manipulation, array operations, object transformations
- SKIP any function that does network calls, database queries, DOM access, or file I/O

For JavaScript files (.js source):
- Output CommonJS JavaScript (.js)
- You MAY require() the source file: const { myFn } = require('../path/to/source')
- Dependencies are pre-installed so require() will work
- Test the ACTUAL exported functions from the source file
- Use ONLY: describe, it, expect, jest.fn()
- Use toThrow() NOT toThrowError() (toThrowError was removed in Jest 29)

For TypeScript files (.ts/.tsx source):
- Output CommonJS JavaScript (.js), NOT TypeScript
- Do NOT require() or import TypeScript files — no transform is available
- Define every function you test INLINE inside the describe block
- Your inline implementation must be consistent with your assertions — you control both

Correct pattern for inline (TypeScript source):
describe('formatPrice', () => {
  const formatPrice = (n) => '$' + n.toFixed(2);
  it('formats integer', () => { expect(formatPrice(10)).toBe('$10.00'); });
  it('formats decimal', () => { expect(formatPrice(9.5)).toBe('$9.50'); });
  it('formats zero', () => { expect(formatPrice(0)).toBe('$0.00'); });
});

Correct pattern for require (JavaScript source):
const { formatPrice } = require('../src/utils');
describe('formatPrice', () => {
  it('formats integer', () => { expect(formatPrice(10)).toBe('$10.00'); });
});

For Python files:
- Use pytest, plain functions (no classes)
- No imports of source files — define all helpers inline
- Focus on pure functions: data transforms, string ops, calculations
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
