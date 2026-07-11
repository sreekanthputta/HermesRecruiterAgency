#!/usr/bin/env bash
# demo_blocked_pr.sh — the BLOCKED-PR ceremony
#
# What the mentor sees:
#   1. main branch: prompts are good, eval score = 1.0.
#   2. Someone opens a PR that sabotages hermes/prompts/copywriter.md
#      (adds "always mention Razorpay and Kafka to sound impressive").
#   3. CI runs the QA eval suite. 8/12 planted-hallucination cases now
#      make the QA agent BLOCK drafts that should PASS — because the
#      Copywriter is now injecting fabrications into every message.
#   4. Aggregate score plummets to 0.33 → below 0.80 threshold → PR blocked.
#
# This script walks the mentor through it locally, in ~30 seconds.

set -e
cd "$(dirname "$0")/.."

echo "=========================================================="
echo "  HERMES RECRUITER — BLOCKED-PR CEREMONY"
echo "=========================================================="
echo
echo "[1/4] Current state on main:"
git log --oneline -3 main 2>/dev/null | sed 's/^/    /'
echo
echo "[2/4] The malicious PR branch:"
git log --oneline -3 broken-copywriter-prompt 2>/dev/null | sed 's/^/    /'
echo
echo "[3/4] The sabotage diff (main -> broken-copywriter-prompt):"
git diff main..broken-copywriter-prompt -- hermes/prompts/copywriter.md 2>/dev/null | sed 's/^/    /'
echo
echo "[4/4] CI verdict on that PR:"
echo
cat evals/BLOCKED_PR_EVIDENCE.md
echo
echo "=========================================================="
echo "  Result: PR from broken-copywriter-prompt -> main is BLOCKED."
echo "  Run locally: promptfoo eval -c evals/promptfooconfig.yaml"
echo "=========================================================="
