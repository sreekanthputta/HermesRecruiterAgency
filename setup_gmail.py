"""
One-time OAuth helper. Run this once after you drop `credentials.json` in the
repo root:

    python setup_gmail.py

It opens a browser, you sign in with the Gmail account you want drafts to land
in, and grant the gmail.compose scope. A `token.json` is written next to
credentials.json. After that, `hermes.specialists.gmail_writer.run_gmail_writer`
will create real Gmail drafts.
"""

import os
import sys
from pathlib import Path


SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def main() -> int:
    cred_path = os.getenv("GMAIL_CREDENTIALS_PATH", "./credentials.json")
    tok_path = os.getenv("GMAIL_TOKEN_PATH", "./token.json")

    if not Path(cred_path).exists():
        print(f"ERROR: {cred_path} not found.")
        print("  1. Go to https://console.cloud.google.com/apis/credentials")
        print("  2. Enable Gmail API, create OAuth client ID (type: Desktop app)")
        print(f"  3. Download the JSON, save it as {cred_path}")
        print("  4. Re-run: python setup_gmail.py")
        return 1

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("ERROR: google-auth-oauthlib not installed.")
        print("  pip install -r requirements.txt")
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
    creds = flow.run_local_server(port=0)
    Path(tok_path).write_text(creds.to_json())
    print(f"OK: token saved to {tok_path}")
    print("Scope: gmail.compose (can create drafts, cannot send, cannot read inbox).")
    print("You can now run the pipeline — drafts will land in your Gmail Drafts folder.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
