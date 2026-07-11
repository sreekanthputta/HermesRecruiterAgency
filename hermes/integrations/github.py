"""GitHub public API client — profile enrichment."""
from __future__ import annotations

import os
import urllib.request
import urllib.error
import json
import re
from typing import Any

GITHUB_API = "https://api.github.com"

_USER_URL_RE = re.compile(r"^https?://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/?$")
_REPO_URL_RE = re.compile(r"^https?://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([^/#?\s]+)/?$")


def parse_github_username(url: str) -> str | None:
    m = _USER_URL_RE.match(url.strip())
    return m.group(1) if m else None


def parse_github_repo(url: str) -> tuple[str, str] | None:
    m = _REPO_URL_RE.match(url.strip())
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    # Filter out reserved paths that aren't repos
    if owner.lower() in {"orgs", "topics", "search", "explore", "collections", "features", "settings", "notifications"}:
        return None
    return owner, repo


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: int = 15):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.timeout = timeout

    def _get(self, path: str) -> Any:
        url = f"{GITHUB_API}{path}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "hermes-recruiter",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise RuntimeError(f"GitHub HTTP {e.code} on {path}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"GitHub network error: {e}") from e

    def user(self, username: str) -> dict[str, Any] | None:
        return self._get(f"/users/{username}")

    def repos(self, username: str, sort: str = "stars", per_page: int = 10) -> list[dict[str, Any]]:
        data = self._get(f"/users/{username}/repos?sort={sort}&per_page={per_page}&type=owner")
        return data if isinstance(data, list) else []

    def languages(self, owner: str, repo: str) -> dict[str, int]:
        data = self._get(f"/repos/{owner}/{repo}/languages")
        return data if isinstance(data, dict) else {}


def enrich_github_profile(url: str, client: GitHubClient | None = None) -> dict[str, Any] | None:
    """Given a github.com/<user> URL, return profile + top repo + languages.

    Returns None if not a user URL or user not found.
    """
    username = parse_github_username(url)
    if not username:
        return None
    gh = client or GitHubClient()
    user = gh.user(username)
    if not user or user.get("type") != "User":
        return None
    repos = gh.repos(username, per_page=15)
    # Exclude forks; sort by stars desc
    own = [r for r in repos if not r.get("fork")]
    own.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
    top = own[0] if own else None
    languages: dict[str, int] = {}
    if top:
        languages = gh.languages(username, top["name"])
    return {
        "username": username,
        "name": user.get("name") or username,
        "bio": user.get("bio") or "",
        "location": user.get("location") or "",
        "company": user.get("company") or "",
        "blog": user.get("blog") or "",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "profile_url": user.get("html_url") or f"https://github.com/{username}",
        "top_repo": top,
        "top_repo_languages": languages,
    }
