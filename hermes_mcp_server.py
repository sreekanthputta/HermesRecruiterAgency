"""MCP server exposing the recruiter pipeline as a single sync tool.

Register with your existing Hermes deployment so a Telegram message can
kick off a full run. Runs stdio; add to Hermes MCP config as:

    {
      "recruiter": {
        "command": "python3",
        "args": ["-m", "hermes_mcp_server"],
        "cwd": "/absolute/path/to/hermes-recruiter-agency"
      }
    }
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).parent.resolve()
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT))

from hermes.manager import run as run_pipeline

mcp = FastMCP("recruiter")


@mcp.tool()
def run_recruiter_pipeline(jd_text: str, founder_request: str | None = None) -> dict:
    """Run the full AI recruiting agency on a job description.

    Given a JD (paste the raw text), executes: JD rewrite + rubric →
    real profile sourcing with evidence links → personal outreach draft
    per candidate → QA gate that blocks fabricated claims → Gmail drafts
    saved to the founder's account (never sent). Human clicks send.

    Traces (per-agent tokens, cost, bounce-backs) stream to Convex and
    are viewable on the run board.

    Args:
        jd_text: Raw job description text.
        founder_request: Optional one-line context ("hiring backend eng in Blr").

    Returns: run_id, role_type, location, candidate/pass counts, totals, board_url.
    """
    result = run_pipeline(jd_text, founder_request=founder_request)
    candidates_total = 0
    passed_qa = 0
    try:
        from hermes.integrations.convex_client import list_candidates_for_run

        cands = list_candidates_for_run(result["run_id"])
        candidates_total = len(cands)
        passed_qa = sum(1 for c in cands if c.get("qa_verdict") == "pass")
    except Exception:
        pass

    board_url = os.getenv("RUN_BOARD_URL", "http://localhost:5173")
    return {
        "run_id": result["run_id"],
        "role_type": result.get("role_type"),
        "location": result.get("location"),
        "status": result.get("status"),
        "candidates_total": candidates_total,
        "passed_qa": passed_qa,
        "totals": result.get("totals", {}),
        "board_url": f"{board_url}?run={result['run_id']}",
    }


if __name__ == "__main__":
    mcp.run()
