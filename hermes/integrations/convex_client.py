"""Convex client with local JSON fallback.

Other builders import:
    from hermes.integrations.convex_client import (
        upsert_run, upsert_candidate, upsert_trace,
        get_run, list_candidates_for_run, list_traces_for_run,
    )

If CONVEX_URL is unset or connection fails, all writes/reads go to
demo/data/{runs,candidates,traces}.json so the demo works without
running `npx convex dev`.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any

try:
    import urllib.request as _urlreq
    import urllib.error as _urlerr
except Exception:  # pragma: no cover
    _urlreq = None
    _urlerr = None

# Optional Convex Python SDK (only used if installed)
try:
    from convex import ConvexClient as _ConvexSDK  # type: ignore
except Exception:
    _ConvexSDK = None


_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "demo" / "data"
_RUNS_FILE = _DATA_DIR / "runs.json"
_CANDS_FILE = _DATA_DIR / "candidates.json"
_TRACES_FILE = _DATA_DIR / "traces.json"

_LOCK = Lock()
_MODE_LOGGED = False


def _log_mode(mode: str) -> None:
    global _MODE_LOGGED
    if not _MODE_LOGGED:
        print(f"[convex_client] {mode}")
        _MODE_LOGGED = True


def _convex_url() -> str:
    return (os.getenv("CONVEX_URL") or "").strip().rstrip("/")


def _ensure_local_files() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    for f in (_RUNS_FILE, _CANDS_FILE, _TRACES_FILE):
        if not f.exists():
            f.write_text("[]")


def _read_local(path: Path) -> list[dict]:
    _ensure_local_files()
    try:
        return json.loads(path.read_text() or "[]")
    except json.JSONDecodeError:
        return []


def _write_local(path: Path, rows: list[dict]) -> None:
    _ensure_local_files()
    path.write_text(json.dumps(rows, indent=2, default=str))


def _local_upsert(path: Path, key: str, row: dict) -> str:
    with _LOCK:
        rows = _read_local(path)
        val = row[key]
        for i, r in enumerate(rows):
            if r.get(key) == val:
                rows[i] = {**r, **row}
                _write_local(path, rows)
                return val
        rows.append(row)
        _write_local(path, rows)
        return val


# ---------- Convex HTTP transport ----------

def _http_call(kind: str, path: str, args: dict) -> Any:
    """kind: 'mutation' or 'query'. Returns parsed JSON 'value'."""
    if _urlreq is None:
        raise RuntimeError("urllib unavailable")
    url = f"{_convex_url()}/api/{kind}"
    body = json.dumps({"path": path, "args": args, "format": "json"}).encode("utf-8")
    req = _urlreq.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with _urlreq.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("status") != "success":
        raise RuntimeError(f"convex {kind} {path} failed: {data}")
    return data.get("value")


def _try_convex(kind: str, path: str, args: dict) -> tuple[bool, Any]:
    if not _convex_url():
        return False, None
    try:
        v = _http_call(kind, path, args)
        _log_mode("Convex live mode")
        return True, v
    except Exception as e:
        _log_mode(f"Local fallback mode (convex error: {type(e).__name__})")
        return False, None


# ---------- Public API ----------

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_trace_id() -> str:
    return "trc_" + uuid.uuid4().hex[:12]


def upsert_run(run: dict) -> str:
    run = dict(run)
    if "run_id" not in run:
        raise ValueError("run.run_id required")
    run.setdefault("created_at_iso", _now_iso())
    run.setdefault("status", "in_progress")
    run.setdefault("role_type", run.get("role_type", "unknown"))
    run.setdefault("founder_request", run.get("founder_request", ""))
    run.setdefault("plan", run.get("plan", []))
    run = {k: v for k, v in run.items() if v is not None}
    ok, _ = _try_convex("mutation", "runs:upsert", run)
    if ok:
        return run["run_id"]
    return _local_upsert(_RUNS_FILE, "run_id", run)


def upsert_candidate(candidate: dict) -> str:
    candidate = dict(candidate)
    if "candidate_id" not in candidate:
        raise ValueError("candidate.candidate_id required")
    candidate.setdefault("status", "sourced")
    # Convex schema stores outreach_draft as string; JSON-encode dict drafts.
    # rubric_breakdown keys may contain non-ASCII (em-dash) — Convex rejects
    # those as field names, so serialise the whole thing to a JSON string.
    if isinstance(candidate.get("outreach_draft"), (dict, list)):
        candidate["outreach_draft"] = json.dumps(candidate["outreach_draft"], ensure_ascii=False)
    if isinstance(candidate.get("rubric_breakdown"), (dict, list)):
        candidate["rubric_breakdown"] = json.dumps(candidate["rubric_breakdown"], ensure_ascii=False)
    candidate = {k: v for k, v in candidate.items() if v is not None}
    ok, _ = _try_convex("mutation", "candidates:upsert", candidate)
    if ok:
        return candidate["candidate_id"]
    return _local_upsert(_CANDS_FILE, "candidate_id", candidate)


def upsert_trace(trace: dict) -> str:
    trace = dict(trace)
    trace.setdefault("trace_id", _new_trace_id())
    trace.setdefault("started_at_iso", _now_iso())
    if "run_id" not in trace:
        raise ValueError("trace.run_id required")
    if "specialist" not in trace:
        raise ValueError("trace.specialist required")
    # Convex v.optional(...) means "may be omitted", not "may be null" —
    # strip None-valued optionals before sending.
    trace = {k: v for k, v in trace.items() if v is not None}
    ok, _ = _try_convex("mutation", "traces:upsert", trace)
    if ok:
        return trace["trace_id"]
    return _local_upsert(_TRACES_FILE, "trace_id", trace)


def get_run(run_id: str) -> dict | None:
    ok, v = _try_convex("query", "runs:getByRunId", {"run_id": run_id})
    if ok:
        return v
    for r in _read_local(_RUNS_FILE):
        if r.get("run_id") == run_id:
            return r
    return None


def list_candidates_for_run(run_id: str) -> list[dict]:
    ok, v = _try_convex("query", "candidates:listForRun", {"run_id": run_id})
    if ok:
        return v or []
    return [c for c in _read_local(_CANDS_FILE) if c.get("run_id") == run_id]


def list_traces_for_run(run_id: str) -> list[dict]:
    ok, v = _try_convex("query", "traces:listForRun", {"run_id": run_id})
    if ok:
        return v or []
    rows = [t for t in _read_local(_TRACES_FILE) if t.get("run_id") == run_id]
    rows.sort(key=lambda r: r.get("started_at_iso", ""))
    return rows


__all__ = [
    "upsert_run",
    "upsert_candidate",
    "upsert_trace",
    "get_run",
    "list_candidates_for_run",
    "list_traces_for_run",
]
