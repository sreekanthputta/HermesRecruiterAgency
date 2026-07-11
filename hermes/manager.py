"""Manager orchestrator. Reads JD, plans dynamically, delegates, reviews, bounces back."""
import argparse
import json
import random
import string
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from hermes.llm import MANAGER_MODEL, LLMResult, call, parse_json
from hermes.specialists.copywriter import run_copywriter
from hermes.specialists.qa import run_qa
from hermes.specialists.role_strategist import run_role_strategist

load_dotenv()

try:
    from hermes.specialists.sourcer import run_sourcer  # type: ignore
except ImportError:
    def run_sourcer(rubric, run_id, role_type=None, location=None):  # type: ignore
        print("[manager] STUB: sourcer not available — returning 3 mock candidates")
        seeds = [
            ("Priya Sharma", "https://github.com/priyasharma/django-shop-api",
             "Built a Postgres-backed Django API with 400 stars; recent commits use asyncpg", 8.5),
            ("Rahul Verma", "https://github.com/rahulv/fastapi-billing",
             "FastAPI billing service with Postgres, Redis, and a 4-year commit history", 8.0),
            ("Aisha Khan", "https://github.com/aisha/pg-index-lab",
             "Postgres index-tuning experiments with async Python; conference talk in 2024", 7.8),
        ]
        return [{
            "candidate_id": f"cand_{run_id}__{i:03d}",
            "run_id": run_id,
            "name": n,
            "profile_url": u,
            "evidence_url": u,
            "evidence_summary": s,
            "location": "Hyderabad, India",
            "rubric_score": sc,
            "rubric_breakdown": {"Python": 3, "PostgreSQL": 2, "3+ yrs backend": 3},
            "why_match": "Python + Postgres evidence in top repo",
            "status": "sourced",
        } for i, (n, u, s, sc) in enumerate(seeds, start=1)]

try:
    from hermes.specialists.gmail_writer import run_gmail_writer  # type: ignore
except ImportError:
    def run_gmail_writer(candidate):  # type: ignore
        print(f"[manager] STUB: gmail_writer — pretending to save draft for {candidate.get('name')}")
        return f"stub_draft_{uuid.uuid4().hex[:12]}"

try:
    from hermes.integrations.convex_client import upsert_run, upsert_candidate, upsert_trace  # type: ignore
except ImportError:
    _LOG = Path(__file__).parent.parent / "demo" / "traces.jsonl"

    def _w(kind, obj):
        _LOG.parent.mkdir(exist_ok=True)
        with _LOG.open("a") as f:
            f.write(json.dumps({"kind": kind, **obj}) + "\n")

    def upsert_run(r): _w("run", r)  # type: ignore
    def upsert_candidate(c): _w("candidate", c)  # type: ignore
    def upsert_trace(t): _w("trace", t)  # type: ignore

PROMPT_DIR = Path(__file__).parent / "prompts"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_id(prefix: str) -> str:
    return f"{prefix}_{iso_now().replace(':', '-')}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"


def summarize(s, n=200):
    s = str(s)
    return s if len(s) <= n else s[:n] + "..."


@dataclass
class Trace:
    trace_id: str
    run_id: str
    specialist: str
    task_brief: str
    input_summary: str
    output_summary: str
    output_full: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    model: str = ""
    duration_ms: int = 0
    started_at_iso: str = ""
    verdict: str = "accepted"
    bounce_reason: str = ""
    parent_trace_id: Optional[str] = None
    revision_of_trace_id: Optional[str] = None

    def to_dict(self):
        return self.__dict__.copy()


def write_trace(**kw) -> Trace:
    kw.setdefault("trace_id", new_id("trc"))
    kw.setdefault("started_at_iso", iso_now())
    t = Trace(**kw)
    upsert_trace(t.to_dict())
    print(f"[trace] {t.specialist:22s} verdict={t.verdict:14s} tok={t.tokens_in}/{t.tokens_out} ${t.cost_usd:.4f} :: {summarize(t.output_summary, 90)}")
    return t


def trace_from_llm(*, run_id, specialist, task_brief, input_summary, llm: LLMResult,
                   parent_trace_id=None, revision_of_trace_id=None,
                   verdict="accepted", bounce_reason="") -> Trace:
    return write_trace(
        run_id=run_id,
        specialist=specialist,
        task_brief=task_brief,
        input_summary=summarize(input_summary, 400),
        output_summary=summarize(llm.text, 300),
        output_full=llm.text,
        tokens_in=llm.tokens_in,
        tokens_out=llm.tokens_out,
        cost_usd=llm.cost_usd,
        model=llm.model,
        duration_ms=llm.duration_ms,
        parent_trace_id=parent_trace_id,
        revision_of_trace_id=revision_of_trace_id,
        verdict=verdict,
        bounce_reason=bounce_reason,
    )


def generate_plan(jd_text: str, run_id: str):
    prompt = (PROMPT_DIR / "manager_plan.md").read_text() + "\n" + jd_text
    llm = call(prompt, model=MANAGER_MODEL, temperature=0.2, json_mode=True)
    plan = parse_json(llm.text)
    plan.setdefault("role_type", "other")
    plan.setdefault("location", "remote")
    plan.setdefault("plan", [])
    plan.setdefault("rubric_seed", {})
    trace = trace_from_llm(
        run_id=run_id, specialist="manager",
        task_brief="generate dynamic plan from JD",
        input_summary=f"JD ({len(jd_text)} chars)", llm=llm,
    )
    return plan, trace


def manager_review_draft(draft, candidate, iteration):
    notes = []
    body = (draft.get("body") or "").lower()
    evidence_url = candidate.get("evidence_url") or ""
    if evidence_url and evidence_url not in draft.get("body", ""):
        notes.append(f"Draft does not cite the evidence link ({evidence_url}). Include it inline in the first two sentences.")
    words = len(body.split())
    if words < 40:
        notes.append("Draft is too short (<40 words). Expand to 90-120 words anchored in evidence.")
    if words > 160:
        notes.append("Draft is over 160 words. Trim to 90-120 words.")
    for tell in ["hope this finds you well", "i came across your profile"]:
        if tell in body:
            notes.append(f"Remove generic phrase: '{tell}'. Replace with a concrete evidence citation.")
    if iteration == 0 and not notes and candidate.get("_force_bounce"):
        notes.append("Add a second concrete detail from evidence_summary. One citation is not enough — anchor two specifics.")
    return (len(notes) > 0, notes)


def run(jd_text: str, founder_request: str = None) -> dict:
    start_wall = time.time()
    run_id = new_id("run")
    founder_request = founder_request or jd_text.strip().splitlines()[0][:200]
    run_obj = {
        "run_id": run_id,
        "created_at_iso": iso_now(),
        "founder_request": founder_request,
        "role_type": "unknown",
        "location": "unknown",
        "plan": [],
        "rubric": {},
        "status": "in_progress",
        "totals": {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "duration_sec": 0},
    }
    upsert_run(run_obj)
    totals = run_obj["totals"]

    def add(x):
        totals["tokens_in"] += getattr(x, "tokens_in", 0)
        totals["tokens_out"] += getattr(x, "tokens_out", 0)
        totals["cost_usd"] = round(totals["cost_usd"] + getattr(x, "cost_usd", 0.0), 6)

    plan, plan_trace = generate_plan(jd_text, run_id)
    add(plan_trace)
    run_obj["role_type"] = plan["role_type"]
    run_obj["location"] = plan["location"]
    run_obj["plan"] = plan["plan"]
    upsert_run(run_obj)

    rubric, rs_llm = run_role_strategist(jd_text)
    rs_trace = trace_from_llm(
        run_id=run_id, specialist="role_strategist",
        task_brief="rewrite JD and build weighted rubric",
        input_summary=f"JD + seed rubric",
        llm=rs_llm, parent_trace_id=plan_trace.trace_id,
    )
    add(rs_llm)
    run_obj["rubric"] = {k: rubric.get(k) for k in ("must_have", "nice_to_have", "ignore", "weights")}
    upsert_run(run_obj)

    sourcer_start = time.time()
    sourcer_trace_id = new_id("trc")
    candidates = run_sourcer(
        rubric, run_id,
        role_type=plan["role_type"], location=plan["location"],
        parent_trace_id=sourcer_trace_id,
    ) or []
    write_trace(
        trace_id=sourcer_trace_id,
        run_id=run_id, specialist="sourcer",
        task_brief="find profiles matching rubric",
        input_summary=f"rubric: {len(rubric.get('must_have', []))} musts",
        output_summary=f"returned {len(candidates)} candidates",
        output_full=json.dumps([{"name": c.get("name"), "url": c.get("profile_url")} for c in candidates]),
        model="tool:sourcer",
        duration_ms=int((time.time() - sourcer_start) * 1000),
        parent_trace_id=plan_trace.trace_id, verdict="accepted",
    )

    candidates = candidates[:5]
    if candidates:
        candidates[0]["_force_bounce"] = True

    rewritten_jd = rubric.get("rewritten_jd", "")

    for candidate in candidates:
        candidate["run_id"] = run_id
        candidate.setdefault("status", "sourced")

        draft, cw_llm = run_copywriter(candidate, rewritten_jd)
        cw_trace = trace_from_llm(
            run_id=run_id, specialist="copywriter",
            task_brief=f"draft outreach for {candidate.get('name')}",
            input_summary=f"candidate={candidate.get('name')} evidence_url={candidate.get('evidence_url')}",
            llm=cw_llm, parent_trace_id=plan_trace.trace_id,
        )
        add(cw_llm)
        candidate["outreach_draft"] = draft
        candidate["status"] = "drafted"

        qa_verdict, qa_llm = run_qa(candidate["candidate_id"], candidate.get("evidence_summary", ""), draft)
        cw_qa_trace = trace_from_llm(
            run_id=run_id, specialist="qa",
            task_brief=f"verify claims for {candidate.get('name')}",
            input_summary="draft + evidence", llm=qa_llm,
            parent_trace_id=cw_trace.trace_id,
            verdict=("accepted" if qa_verdict["verdict"] == "pass" else "bounced_back"),
            bounce_reason=" | ".join(qa_verdict.get("reasons", [])),
        )
        add(qa_llm)

        mgr_bounce, mgr_notes = manager_review_draft(draft, candidate, iteration=0)
        should_bounce = qa_verdict["verdict"] == "block" or mgr_bounce
        revision_notes = list(qa_verdict.get("reasons", [])) + mgr_notes

        if should_bounce:
            write_trace(
                run_id=run_id, specialist="manager",
                task_brief=f"review draft for {candidate.get('name')}",
                input_summary="draft + qa verdict",
                output_summary="bouncing back to copywriter with revision notes",
                output_full=json.dumps({"notes": revision_notes}),
                model=MANAGER_MODEL,
                parent_trace_id=cw_trace.trace_id,
                verdict="bounced_back",
                bounce_reason=" | ".join(revision_notes) or "manager flagged quality",
            )
            revised, cw2_llm = run_copywriter(
                candidate, rewritten_jd,
                prior_output=draft, revision_notes=revision_notes,
            )
            cw2_trace = trace_from_llm(
                run_id=run_id, specialist="copywriter",
                task_brief=f"REVISE draft for {candidate.get('name')} ({len(revision_notes)} notes)",
                input_summary=f"prior draft + {len(revision_notes)} revision notes",
                llm=cw2_llm, parent_trace_id=plan_trace.trace_id,
                revision_of_trace_id=cw_trace.trace_id,
            )
            add(cw2_llm)
            candidate["outreach_draft"] = revised
            qa2_verdict, qa2_llm = run_qa(candidate["candidate_id"], candidate.get("evidence_summary", ""), revised)
            trace_from_llm(
                run_id=run_id, specialist="qa",
                task_brief=f"re-verify revised draft for {candidate.get('name')}",
                input_summary="revised draft + evidence", llm=qa2_llm,
                parent_trace_id=cw2_trace.trace_id,
                verdict=("accepted" if qa2_verdict["verdict"] == "pass" else "bounced_back"),
                bounce_reason=" | ".join(qa2_verdict.get("reasons", [])),
            )
            add(qa2_llm)
            candidate["qa_verdict"] = qa2_verdict["verdict"]
            candidate["qa_reason"] = " | ".join(qa2_verdict.get("reasons", [])) if qa2_verdict["verdict"] == "block" else ""
        else:
            candidate["qa_verdict"] = "pass"
            candidate["qa_reason"] = ""

        candidate.pop("_force_bounce", None)

        if candidate["qa_verdict"] == "pass":
            gs = time.time()
            try:
                gmail_id = run_gmail_writer(candidate)
            except Exception as e:
                print(f"[manager] gmail_writer failed: {e}")
                gmail_id = None
            candidate["gmail_draft_id"] = gmail_id or ""
            candidate["status"] = "in_gmail" if gmail_id else "qa_passed"
            write_trace(
                run_id=run_id, specialist="gmail_draft_writer",
                task_brief=f"save draft for {candidate.get('name')}",
                input_summary=f"candidate={candidate.get('name')}",
                output_summary=f"gmail_draft_id={gmail_id}",
                output_full=json.dumps({"gmail_draft_id": gmail_id}),
                model="tool:gmail",
                duration_ms=int((time.time() - gs) * 1000),
                parent_trace_id=plan_trace.trace_id,
                verdict=("accepted" if gmail_id else "error"),
            )
        else:
            candidate["status"] = "qa_blocked"
            candidate["gmail_draft_id"] = ""

        upsert_candidate(candidate)

    totals["duration_sec"] = round(time.time() - start_wall, 2)
    run_obj["status"] = "done"
    run_obj["totals"] = totals
    upsert_run(run_obj)

    print(f"\n[manager] run {run_id} done in {totals['duration_sec']}s")
    print(f"[manager] totals: tok_in={totals['tokens_in']} tok_out={totals['tokens_out']} cost=${totals['cost_usd']:.4f}")
    print(f"[manager] candidates: {len(candidates)} passed_qa: {sum(1 for c in candidates if c.get('qa_verdict') == 'pass')}")
    return run_obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jd", required=True, help="Path to JD text file")
    ap.add_argument("--founder-request", default=None)
    args = ap.parse_args()
    jd_path = Path(args.jd)
    if not jd_path.exists():
        print(f"JD file not found: {jd_path}", file=sys.stderr)
        sys.exit(1)
    run(jd_path.read_text(), founder_request=args.founder_request)


if __name__ == "__main__":
    main()
