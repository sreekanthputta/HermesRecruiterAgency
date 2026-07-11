"""Thin OpenAI wrapper with token + cost tracking."""
import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv(override=True)
# Guard against shell OPENAI_BASE_URL / OPENAI_ORGANIZATION redirecting to a local proxy.
for _v in ("OPENAI_BASE_URL", "OPENAI_ORGANIZATION"):
    if _v in os.environ and not os.environ[_v].startswith("https://api.openai.com"):
        os.environ.pop(_v, None)

# Rates in USD per token
RATES = {
    "gpt-4o": {"in": 2.50 / 1_000_000, "out": 10.00 / 1_000_000},
    "gpt-4o-mini": {"in": 0.15 / 1_000_000, "out": 0.60 / 1_000_000},
    "gpt-4.1": {"in": 2.50 / 1_000_000, "out": 10.00 / 1_000_000},
    "gpt-4.1-mini": {"in": 0.15 / 1_000_000, "out": 0.60 / 1_000_000},
}

MANAGER_MODEL = os.getenv("OPENAI_MODEL_MANAGER", "gpt-4o")
SPECIALIST_MODEL = os.getenv("OPENAI_MODEL_SPECIALIST", "gpt-4o-mini")


@dataclass
class LLMResult:
    text: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    duration_ms: int
    raw: dict = field(default_factory=dict)


def _client():
    from openai import OpenAI
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url and not base_url.startswith("https://api.openai.com"):
        base_url = None
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)


def call(prompt: str, model: str = None, temperature: float = 0.4, json_mode: bool = False) -> LLMResult:
    """Single-shot chat completion. Returns LLMResult with cost tracking."""
    model = model or SPECIALIST_MODEL
    started = time.time()
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    if not os.getenv("OPENAI_API_KEY"):
        # Offline stub — return skeleton JSON so downstream code doesn't crash
        return _offline_stub(prompt, model, started, json_mode)

    try:
        resp = _client().chat.completions.create(**kwargs)
    except Exception as e:
        print(f"[llm] OpenAI call failed ({e}); returning stub")
        return _offline_stub(prompt, model, started, json_mode)

    text = resp.choices[0].message.content or ""
    usage = resp.usage
    t_in = getattr(usage, "prompt_tokens", 0) if usage else 0
    t_out = getattr(usage, "completion_tokens", 0) if usage else 0
    rate = RATES.get(model, RATES["gpt-4o-mini"])
    cost = t_in * rate["in"] + t_out * rate["out"]
    return LLMResult(
        text=text,
        model=model,
        tokens_in=t_in,
        tokens_out=t_out,
        cost_usd=round(cost, 6),
        duration_ms=int((time.time() - started) * 1000),
        raw={"finish_reason": resp.choices[0].finish_reason},
    )


def _offline_stub(prompt: str, model: str, started: float, json_mode: bool) -> LLMResult:
    """Return plausible-shape output when OPENAI_API_KEY is missing."""
    lp = prompt.lower()
    if "role strategist" in lp or "rewritten_jd" in lp:
        text = json.dumps({
            "rewritten_jd": "Pre-seed B2B SaaS founder hiring first backend engineer. Python + Postgres, ship end-to-end with the founder for six months.",
            "must_have": ["Production Python (Django or FastAPI)", "PostgreSQL schema and query work", "3+ yrs backend"],
            "nice_to_have": ["Async Python (asyncio/asyncpg)", "Distributed systems", "Startup experience"],
            "ignore": ["Frontend-only", "WordPress specialists", "Bootcamp-only"],
            "weights": {"Production Python (Django or FastAPI)": 3, "PostgreSQL schema and query work": 3, "3+ yrs backend": 2, "Async Python (asyncio/asyncpg)": 1, "Distributed systems": 1, "Startup experience": 1},
        })
    elif "manager of an ai recruiting agency" in lp:
        text = json.dumps({
            "role_type": "backend_engineer",
            "location": "Hyderabad",
            "plan": [
                {"step": 1, "specialist": "role_strategist", "task": "rewrite JD and build weighted rubric"},
                {"step": 2, "specialist": "sourcer", "task": "find GitHub-heavy profiles"},
                {"step": 3, "specialist": "copywriter", "task": "draft one personal outreach per candidate"},
                {"step": 4, "specialist": "qa", "task": "verify every claim against evidence"},
                {"step": 5, "specialist": "gmail_draft_writer", "task": "save qa-passed drafts to Gmail"},
            ],
            "rubric_seed": {
                "must_have": ["Python", "PostgreSQL", "3+ yrs backend"],
                "nice_to_have": ["distributed systems", "startup experience"],
                "ignore": ["frontend-only", "students"],
            },
        })
    elif "outreach copywriter" in lp:
        text = json.dumps({
            "subject": "Quick note on your public work",
            "body": "Hi — I saw your recent open-source work and it lined up with what we are building. I'm a solo founder at a pre-seed B2B SaaS and hiring my first backend engineer (Python + Postgres, own the core service). Worth a 15-min chat this week? — Alex",
        })
    elif "qa agent" in lp:
        text = json.dumps({
            "candidate_id": "cand_stub",
            "verdict": "pass",
            "reasons": [],
            "unverified_claims": [],
            "verified_claims": ["public work"],
        })
    else:
        text = "{}" if json_mode else "stub"
    return LLMResult(
        text=text,
        model=model,
        tokens_in=len(prompt) // 4,
        tokens_out=len(text) // 4,
        cost_usd=0.0,
        duration_ms=int((time.time() - started) * 1000),
        raw={"stub": True},
    )


def parse_json(text: str) -> dict:
    """Best-effort JSON parse from an LLM response — strips code fences."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.startswith("json"):
            t = t[4:]
        t = t.strip().rstrip("`").strip()
    # If model returned prose before/after, grab first {...} block
    try:
        return json.loads(t)
    except Exception:
        pass
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except Exception:
            pass
    print(f"[llm] parse_json failed on: {text[:200]}")
    return {}
