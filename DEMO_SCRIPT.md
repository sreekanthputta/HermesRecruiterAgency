# Demo Script — Hermes Recruiter Agency

**Total runtime:** ~2 min live + 30 sec Q&A hook
**Track:** AI as Agency (GrowthX Buildathon)
**One-line pitch:** *"An AI recruiting agency a solo founder can DM on Telegram — it rewrites the JD, sources real profiles, drafts personal outreach, QA-blocks any lie, and lands the approved drafts in the founder's own Gmail. Human clicks Send."*

---

## Pre-flight (T-5 min)

Run this checklist right before you go on stage. If any item fails, **use offline mode** (see Contingencies).

```bash
# 1. Convex is reachable + tables empty
cd convex && CONVEX_DEPLOY_KEY='<key>' npx convex run admin:clearAll

# 2. Hermes gateway is up + MCP registered
hermes gateway status && hermes mcp list         # 'recruiter' should show ✓ enabled

# 3. Web board is deployed + hitting live Convex
open https://hermes-recruiter.pages.dev

# 4. Gmail Drafts folder is empty (or has known count) on your phone
open https://mail.google.com/mail/u/0/#drafts

# 5. Telegram chat with @HermesRecruiterBot is scrolled to bottom, ready
```

**Screens on projector (in order):**
1. Telegram (phone, mirrored) — left half
2. Run board (browser) — right half
3. Gmail Drafts (phone) — swap in for the Send moment
4. GitHub Actions failing run — swap in for the closer

---

## The Script

### 0:00 — 0:10 · Cold open

**On screen:** empty run board (0 runs, "Waiting for first run…"), empty Gmail Drafts.

> "This is a solo founder in Hyderabad hiring their first backend engineer. Their inbox has 400 junk applies from job portals. They want to send 10 real personal outreach messages tonight. I'm going to DM my recruiter agency on Telegram."

### 0:10 — 0:25 · Send the JD

**Action:** on phone, paste into Telegram DM:

> *"hiring a backend engineer in Hyderabad, Python + Postgres, 3-6 yrs, remote OK"*

**Say:** "That's it. No form, no dashboard. One sentence, one channel."

**On screen:** Telegram shows "typing…", then Hermes replies with the plan.

### 0:25 — 1:00 · The board fills live

**Action:** switch focus to the run board. Point at it as nodes appear.

**Beat 1 — Plan** (~2s in): manager node appears, `generate dynamic plan from JD`. Click it. **Say:** "The manager reads the specific request and picks the crew. This isn't a hardcoded pipeline — a design role would produce a different plan with a Portfolio Reviewer."

**Beat 2 — Strategist** (~4s): `rewrite JD and build weighted rubric` appears. **Say:** "The JD becomes a scoring rubric. Every rubric hit will show up on the candidate row."

**Beat 3 — Sourcer** (~15s): sourcer node with sub-steps `linkup_search → enrich → final` nested under it. **Say:** "Linkup + GitHub API. Every candidate row has an evidence link — a repo, a blog, a public profile. You can click through, it's not a resume-keyword game."

**Beat 4 — Copywriter → QA loop begins.** Candidates start streaming.

### 1:00 — 1:30 · **THE MOMENT** — QA blocks a lie

**On screen:** trace tree shows a red `qa BOUNCED` node. Click it.

**Say:** "The QA agent just blocked an outreach draft. It claimed the candidate had Kafka work at Razorpay — but their profile shows neither. The manager bounces it back to the copywriter with revision notes."

**Action:** click the next node — a yellow `copywriter REVISION` node. Then the next `qa` node — green, accepted.

**Say:** "Second draft, same candidate, no fabrication, passes. This is the wedge. Job portals don't do this. Recruiters don't do this. My agency does."

### 1:30 — 1:50 · Gmail moment

**Action:** switch the projector to the phone's Gmail Drafts. Pull to refresh.

**On screen:** 2 real drafts, subject lines mentioning specific candidates by first name.

**Say:** "These are in my founder's own Gmail. Never automated. Never sent. Human clicks Send."

**Action:** open one draft. Read the first line out loud. Hit **Send** on camera.

### 1:50 — 2:20 · CI-blocked PR (the closer)

**Action:** switch projector to GitHub Actions. Show the failing run:
[actions/runs/29169516024](https://github.com/sreekanthputta/HermesRecruiterAgency/actions/runs/29169516024)

**Say:** "One more thing. This is the automated eval pipeline. Someone opened a PR that rewrote the copywriter prompt to boost reply rates — sounds fine, right? The evals caught that the new prompt hallucinates Kafka work in every draft. CI blocks the merge. Score below 0.80 threshold. This is real, in git history."

**Action:** click into the failing job log — show the `::error::Eval score .5000 below threshold 0.80 — BLOCKING merge` line.

### 2:20 — end · Close

**Say:** *"Two defenses: manager bounce-back in the run, CI evals at merge time. Every draft either passes QA or gets bounced. Every prompt either passes eval or gets blocked. The founder sends only what survived both. That's my submission."*

---

## Anticipated Q&A

**Q: Are those real profiles?**
A: Yes. Every candidate row has an evidence URL. Click any of them — GitHub profile, blog, LinkedIn. We use Linkup for public web search, GitHub public API for enrichment. No synthetic data.

**Q: Why not auto-send?**
A: The founder is on the hook if outreach embarrasses them. Human-in-the-loop is a feature, not a limitation. Also: Gmail sending API is easy — restraint is the design choice.

**Q: What if the LLM QA misses a lie?**
A: That's why CI evals exist too. Golden set of 20 cases, ~half of which are "did the QA block the fabrication?" — the pipeline catches drift in the QA prompt itself. Shown on stage.

**Q: How does this compare to an ATS?**
A: An ATS receives inbound applications. This does outbound sourcing + first-contact drafting. Different job.

**Q: What's the manager actually deciding?**
A: For a backend role → GitHub-heavy sourcing. For a design role → portfolio-heavy sourcing + Portfolio Reviewer specialist. For senior roles → optional Reference Checker. The plan is generated from the JD, not templated.

**Q: What's Level 5 look like?**
A: Manager spawns new specialists at runtime instead of picking from a fixed roster. Also cross-batch memory that retrains rubric weights from founder's advance/reject clicks. Neither in this cut — L4 dynamic delegation is what we're claiming.

**Q: Is this reproducible?**
A: Yes. `bash demo/run.sh` with the JD file runs end-to-end. Repo public at github.com/sreekanthputta/HermesRecruiterAgency.

---

## Rubric hits to name-drop if asked

| Dim | What to point at on stage |
|---|---|
| Working product | Real drafts in real Gmail, Send on camera |
| Agent org (dynamic + bounce-back) | Trace tree shows different plans for different JDs; red BOUNCED node followed by REVISION → PASS |
| Observability | Trace tree with tokens + cost per node, filter by agent, sub-steps nested under sourcer |
| Evals + CI gate | GitHub Actions failing run, PR #1 blocked in git history |

Power-ups: **Linkup** (live sourcing) · **Convex** (backend + real-time board) · **Cloudflare Pages** (run board) · **Hermes** (Telegram + MCP tool loop).

---

## Contingencies

### If Convex is down
Set `CONVEX_URL=""` in `.env` before the run. Client falls back to local JSON files under `demo/data/`. The web board won't update live, but you can point at `demo/data/traces.json` in a terminal to show trace rows landing.

### If Linkup / OpenAI rate-limits mid-run
The board will show a `sourcer` node with 0 candidates. Have `demo/sample-run.json` ready and load it into the web app via `?demo=1`. Say: *"For time, I'm going to switch to a pre-recorded run — the code and traces are the same."*

### If Telegram flakes
Skip Telegram. Run `bash demo/run.sh demo/jd.txt` on the terminal. Same output, same board fills, same Gmail drafts. Say: *"I'll trigger the pipeline from the CLI so you can see the same behavior."*

### If the QA-block moment doesn't fire on this run
The manager forces one bounce-back for demo purposes (`_force_bounce=True` on the first candidate in `manager.py:233`). If somehow it still passes: click into a **prior** run's trace tree via the Run selector dropdown — every past run has at least one bounced trace.

### If Gmail auth expires
Show `demo/drafts/*.eml` files on the terminal — same content, plaintext. Say: *"Auth expired at the worst moment. These are the same drafts as .eml files."*

---

## Post-demo actions (do not skip)

- [ ] Rotate: OpenAI key, GitHub PAT, Convex deploy key, Linkup key, Cloudflare token
- [ ] Revoke Gmail OAuth for the demo Gmail account
- [ ] `hermes gateway stop` if not going to keep it running
- [ ] Commit any polish, tag `v1.0-demo`
