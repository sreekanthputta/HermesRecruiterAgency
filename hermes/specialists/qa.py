"""QA specialist: verify every claim in an outreach draft against evidence."""
import json
from pathlib import Path

from hermes.llm import LLMResult, MANAGER_MODEL, call, parse_json

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "qa.md"


def run_qa(candidate_id: str, evidence_summary: str, outreach_draft: dict, model: str = None) -> tuple[dict, LLMResult]:
    """Return (QAVerdict dict, LLMResult). Uses manager-tier model — QA must be strict."""
    payload = {
        "candidate_id": candidate_id,
        "evidence_summary": evidence_summary,
        "outreach_draft": outreach_draft,
    }
    prompt = PROMPT_PATH.read_text() + "\n\nInput:\n" + json.dumps(payload, indent=2)
    result = call(prompt, model=model or MANAGER_MODEL, temperature=0.1, json_mode=True)
    verdict = parse_json(result.text)
    verdict.setdefault("candidate_id", candidate_id)
    verdict.setdefault("verdict", "block")
    verdict.setdefault("reasons", [])
    verdict.setdefault("unverified_claims", [])
    verdict.setdefault("verified_claims", [])
    if verdict["verdict"] not in {"pass", "block"}:
        verdict["verdict"] = "block"
    return verdict, result
