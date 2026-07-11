"""Linkup API client — evidence-linked web search.

Docs: https://docs.linkup.so
Endpoint: POST https://api.linkup.so/v1/search
"""
from __future__ import annotations

import os
import urllib.request
import urllib.error
import json
from typing import Any

LINKUP_URL = "https://api.linkup.so/v1/search"


class LinkupClient:
    def __init__(self, api_key: str | None = None, timeout: int = 30):
        self.api_key = api_key or os.getenv("LINKUP_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("LINKUP_API_KEY not set")
        self.timeout = timeout

    def search(self, q: str, depth: str = "standard", output_type: str = "searchResults") -> dict[str, Any]:
        """Run a Linkup search. depth='deep' is slower but higher quality."""
        payload = json.dumps({"q": q, "depth": depth, "outputType": output_type}).encode("utf-8")
        req = urllib.request.Request(
            LINKUP_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Linkup HTTP {e.code}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Linkup network error: {e}") from e


def linkup_search(q: str, depth: str = "standard") -> list[dict[str, Any]]:
    """Convenience wrapper — returns just the results array."""
    client = LinkupClient()
    resp = client.search(q, depth=depth)
    return resp.get("results", []) or []
