# Hermes Recruiter Agency

Hackathon submission — **GrowthX World's Largest Hermes Buildathon**, **AI as Agency** track.

**Live run board:** https://hermes-recruiter.pages.dev/

An AI recruiting agency that runs first-round hiring for a solo founder: rewrites the JD into a scoring rubric, sources 30 real public profiles with evidence, drafts personal outreach per candidate, QAs every message before it moves, and saves approved drafts to the founder's real Gmail. Human clicks Send.

## Architecture

```
[Founder]  →  [Manager]  →  Role Strategist  →  Sourcer (Linkup + GitHub)
                                                       ↓
                                                 Copywriter
                                                       ↓
                                                     QA  (bounces bad drafts back to Copywriter)
                                                       ↓
                                                 Gmail Draft Writer
```

- **Manager** is dynamic — reads the specific JD and generates a plan. Different role types → different plans.
- **QA blocks lies** — any outreach claim not backed by evidence gets rejected. Manager bounces back with revision notes.
- **Real surfaces** — profiles are real (evidence links click through), drafts land in a real Gmail inbox, run board deploys to Cloudflare Pages, state persists in Convex.

## Power-ups claimed

- **Wispr Flow** — build narration + Slack updates dictated with Wispr
- **Linkup** — live sourcing with evidence citations
- **Convex** — main backend (runs, candidates, traces)
- **Cloudflare** — Pages hosts the live run board
- (Optional) ElevenLabs, Dodo — not in this cut

## Quickstart

```bash
# 1. Install deps
pip install -r requirements.txt
cd web && npm install && cd ..

# 2. Fill .env — copy .env.example, paste keys
cp .env.example .env
# edit .env

# 3. Bring Convex live (interactive, one-time)
cd convex && npx convex dev
# copy the URL and deploy key it prints → paste into ../.env
cd ..

# 4. (Optional) Enable real Gmail Drafts
python setup_gmail.py

# 5. Deploy web UI to Cloudflare Pages
cd web && ./deploy.sh
# copy the URL it prints for the demo

# 6. Run the demo
bash demo/run.sh
```

## Repo layout

| Path | Owner |
|---|---|
| `hermes/manager.py` | Manager loop |
| `hermes/specialists/*.py` | 5 specialists |
| `hermes/prompts/*.md` | Editable prompts (version-controlled, evals gate PRs to these) |
| `hermes/integrations/*.py` | Linkup, GitHub, Gmail, Convex, ElevenLabs clients |
| `convex/*.ts` | Convex schema + functions |
| `web/` | React run board, deploys to Cloudflare Pages |
| `evals/` | promptfoo test suite |
| `.github/workflows/eval.yml` | CI — blocks merge on eval failure |
| `schemas/contracts.md` | Locked JSON contracts between all components |
| `demo/` | Strawman JD, run scripts, sample drafts |

## Rubric coverage (self-assessment)

| Dimension | Level | Weight | Points |
|---|---|---|---|
| Working product (Gmail drafts, real profiles, human approves) | L4 | 20x | 80 |
| Agent org (dynamic manager, bounces work back) | L4 | 5x | 20 |
| Observability (trace tree, tokens+cost, filter by agent) | L4 | 7x | 28 |
| Evals (promptfoo + CI blocks a real bad PR) | L4 | 5x | 20 |
| Memory / handoffs | L3 | 2x | 6 |
| Cost / latency | L3 | 1x | 3 |
| Management UI | L2-L3 | 1x | 2-3 |
| **Subtotal** | | | **~159** |
| Wispr (dictate 500+ words during event) | +25 | | 25 |
| Linkup (live search doing real work) | +25 | | 25 |
| Convex (main backend) | +25 | | 25 |
| Cloudflare (Pages hosts run board) | +25 | | 25 |
| **Total** | | | **~259** |

## What's intentionally NOT built (and why)

- **Dodo Payments** — a solo founder using AI to hire doesn't hit a paywall mid-demo. Story cost > 25 pts.
- **ElevenLabs voice narration** — not on the primary scoring path. Skipped for time; can be added if Hermes existing integration is available.
- **Telegram** — demo runs from CLI + browser. Telegram adds integration surface without adding rubric points.
- **Memory across batches (L4 self-learning)** — would need multiple real runs over time to demo. Kept at L3 (context within task + handoffs).
- **L5 Emergent org** — manager doesn't spawn new specialists at runtime. L4 dynamic delegation is the target.

## Demo script (~90 sec)

1. Open Gmail on phone. Empty Drafts folder. (Show on projector.)
2. `bash demo/run.sh` — feed strawman JD ("backend engineer, Hyderabad, Python + Postgres, 3-6 yrs").
3. Cloudflare Pages board on projector — trace tree fills row by row. Tokens + cost tick up.
4. Point to one bounced-back trace: click into it. Read: "QA blocked — draft claimed 'your Kafka work at Razorpay', evidence shows neither. Revision below."
5. Show the revised trace next to it. "Same candidate, second draft, verdict pass."
6. Refresh Gmail. Two real drafts in Drafts folder. Open one, hit Send on camera.
7. Switch to git log: show the branch `broken-copywriter-prompt` and its failing eval output. "This PR is blocked. Cannot merge."

## Rotate these keys after the demo

- OpenAI (in .env)
- GitHub PAT (in .env)
- Cloudflare API token (in .env)
- Linkup key (in .env)
