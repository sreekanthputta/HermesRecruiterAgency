# JSON Contracts — locked before parallel dispatch

All 7 parallel builders read this. Do not deviate. If a contract needs to change, stop and ask.

## 1. `Run`

A single founder request → one Run. One Run has many Candidates and many Traces.

```json
{
  "run_id": "run_2026-07-11T16-30-00_abc123",
  "created_at_iso": "2026-07-11T16:30:00Z",
  "founder_request": "hiring a backend engineer in Hyderabad, Python + Postgres, 3-6 yrs, remote OK",
  "role_type": "backend_engineer",
  "location": "Hyderabad",
  "plan": [
    {"step": 1, "specialist": "role_strategist", "task": "rewrite JD + build rubric"},
    {"step": 2, "specialist": "sourcer", "task": "find 30 profiles matching rubric"},
    {"step": 3, "specialist": "copywriter", "task": "draft outreach per candidate"},
    {"step": 4, "specialist": "qa", "task": "verify claims against evidence"},
    {"step": 5, "specialist": "gmail_draft_writer", "task": "save approved to Drafts"}
  ],
  "rubric": {
    "must_have": ["Python", "Postgres", "3+ yrs backend"],
    "nice_to_have": ["distributed systems", "startup experience"],
    "ignore": ["frontend-only", "students"],
    "weights": {"Python": 3, "Postgres": 2, "3+ yrs backend": 3, "distributed systems": 1}
  },
  "status": "in_progress | done | failed",
  "totals": {
    "tokens_in": 12450,
    "tokens_out": 3200,
    "cost_usd": 0.42,
    "duration_sec": 187
  }
}
```

## 2. `Candidate`

One row per sourced profile.

```json
{
  "candidate_id": "cand_run_...__001",
  "run_id": "run_2026-07-11T16-30-00_abc123",
  "name": "Priya Sharma",
  "profile_url": "https://github.com/priyasharma",
  "evidence_url": "https://github.com/priyasharma/django-shop-api",
  "evidence_summary": "Built a Postgres-backed Django API with 400 stars; recent commits use asyncpg",
  "location": "Hyderabad, India",
  "rubric_score": 8.5,
  "rubric_breakdown": {"Python": 3, "Postgres": 2, "3+ yrs backend": 3, "distributed systems": 0.5},
  "why_match": "Python + Postgres directly demonstrated in top repo",
  "outreach_draft": "Hi Priya — I saw your django-shop-api repo...",
  "qa_verdict": "pass | block",
  "qa_reason": "",
  "gmail_draft_id": "r-1234567890abcdef",
  "status": "sourced | drafted | qa_passed | qa_blocked | in_gmail | rejected_by_founder | advanced_by_founder"
}
```

## 3. `Trace`

One row per agent step. This is the trace-tree data source.

```json
{
  "trace_id": "trc_...",
  "run_id": "run_...",
  "parent_trace_id": null,
  "specialist": "manager | role_strategist | sourcer | copywriter | qa | gmail_draft_writer",
  "task_brief": "rewrite JD + build rubric",
  "input_summary": "founder_request: 'hiring a backend engineer...'",
  "output_summary": "rubric with 3 must-haves, 2 nice-to-haves",
  "output_full": "...",
  "tokens_in": 850,
  "tokens_out": 220,
  "cost_usd": 0.012,
  "model": "gpt-4o",
  "duration_ms": 3400,
  "started_at_iso": "2026-07-11T16:30:05Z",
  "verdict": "accepted | bounced_back | error",
  "bounce_reason": "",
  "revision_of_trace_id": null
}
```

**Trace tree rules:**
- Manager traces have `parent_trace_id = null`
- Specialist traces have `parent_trace_id = <manager trace that dispatched them>`
- Bounce-back: manager writes a new specialist trace with `revision_of_trace_id = <prior specialist trace>`

## 4. `TaskBrief` (manager → specialist)

The exact payload passed to each specialist call.

```json
{
  "specialist": "sourcer",
  "run_id": "run_...",
  "task": "find 30 GitHub profiles in Hyderabad matching rubric",
  "context": {
    "rubric": {...},
    "role_type": "backend_engineer",
    "location": "Hyderabad",
    "prior_output": null,
    "revision_notes": null
  },
  "expected_output_shape": "list of Candidate objects (fields: name, profile_url, evidence_url, evidence_summary, rubric_score, why_match)"
}
```

For bounce-backs, the manager fills `revision_notes` with concrete asks: "Draft 3 hallucinated 'your work at Razorpay' — Priya has no Razorpay in her profile. Rewrite with only evidence-backed claims."

## 5. `QAVerdict`

```json
{
  "candidate_id": "cand_...",
  "verdict": "pass | block",
  "reasons": [
    "Claims 'your Kafka work' — no Kafka in evidence",
    "Claims 3+ years — LinkedIn shows 1.5 years"
  ],
  "unverified_claims": ["Kafka", "3+ years"],
  "verified_claims": ["Python", "Postgres"]
}
```

## 6. Convex table names

- `runs` — matches `Run` shape
- `candidates` — matches `Candidate` shape
- `traces` — matches `Trace` shape

## 7. File paths owned by each builder

| Builder | Owns |
|---|---|
| A (manager) | `hermes/manager.py`, `hermes/specialists/*.py`, `hermes/prompts/*.md` |
| B (sourcer) | `hermes/specialists/sourcer.py`, `hermes/integrations/linkup.py`, `hermes/integrations/github.py` |
| C (gmail) | `hermes/specialists/gmail_writer.py`, `hermes/integrations/gmail.py` |
| D (convex) | `convex/schema.ts`, `convex/candidates.ts`, `convex/runs.ts`, `convex/traces.ts`, `hermes/integrations/convex_client.py` |
| E (web) | `web/**` |
| F (evals) | `evals/**`, `.github/workflows/eval.yml` |
| G (elevenlabs) | `hermes/integrations/elevenlabs.py`, `hermes/narrator.py` |

**No builder writes outside its lane.** Shared config only via `.env`.
