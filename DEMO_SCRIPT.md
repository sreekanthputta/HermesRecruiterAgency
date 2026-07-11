# Demo Script — Hermes Recruiter Agency

**Runtime:** ~2 min. **Pitch:** *An AI recruiter you DM on Telegram. Sources real profiles, drafts outreach, QA blocks lies, drops approved into your Gmail. You click Send.*

---

## Pre-flight (T-5 min)

```bash
cd convex && CONVEX_DEPLOY_KEY='<key>' npx convex run admin:clearAll   # wipe demo state
hermes gateway status && hermes mcp list                                # 'recruiter' ✓ enabled
open https://hermes-recruiter.pages.dev                                 # board loads, empty
```
Phone: Gmail Drafts empty, Telegram chat ready.

Projector split: Telegram (left) · run board (right). Swap in Gmail Drafts for the Send moment, GitHub Actions for the closer.

---

## The beats

**0:00 — Cold open.** Board empty, drafts empty. *"Solo founder in Hyderabad hiring their first backend engineer. 400 junk applies in their inbox. Wants 10 real outreach messages tonight. Watch."*

**0:10 — Send the JD.** Paste into Telegram: *"hiring a backend engineer in Hyderabad, Python + Postgres, 3-6 yrs, remote OK"*. *"One sentence, one channel. No form."*

**0:25 — Board fills live.** Point at nodes as they appear:
- `manager` — *"Reads the request, picks the crew. Design role → different plan."*
- `role_strategist` — *"JD becomes a weighted scoring rubric."*
- `sourcer` (with linkup_search / enrich / final nested) — *"Linkup + GitHub. Every row has a clickable evidence link."*

**1:00 — The money moment.** Red `qa BOUNCED` node. Click it. *"QA blocked a draft that claimed Kafka work at Razorpay — profile shows neither. Manager bounces it back."* Next node: yellow `copywriter REVISION`. Then green `qa` accepted. *"Same candidate, second draft, no fabrication. Passes."*

**1:30 — Gmail on camera.** Switch projector to phone's Drafts. Pull to refresh — 2 real drafts. Open one, read first line, hit **Send** live.

**1:50 — CI-blocked PR (closer).** Switch to [actions/runs/29169516024](https://github.com/sreekanthputta/HermesRecruiterAgency/actions/runs/29169516024). *"Automated evals blocked a PR that would've made the copywriter fabricate Kafka in every draft. Score 0.50, threshold 0.80. Real, in git history."*

**2:15 — Close.** *"Two defenses: manager bounces at run time, CI evals block at merge time. Founder only sends what survived both."*

---

## If it breaks live

| Failure | Fallback |
|---|---|
| Telegram flakes | `bash demo/run.sh demo/jd.txt` — same output, same board |
| Convex 522 / down | `CONVEX_URL=""` in .env — client falls back to local JSON; show `demo/data/traces.json` |
| Linkup / OpenAI rate-limit | Switch to prior run in the board's Run selector — every past run has a bounce |
| Gmail auth expired | Show `demo/drafts/*.eml` in a terminal — same content, plaintext |
| QA doesn't fire a block | `manager.py:233` forces one bounce; if still passes, click into a prior run's tree |
