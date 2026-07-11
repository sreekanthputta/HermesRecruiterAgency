# Things only you can do (Sreekanth)

The 6 parallel builders can't do these because they need interactive login or your personal creds.

## 1. Convex live setup (2 min — interactive OAuth)

```bash
cd convex
npx convex dev
# Opens browser. Sign in with GitHub or Google.
# It prints CONVEX_URL and CONVEX_DEPLOY_KEY.
# Copy both, paste into ../.env at lines CONVEX_URL= and CONVEX_DEPLOY_KEY=
cd ..
```

Until this is done, the code writes to local JSON files (works, but web board won't be live-updating).

## 2. Gmail credentials (5 min if you don't already have a Google Cloud project)

Fastest path:
1. Go to https://console.cloud.google.com
2. Create new project (or use existing)
3. APIs & Services → Library → search "Gmail API" → Enable
4. APIs & Services → Credentials → Create Credentials → OAuth Client ID
   - Application type: Desktop app
   - Download the JSON — save as `credentials.json` at repo root
5. Run: `python setup_gmail.py`
   - Opens browser to authorize the compose scope
   - Saves `token.json` at repo root
6. Also paste your email into `.env` at `GMAIL_TARGET_ACCOUNT=`

Alternative for speed: skip Gmail entirely. The stub mode writes drafts to `demo/drafts/*.eml` — mentors can inspect the files instead. Loses some rubric points on "real surface" but saves 5 min.

## 3. Wispr Flow — +25 free points

Just use Wispr to dictate 500+ words during the event. Slack messages, chat prompts, notes — anything counts. Take the screenshot at the end.

Do this now: dictate your next 3-4 messages to me instead of typing.

## 4. Optional: push to GitHub for real CI blocked-PR

```bash
gh repo create hermes-recruiter-agency --public --source=. --push
gh secret set OPENAI_API_KEY --body "$(grep OPENAI_API_KEY .env | cut -d= -f2)"
git push origin broken-copywriter-prompt
gh pr create --base main --head broken-copywriter-prompt --title "Prompt tweak: more assertive" --body "See changes"
# Watch Actions tab fail. Screenshot the blocked check.
```

This upgrades the blocked-PR moment from "local git log" to "real GitHub PR that anyone can click". Worth 3-5 min if time allows.

## Timing recommendation

- **Right now:** Kick off #1 (Convex). It takes 2 min interactive.
- **After Convex:** Do #2 (Gmail) if you want the strongest demo.
- **Any time:** #3 (Wispr) — just keep dictating.
- **Last 5 min:** #4 (GitHub push) if things are going smoothly.
