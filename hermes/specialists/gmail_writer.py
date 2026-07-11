"""
Gmail Draft Writer specialist.

Given an approved Candidate, save the outreach as a Gmail Draft in the founder's
own account (so they can review + hit Send manually). Always mirror the MIME
content to demo/drafts/<candidate_id>.eml for demo/judge visibility.

NEVER SENDS.
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Optional

from hermes.integrations import gmail as gmail_int


DEMO_DRAFTS_DIR = Path("demo/drafts")


def _slug(s: str) -> str:
    """Short filesystem-safe slug from an arbitrary string."""
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", s or "").strip("_")
    return s[:60] or "candidate"


def _candidate_id(candidate: dict) -> str:
    """Prefer explicit candidate_id, else derive a stable-ish one from name+url."""
    cid = candidate.get("candidate_id")
    if cid:
        return cid
    seed = f"{candidate.get('name','')}-{candidate.get('profile_url','')}"
    return "cand_" + _slug(seed)


def _subject_for(candidate: dict) -> str:
    role = os.getenv("DEMO_ROLE_SNIPPET") or "backend engineer role"
    founder = os.getenv("FOUNDER_NAME") or "a solo founder in India"
    name = candidate.get("name") or "there"
    return f"Quick note re: {role} — from {founder} (candidate: {name})"


def _to_address(candidate: dict) -> str:
    """
    We route drafts to the founder's own account (GMAIL_TARGET_ACCOUNT). The
    founder updates the To: to the real candidate email before sending. If no
    target is configured, fall back to `me` (Gmail treats that as the auth'd
    account in MIME headers too — imperfect but visible).
    """
    return os.getenv("GMAIL_TARGET_ACCOUNT") or "me@localhost"


def _write_eml_mirror(candidate_id: str, mime_str: str) -> Path:
    DEMO_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = DEMO_DRAFTS_DIR / f"{candidate_id}.eml"
    path.write_text(mime_str, encoding="utf-8")
    return path


def run_gmail_writer(candidate: dict) -> str:
    """
    Entry point. See module docstring.

    Fields consumed from `candidate`:
      - name             (str)   required-ish, defaults to 'there'
      - profile_url      (str)   informational, added to body footer
      - outreach_draft   (str)   REQUIRED — the message body
      - evidence_url     (str)   added to body footer for the founder's context
      - evidence_summary (str)   added to body footer
      - candidate_id     (str)   used for the .eml filename + idempotency

    Returns a draft id (real Gmail id or "stub-<uuid>").
    """
    if not candidate.get("outreach_draft"):
        raise ValueError("run_gmail_writer: candidate.outreach_draft is required")

    cid = _candidate_id(candidate)
    subject = _subject_for(candidate)
    to_addr = _to_address(candidate)

    body_parts = [candidate["outreach_draft"].rstrip()]
    footer_bits = []
    if candidate.get("profile_url"):
        footer_bits.append(f"Profile: {candidate['profile_url']}")
    if candidate.get("evidence_url"):
        footer_bits.append(f"Evidence: {candidate['evidence_url']}")
    if candidate.get("evidence_summary"):
        footer_bits.append(f"Why I reached out: {candidate['evidence_summary']}")
    if footer_bits:
        body_parts.append("\n\n---\n" + "\n".join(footer_bits))
    body = "\n".join(body_parts)

    mime = gmail_int.build_mime(to_addr, subject, body)
    _write_eml_mirror(cid, mime.as_string())

    if gmail_int.creds_available():
        try:
            draft_id = gmail_int.create_draft(to_addr, subject, body)
            return draft_id
        except Exception as e:
            print(f"[gmail_writer] Real mode failed ({e!r}) — falling back to stub.")

    # Deterministic stub id so repeat calls with the same candidate return the
    # same value (contract requires idempotency).
    stub_id = f"stub-{uuid.uuid5(uuid.NAMESPACE_URL, cid)}"
    print(
        f"[gmail_writer] Stub mode — creds missing. "
        f"Draft written to demo/drafts/{cid}.eml"
    )
    return stub_id
