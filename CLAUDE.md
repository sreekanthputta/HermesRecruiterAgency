# Hermes Recruiter Agency — Hackathon Build

## What this is

A submission for **GrowthX's World's Largest Hermes Buildathon** in the **AI as Agency** track. An AI recruiting agency that runs the first round of hiring for a solo founder end-to-end: rewrites the JD, sources 30 real public profiles with evidence, drafts personal outreach, and QAs every message before the founder sends. Human approves every step.

Not resume-keyword-bingo. The wedge is **the JD rewrite becomes a scoring rubric**, and every candidate ships with an evidence link. QA blocks any outreach that misstates a candidate's work.

## The user, one sentence

A founder in Hyderabad hiring their first backend engineer, drowning in 400 junk applies from job portals, who wants to send 10 real personal outreach messages tonight.

## Rubric being targeted (all four dimensions)

| Dimension | How we hit it |
|-----------|---------------|
| Real output on real surfaces, human approves every step, 70–85% success | Real Gmail drafts, real Convex board, real Telegram gateway, QA gate before anything moves, human clicks send |
| Dynamic manager plans + delegates + reviews + bounces back | Manager reads the specific request, generates a plan, delegates to specialists via MCP tools, reviews outputs, bounces work back with revision notes when quality drops |
| Trace tree with tokens + cost, filterable by agent/task | Every MCP tool call writes a trace row to Convex. Run board renders it as a tree, filterable |
| Automated eval pipeline in CI, blocks releases | GitHub Actions + promptfoo. 20 golden test cases. Branch protection blocks merge on eval failure. Show one real blocked PR |

## Architecture (Option C: Hermes as manager + MCP tool specialists)

```
[Founder on Telegram]  ←→  [Hermes agent (manager)]
                                    ↓ MCP tool calls
                    ┌───────────────┼───────────────┬──────────────┐
                    ↓               ↓               ↓              ↓
              Strategist        Sourcer         Copywriter        QA
              (MCP tool)   (MCP + Linkup)      (MCP tool)     (MCP tool)
                    ↓               ↓               ↓              ↓
                     ─── writes traces + candidate rows ───
                                    ↓
                                [Convex]
                                    ↓
              [Cloudflare Pages run board] + [Founder's Gmail drafts]
```

Hermes is the single agent (its natural mode). The 5 specialists are **MCP tools** it calls. This gives us:
- One Hermes to deploy (already running with Telegram + ElevenLabs)
- Clean trace tree (each MCP call = one node)
- Dynamic routing (manager picks which tools to call, in what order, based on the request)
- Real crew feel (specialists are separately prompted, separately traced, separately eval'd)

## The crew

**Manager** — runs inside Hermes's system prompt / top-level skill. Not a separate agent, but the orchestrator.

| # | Specialist | Job | Tools it uses |
|---|-----------|-----|---------------|
| 1 | Role Strategist | Rewrites JD + builds weighted scoring rubric (must-haves, nice-to-haves, ignore-list) | LLM only |
| 2 | Sourcer | Finds 30 real public profiles. Each row: name, URL, evidence link, why-match, rubric score | Linkup + GitHub public API + browser |
| 3 | Outreach Copywriter | Drafts one personal message per candidate | LLM + candidate row from Convex |
| 4 | QA Agent | Reads every outreach draft; blocks any message that claims something not verifiable from evidence | LLM + candidate evidence |
| 5 | Gmail Draft Writer | Saves approved outreach into founder's Gmail Drafts folder. Never sends. | Gmail API `users.drafts.create` |

Optional pre-defined specialists (called only when relevant to the specific role): Portfolio Reviewer (design roles), Reference Checker (senior roles).

## Dynamic manager behavior (rubric dimension 2)

The manager is NOT a static pipeline. Per request:

1. **Read request** — "hire a backend engineer in Hyderabad" vs "hire a marketing designer" produce different plans.
2. **Generate plan** — engineer plan: Strategist → Sourcer (GitHub-heavy) → Copywriter → QA. Designer plan: Strategist → Sourcer (portfolio-heavy) → Portfolio Reviewer → Copywriter → QA.
3. **Delegate** — call each specialist via its MCP tool with a structured task brief.
4. **Review** — read each specialist's output. If quality drops (generic outreach, weak evidence, hallucinated claim), **bounce back with concrete revision notes**.
5. **Accept only when good** — then proceed to next step or loop back.

**Mentor verification test we must pass:** two structurally different requests → traces show different plans + at least one output was rejected and revised.

## Non-negotiables

- **Real public profiles only.** No synthetic candidates. Judges will click evidence links.
- **Outreach lands as Gmail Drafts in the founder's own account.** No SendGrid, no burner. Founder hits Send manually.
- **QA blocks on false claims.** If Copywriter praises "your Kafka work at Razorpay" but profile shows neither, QA rejects it. Rehearse this as the on-stage moment.
- **Evidence link per candidate.** GitHub repo, blog post, LinkedIn line — something concrete.
- **Trace tree over reports.** Every decision visible as a node with tokens + cost. Filterable by agent or task.
- **Manager must bounce work back at least once per run.** Bake this into the eval suite so we can prove it on stage.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Agent framework | **Hermes Agent** (already set up with Telegram + ElevenLabs) | Free gateway + voice + memory + tool loop |
| Model | Claude Sonnet 4.6 (specialists) + Opus 4.7 (manager + QA) via OpenRouter | Provider-agnostic, quality where it matters |
| Specialist runtime | **MCP tool servers** | Clean trace nodes, dynamic routing feel |
| Data + traces + run board state | **Convex** | Real-time UI, easy schema, +25 power-up |
| Live web research | **Linkup** | Evidence-linked citations, +25 power-up |
| Waitlist + run board UI | **Cloudflare Pages** (React + Convex client) | Fast deploy, power-up |
| Real outreach surface | **Founder's Gmail (Drafts folder)** via Gmail API | Human clicks send, never automated |
| CI evals | **GitHub Actions + promptfoo** | Blocks merge on quality drop |
| Voice narration | **ElevenLabs** (already wired via Hermes) | Manager narrates the run over Telegram voice |
| User channel | **Telegram** (already wired via Hermes) | Founder DMs the manager, gets voice + text back |

## Partner power-ups being claimed

- Linkup (+25) — evidence-linked sourcing
- Convex (+25) — candidate board, rubric scores, trace tree, run logs
- Cloudflare — Pages for waitlist + workspace UI
- ElevenLabs — voice narration on Telegram (already integrated)

## Memory / self-learning (the L4 vs L5 story)

- **L5 baseline:** wipe memory and it's a generic sourcing script with no taste.
- **L4 target:** across batches, founder's advance/reject clicks retrain rubric weights and copywriter tone automatically. Demo by running batch 1 (~5/10 founder agreement) vs batch 3 (~9/10).
- Memory holds: hiring bar, rejected-profile patterns, founder's outreach tone, past verdicts.
- Uses Hermes's built-in memory system (persistent across sessions).

## Build order (~8 hours)

1. **0:00–0:30** — Waitlist page live on Cloudflare Pages. Post announcement on Twitter/LinkedIn.
2. **0:30–1:30** — Convex schema (runs, candidates, traces). Real-time subscriptions.
3. **1:30–3:30** — 5 MCP tool servers with stub outputs. Wired to Hermes. All 5 trace nodes appear in Convex.
4. **3:30–5:00** — Real Linkup + GitHub in Sourcer. Real profiles start flowing. QA blocking logic proven on a planted overstatement.
5. **5:00–6:00** — Manager persona + dynamic plan prompt. Test with 2 different role types — must produce different plans.
6. **6:00–7:00** — Run board UI on Cloudflare Pages. Trace tree renders live from Convex.
7. **7:00–7:30** — Gmail draft creation. Memory hookup.
8. **7:30–8:00** — CI eval pipeline. Get one real blocked PR into git history for the demo.
9. **Then** — End-to-end dry run with real founder friend, real open role. Record demo footage.

## Demo moment (rehearse this)

1. Founder DMs Hermes on Telegram: "hiring a backend engineer in Hyderabad, here's the JD" (voice or text).
2. Hermes narrates the plan over ElevenLabs voice.
3. Run board fills row by row on projector — Strategist → Sourcer → Copywriter → QA.
4. Trace tree grows live with tokens + cost per node.
5. QA blocks one draft on stage. Show the evidence side-by-side.
6. Manager bounces the blocked draft back to Copywriter with revision notes. Second draft passes.
7. Founder opens their Gmail on phone. Two real drafts are there. Hits Send on both. On camera.
8. Cut to: (a) batch 1 vs batch 3 comparison showing learning, (b) the blocked GitHub PR from CI evals.

## What NOT to build

- No fake candidates in the demo. Judges click links.
- No autopilot send. Every outbound message is a human click.
- No burner email account. Founder's real Gmail.
- No LinkedIn scraper. Use Linkup.
- No fancy candidate scoring math. Simple rubric weights.
- No mobile app, no extension, no Slack bot.
- No CRM. Gmail + Convex is enough.

## Open questions to resolve on day 1

- Which real founder is the design partner for the live demo?
- Which real open role? (Backend engineer in Hyderabad is the strawman.)
- Do we self-host Hermes on Hostinger VPS or run local for the hackathon? (Already up — check current setup.)
- OpenRouter vs direct Anthropic for the models?

## Reference links

- Hermes Agent docs: https://hermes-agent.nousresearch.com/docs
- Hermes Agent GitHub: https://github.com/nousresearch/hermes-agent
- Buildathon (Bangalore): https://growthx.club/events/world-s-largest-hermes-buildathon-bangalore-17e278
- Convex docs: https://docs.convex.dev
- MCP docs: https://modelcontextprotocol.io
- Linkup: https://linkup.so
- Cloudflare Pages: https://pages.cloudflare.com
- promptfoo: https://www.promptfoo.dev
