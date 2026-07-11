"""Role Strategist specialist: JD -> weighted rubric."""
from pathlib import Path

from hermes.llm import MANAGER_MODEL, LLMResult, call, parse_json

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "role_strategist.md"


def run_role_strategist(jd_text: str, model: str = None) -> tuple[dict, LLMResult]:
    """Return (rubric_dict, LLMResult) so caller can log trace."""
    prompt = PROMPT_PATH.read_text() + "\n" + jd_text
    result = call(prompt, model=model or MANAGER_MODEL, temperature=0.3, json_mode=True)
    rubric = parse_json(result.text)
    # Guarantee shape even if LLM screws up
    rubric.setdefault("must_have", [])
    rubric.setdefault("nice_to_have", [])
    rubric.setdefault("ignore", [])
    rubric.setdefault("weights", {})
    rubric.setdefault("rewritten_jd", "")
    return rubric, result
