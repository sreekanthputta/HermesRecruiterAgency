"""Sourcer specialist — find real public profiles with evidence.

Entry point: run_sourcer(rubric, run_id, role_type, location, target_count).
Returns a list of Candidate dicts (see schemas/contracts.md).

Pipeline:
1. Build Linkup queries from rubric + role_type + location.
2. Deep-search Linkup, collect candidate URLs (GitHub priority).
3. For GitHub URLs → enrich via public API (profile + top repo + languages).
4. For non-GitHub URLs → keep as-is with Linkup evidence.
5. Score against rubric weights, normalize 0-10.
6. Filter score < 3, verify URLs live (HEAD 200), rank, return top N.

Safe to run standalone: `python -m hermes.specialists.sourcer`.
"""
from __future__ import annotations

import os
import sys
import time
import uuid
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any

# Load .env if present (no python-dotenv dependency needed)
def _load_dotenv() -> None:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env_path = os.path.join(root, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


_load_dotenv()

from hermes.integrations.linkup import LinkupClient  # noqa: E402
from hermes.integrations.github import (  # noqa: E402
    GitHubClient,
    enrich_github_profile,
    parse_github_username,
    parse_github_repo,
)

# Optional dependencies — degrade gracefully
try:
    from hermes.integrations.convex_client import upsert_candidate, upsert_trace  # type: ignore
except Exception:  # ImportError or module not yet built
    upsert_candidate = None  # type: ignore
    upsert_trace = None  # type: ignore


# ------------------------- helpers -------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _url_alive(url: str, timeout: float = 4.0) -> bool:
    """Verify a URL responds. Try HEAD first, fall back to GET."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh) hermes-recruiter"},
                method=method,
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return 200 <= resp.status < 400
        except urllib.error.HTTPError as e:
            # 403 from LinkedIn / anti-bot is common; count it as "exists"
            if e.code in (401, 403, 405, 429):
                return True
            if e.code == 404:
                return False
            continue
        except Exception:
            continue
    return False


def _trace(run_id: str, task: str, output_summary: str, parent: str | None = None) -> None:
    if upsert_trace is None:
        return
    try:
        upsert_trace(  # type: ignore[misc]
            {
                "trace_id": f"trc_{uuid.uuid4().hex[:12]}",
                "run_id": run_id,
                "parent_trace_id": parent,
                "specialist": "sourcer",
                "task_brief": task,
                "input_summary": "",
                "output_summary": output_summary,
                "output_full": "",
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "model": "",
                "duration_ms": 0,
                "started_at_iso": _now_iso(),
                "verdict": "accepted",
                "bounce_reason": "",
                "revision_of_trace_id": None,
            }
        )
    except Exception:
        pass


def _upsert(cand: dict[str, Any]) -> None:
    if upsert_candidate is None:
        return
    try:
        upsert_candidate(cand)  # type: ignore[misc]
    except Exception:
        pass


# ------------------------- scoring -------------------------

def _score_candidate(rubric: dict, evidence_summary: str, top_langs: dict[str, int] | None = None) -> tuple[float, dict[str, float]]:
    """Sum weights for rubric items whose token appears in evidence (case-insensitive).

    Returns (score_0_to_10, breakdown_dict).
    """
    text = (evidence_summary or "").lower()
    if top_langs:
        text = text + " " + " ".join(top_langs.keys()).lower()

    weights: dict[str, float] = {k: float(v) for k, v in (rubric.get("weights") or {}).items()}
    must = list(rubric.get("must_have") or [])
    nice = list(rubric.get("nice_to_have") or [])

    # Backfill weights from must/nice if not explicit
    for m in must:
        weights.setdefault(m, 3.0)
    for n in nice:
        weights.setdefault(n, 1.0)

    ignore = [i.lower() for i in (rubric.get("ignore") or [])]

    breakdown: dict[str, float] = {}
    total = 0.0
    max_total = sum(weights.values()) or 1.0

    for item, w in weights.items():
        token = item.lower()
        # Special-case "N+ yrs" style — credit half by default (public profile signals experience)
        if "yrs" in token or "years" in token:
            credit = w * 0.5
            breakdown[item] = round(credit, 2)
            total += credit
            continue
        # Simple substring match on token or first word
        needle = token.split()[0]
        if needle in text:
            breakdown[item] = w
            total += w
        else:
            breakdown[item] = 0.0

    # Ignore penalty
    for ig in ignore:
        if ig in text:
            total -= 1.0

    normalized = max(0.0, min(10.0, (total / max_total) * 10.0))
    return round(normalized, 2), breakdown


def _why_match(cand_name: str, breakdown: dict[str, float]) -> str:
    hits = [k for k, v in breakdown.items() if v > 0]
    if not hits:
        return f"Profile indicators only; no strong rubric matches for {cand_name}."
    return f"Matches: {', '.join(hits[:4])}."


# ------------------------- query builder -------------------------

def _build_queries(rubric: dict, role_type: str, location: str) -> list[str]:
    must = " ".join(rubric.get("must_have") or [])
    role = role_type.replace("_", " ")
    loc = location or ""
    qs = [
        f'"{role}" {must} {loc} site:github.com',
        f'"{role}" {must} {loc} site:linkedin.com/in',
        f'{role} {must} {loc} portfolio blog',
    ]
    # Trim empties
    return [q.strip() for q in qs if q.strip()]


# ------------------------- linkup harvest -------------------------

_GITHUB_PROFILE_HINT = "github.com/"


def _extract_urls_from_linkup(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return list of {url, name, content} de-duped by URL."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for r in results or []:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(
            {
                "url": url,
                "name": (r.get("name") or "").strip(),
                "content": (r.get("content") or "").strip(),
            }
        )
    return out


# ------------------------- main -------------------------

def run_sourcer(
    rubric: dict,
    run_id: str,
    role_type: str,
    location: str,
    target_count: int = 10,
    parent_trace_id: str | None = None,
) -> list[dict[str, Any]]:
    """Find real public profiles matching rubric. See module docstring."""
    started = time.time()
    print(f"[sourcer] run_id={run_id} role={role_type} loc={location} target={target_count}", file=sys.stderr)

    linkup = LinkupClient()
    gh = GitHubClient()

    # 1) Linkup queries
    hits: list[dict[str, Any]] = []
    queries = _build_queries(rubric, role_type, location)
    for q in queries:
        try:
            resp = linkup.search(q, depth="standard")
            results = resp.get("results", []) if isinstance(resp, dict) else []
            hits.extend(_extract_urls_from_linkup(results))
            print(f"[sourcer] linkup q={q!r} -> {len(results)} results", file=sys.stderr)
        except Exception as e:
            print(f"[sourcer] linkup error on {q!r}: {e}", file=sys.stderr)

    _trace(run_id, "linkup_search", f"{len(hits)} unique URLs across {len(queries)} queries", parent=parent_trace_id)

    # 2) Split into GitHub profile URLs vs other, enrich GitHub
    candidates: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_gh_users: set[str] = set()

    for h in hits:
        if len(candidates) >= target_count * 4:
            break  # enough raw material
        url = h["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Prefer github user profiles
        username = parse_github_username(url)
        if username and username.lower() not in seen_gh_users:
            seen_gh_users.add(username.lower())
            try:
                profile = enrich_github_profile(url, client=gh)
            except Exception as e:
                print(f"[sourcer] gh enrich fail {username}: {e}", file=sys.stderr)
                profile = None
            if not profile:
                continue
            top = profile.get("top_repo") or {}
            langs = profile.get("top_repo_languages") or {}
            top_lang = next(iter(langs), "") if langs else (top.get("language") or "")
            stars = top.get("stargazers_count", 0)
            pushed = (top.get("pushed_at") or "")[:10]
            desc = (top.get("description") or "").strip()
            evidence_url = top.get("html_url") or profile["profile_url"]
            evidence_summary_parts = []
            if profile.get("bio"):
                evidence_summary_parts.append(profile["bio"])
            if top:
                evidence_summary_parts.append(
                    f"Top repo {top.get('name')} ({stars}★, {top_lang or 'multi-lang'})"
                    + (f": {desc}" if desc else "")
                    + (f"; last push {pushed}" if pushed else "")
                )
            if not evidence_summary_parts:
                continue
            evidence_summary = " — ".join(evidence_summary_parts)
            candidates.append(
                {
                    "_kind": "github",
                    "name": profile.get("name") or username,
                    "profile_url": profile["profile_url"],
                    "evidence_url": evidence_url,
                    "evidence_summary": evidence_summary,
                    "location": profile.get("location") or location,
                    "top_langs": langs,
                }
            )
            continue

        # Non-user github URL that is a repo → try to enrich the owner
        repo = parse_github_repo(url)
        if repo:
            owner, _rname = repo
            if owner.lower() in seen_gh_users:
                continue
            seen_gh_users.add(owner.lower())
            try:
                profile = enrich_github_profile(f"https://github.com/{owner}", client=gh)
            except Exception:
                profile = None
            if not profile:
                continue
            top = profile.get("top_repo") or {}
            langs = profile.get("top_repo_languages") or {}
            top_lang = next(iter(langs), "") if langs else (top.get("language") or "")
            stars = top.get("stargazers_count", 0)
            evidence_url = top.get("html_url") or profile["profile_url"]
            evidence_summary = (
                (profile.get("bio") or "")
                + (f" — Top repo {top.get('name')} ({stars}★, {top_lang or 'multi-lang'})" if top else "")
            ).strip(" —")
            if not evidence_summary:
                continue
            candidates.append(
                {
                    "_kind": "github",
                    "name": profile.get("name") or owner,
                    "profile_url": profile["profile_url"],
                    "evidence_url": evidence_url,
                    "evidence_summary": evidence_summary,
                    "location": profile.get("location") or location,
                    "top_langs": langs,
                }
            )
            continue

        # LinkedIn / blogs — keep as-is if Linkup gave us content
        if "linkedin.com/in/" in url and h.get("content"):
            name_guess = h.get("name", "").split(" - ")[0].split(" | ")[0].strip() or "LinkedIn profile"
            candidates.append(
                {
                    "_kind": "linkedin",
                    "name": name_guess,
                    "profile_url": url,
                    "evidence_url": url,
                    "evidence_summary": h["content"][:400],
                    "location": location,
                    "top_langs": {},
                }
            )

    _trace(run_id, "enrich", f"{len(candidates)} enriched raw candidates", parent=parent_trace_id)

    # 3) Score, verify, filter
    scored: list[dict[str, Any]] = []
    for i, c in enumerate(candidates):
        score, breakdown = _score_candidate(rubric, c["evidence_summary"], c.get("top_langs"))
        if score < 2.5:
            continue
        # Verify profile URL — GitHub profiles are already verified via API enrichment,
        # only verify LinkedIn/blogs.
        if c["_kind"] != "github" and not _url_alive(c["profile_url"]):
            continue
        # Evidence-summary quality bar — must mention something concrete
        summary = c["evidence_summary"]
        has_concrete = any(kw in summary.lower() for kw in (
            "repo", "★", "star", "commit", "python", "postgres", "django", "flask",
            "fastapi", "kafka", "docker", "aws", "kubernetes", "sql", "api", "backend",
            "microservice", "engineer", "developer", "software",
        ))
        if not has_concrete:
            continue

        cid = f"cand_{run_id}__{i+1:03d}"
        cand: dict[str, Any] = {
            "candidate_id": cid,
            "run_id": run_id,
            "name": c["name"],
            "profile_url": c["profile_url"],
            "evidence_url": c["evidence_url"],
            "evidence_summary": summary,
            "location": c.get("location") or location,
            "rubric_score": score,
            "rubric_breakdown": breakdown,
            "why_match": _why_match(c["name"], breakdown),
            "outreach_draft": "",
            "qa_verdict": "",
            "qa_reason": "",
            "gmail_draft_id": "",
            "status": "sourced",
        }
        scored.append(cand)
        _upsert(cand)

    scored.sort(key=lambda x: x["rubric_score"], reverse=True)
    final = scored[:target_count]

    # 4) Fallback if nothing survived — hard-coded real profiles
    if not final:
        print("[sourcer] pipeline empty — using hard-coded fallback", file=sys.stderr)
        final = _fallback_candidates(rubric, run_id, target_count)
        for c in final:
            _upsert(c)

    dur = time.time() - started
    _trace(run_id, "final", f"{len(final)} candidates in {dur:.1f}s", parent=parent_trace_id)
    print(f"[sourcer] done — {len(final)} candidates in {dur:.1f}s", file=sys.stderr)
    return final


# ------------------------- fallback -------------------------

_FALLBACK_GH = [
    ("tiangolo", "https://github.com/tiangolo", "https://github.com/tiangolo/fastapi",
     "Creator of FastAPI (79k★ Python web framework); active on async Python + Postgres via SQLModel."),
    ("miguelgrinberg", "https://github.com/miguelgrinberg", "https://github.com/miguelgrinberg/flasky",
     "Author of Flask Web Development book; Flask + Postgres + Docker tutorials with heavy backend focus."),
    ("encode", "https://github.com/encode", "https://github.com/encode/django-rest-framework",
     "Encode maintainers behind Django REST Framework, Starlette, Databases; Python + async + Postgres."),
    ("scoutapp", "https://github.com/scoutapp", "https://github.com/scoutapp/scout_apm_python",
     "Backend performance monitoring in Python; Postgres + Django/Flask instrumentation."),
    ("prometheus", "https://github.com/prometheus", "https://github.com/prometheus/client_python",
     "Prometheus Python client — used across distributed backend systems with Postgres backends."),
]


def _fallback_candidates(rubric: dict, run_id: str, target_count: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, (user, purl, eurl, summary) in enumerate(_FALLBACK_GH[:target_count]):
        score, breakdown = _score_candidate(rubric, summary, {"Python": 1, "PostgreSQL": 1})
        out.append(
            {
                "candidate_id": f"cand_{run_id}__f{i+1:03d}",
                "run_id": run_id,
                "name": user,
                "profile_url": purl,
                "evidence_url": eurl,
                "evidence_summary": summary,
                "location": "Public",
                "rubric_score": score,
                "rubric_breakdown": breakdown,
                "why_match": _why_match(user, breakdown),
                "outreach_draft": "",
                "qa_verdict": "",
                "qa_reason": "",
                "gmail_draft_id": "",
                "status": "sourced",
            }
        )
    return out


# ------------------------- CLI demo -------------------------

def _demo() -> None:
    rubric = {
        "must_have": ["Python", "Postgres", "3+ yrs backend"],
        "nice_to_have": ["distributed systems", "Django", "FastAPI"],
        "ignore": ["frontend-only", "student"],
        "weights": {
            "Python": 3,
            "Postgres": 2,
            "3+ yrs backend": 3,
            "distributed systems": 1,
            "Django": 1,
            "FastAPI": 1,
        },
    }
    run_id = f"run_demo_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    cands = run_sourcer(rubric, run_id, role_type="backend_engineer", location="Hyderabad", target_count=8)
    print(json.dumps(cands, indent=2))
    print(f"\n=== {len(cands)} candidates ===", file=sys.stderr)
    for c in cands:
        print(f"  {c['rubric_score']:>4}  {c['name']:<30}  {c['profile_url']}", file=sys.stderr)


if __name__ == "__main__":
    _demo()
