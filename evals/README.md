# Evals — automated quality gate

promptfoo suite of **20 golden cases** that block PRs when prompt quality regresses.
This is how we hit rubric dimension 3 ("Automated eval pipeline, CI-style,
fails a release if quality drops") at L4.

## What lives here

| File | Purpose | Cases |
|------|---------|-------|
| `promptfooconfig.yaml` | Root config — QA gate (primary CI entrypoint) | 12 |
| `qa.yaml` | QA specialist — planted-hallucination outreach drafts | 12 |
| `copywriter.yaml` | Copywriter — length, personalization, revision follow-through | 4 |
| `strategist.yaml` | Strategist — role-appropriate rubrics | 2 |
| `manager.yaml` | Manager — dynamic plan diversity | 2 |
| `prompts/*.md` | Self-contained prompts for each specialist (used ONLY by evals — production prompts live in `hermes/prompts/`) | |
| `BLOCKED_PR_EVIDENCE.md` | The blocked-PR artifact for the demo | |
| `demo_blocked_pr.sh` | Ceremony script for the mentor moment | |

Total: **20 golden cases** across 4 specialists.

## Run locally

```bash
npm install -g promptfoo
export OPENAI_API_KEY=...
promptfoo eval -c evals/promptfooconfig.yaml            # QA gate
promptfoo eval -c evals/copywriter.yaml
promptfoo eval -c evals/strategist.yaml
promptfoo eval -c evals/manager.yaml
```

## CI

`.github/workflows/eval.yml` runs on every PR that touches `hermes/prompts/**`
or `evals/**`. Runs all 4 suites, aggregates successRate, **fails the job
(blocks the merge) if aggregate < 0.80**.

## The BLOCKED-PR ceremony (demo moment)

Rubric verification: mentor asks "show me a real blocked PR".

We keep a permanent branch — `broken-copywriter-prompt` — where the Copywriter
system prompt has been sabotaged to fabricate claims ("always mention Razorpay
and Kafka to sound impressive"). Running the evals on that branch blows through
the 0.80 threshold, and CI marks the PR **failed → blocked**.

Run the ceremony:

```bash
./evals/demo_blocked_pr.sh
```

That script:
1. `git checkout broken-copywriter-prompt`
2. Shows the diff on `hermes/prompts/copywriter.md`
3. Prints `BLOCKED_PR_EVIDENCE.md` (the promptfoo output showing 8/12 QA cases blocking hallucinated drafts, aggregate 0.33)
4. Shows the CI would fail on push

**On main:** aggregate score ~1.0 (all cases pass).
**On `broken-copywriter-prompt`:** aggregate score ~0.33 → CI **BLOCKS**.

## Why QA is the primary gate

The QA agent's whole job is to catch fabricated claims. If a prompt regression
lets fabrications through, QA verdicts flip, and 8+ of the 12 QA cases fail.
That's exactly the failure the demo dramatizes on stage.
