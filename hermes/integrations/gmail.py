"""
Gmail integration — saves outreach messages as DRAFTS in the founder's own Gmail.

NEVER SENDS. The founder is the human-in-the-loop: they open Drafts, update the
To: field with the candidate's real email (or send to themselves for review),
and click Send manually.

Scope: gmail.compose only (cannot read inbox, cannot send — safest scope for
this workflow).

============================================================
HOW TO ENABLE REAL GMAIL DRAFTS (3 steps)
============================================================

  1. Create OAuth credentials
     - Go to https://console.cloud.google.com/apis/credentials
     - Enable Gmail API for a project
     - Create OAuth client ID -> type "Desktop app"
     - Download the JSON, save it to repo root as `credentials.json`
       (path is configurable via GMAIL_CREDENTIALS_PATH in .env)

  2. Run the one-time OAuth helper
       python setup_gmail.py
     A browser window opens, you sign in and grant the gmail.compose scope.
     A `token.json` is written to repo root.

  3. Set GMAIL_TARGET_ACCOUNT in .env to your Gmail address
     (drafts land in this account's Drafts folder).
     Then any call to run_gmail_writer(candidate) will create a real draft
     instead of a stub .eml file.

============================================================
"""

from __future__ import annotations

import base64
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional


GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def creds_available() -> bool:
    """True if both credentials.json and token.json exist on disk."""
    cred_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")
    tok_path = os.getenv("GMAIL_TOKEN_PATH", "./token.json")
    return Path(cred_path).exists() and Path(tok_path).exists()


def _load_service():
    """Build and return a Gmail API service client. Requires creds present."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    tok_path = os.getenv("GMAIL_TOKEN_PATH", "./token.json")
    cred_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")

    creds = Credentials.from_authorized_user_file(tok_path, GMAIL_SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(tok_path).write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def build_mime(to_addr: str, subject: str, body: str, from_addr: Optional[str] = None) -> MIMEText:
    """Compose a plain-text MIME email."""
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to_addr
    msg["Subject"] = subject
    if from_addr:
        msg["From"] = from_addr
    return msg


def mime_to_raw(msg: MIMEText) -> str:
    """base64url encoded string, as required by Gmail API drafts.create."""
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")


def find_existing_draft(service, subject: str) -> Optional[str]:
    """Return the draft id whose subject matches, or None. Idempotency check."""
    try:
        resp = service.users().drafts().list(userId="me", maxResults=100).execute()
        for d in resp.get("drafts", []):
            full = service.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()
            headers = full.get("message", {}).get("payload", {}).get("headers", [])
            for h in headers:
                if h.get("name", "").lower() == "subject" and h.get("value") == subject:
                    return d["id"]
    except Exception:
        return None
    return None


def create_draft(to_addr: str, subject: str, body: str, from_addr: Optional[str] = None) -> str:
    """
    Create a real Gmail draft (or return existing id if a matching-subject draft
    already exists — makes calls idempotent). Returns the draft id.
    """
    service = _load_service()

    existing = find_existing_draft(service, subject)
    if existing:
        return existing

    msg = build_mime(to_addr, subject, body, from_addr=from_addr)
    payload = {"message": {"raw": mime_to_raw(msg)}}
    draft = service.users().drafts().create(userId="me", body=payload).execute()
    return draft["id"]
