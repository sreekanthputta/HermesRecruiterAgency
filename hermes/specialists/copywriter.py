"""Copywriter specialist: candidate + rubric -> outreach draft. Supports revision mode."""
import json
from pathlib import Path

from hermes.llm import LLMResult, SPECIALIST_MODEL, call, parse_json

PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def run_copywriter(
    candidate: dict,
    rewritten_jd: str,
    founder_context: str = "solo founder, pre-seed B2B SaaS, hiring first backend engineer",
    prior_output: dict = None,
    revision_notes: list = None,
    model: str = None,
) -> tuple[dict, LLMResult]:
    """Return ({subject, body}, LLMResult)."""
    is_revision = bool(prior_output and revision_notes)
    prompt_file = "copywriter_revision.md" if is_revision else "copywriter.md"
    prompt = (PROMPT_DIR / prompt_file).read_text()

    payload = {
        "candidate": {
            "name": candidate.get("name"),
            "evidence_url": candidate.get("evidence_url"),
            "evidence_summary": candidate.get("evidence_summary"),
            "why_match": candidate.get("why_match"),
        },
        "rewritten_jd": rewritten_jd,
        "founder_context": founder_context,
    }
    if is_revision:
        payload["prior_output"] = prior_output
        payload["revision_notes"] = revision_notes

    full_prompt = prompt + "\n\nInput:\n" + json.dumps(payload, indent=2)
    result = call(full_prompt, model=model or SPECIALIST_MODEL, temperature=0.6, json_mode=True)
    draft = parse_json(result.text)
    draft.setdefault("subject", "Quick note")
    draft.setdefault("body", "")
    return draft, result
