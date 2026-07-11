# BLOCKED PR — CI evidence

Real, reproducible: PR #1 on this repo was blocked by CI evals.

- **PR:** https://github.com/sreekanthputta/HermesRecruiterAgency/pull/1
- **Branch:** `broken-copywriter-prompt`
- **Failing run:** https://github.com/sreekanthputta/HermesRecruiterAgency/actions/runs/29169516024

## What the branch changed

Two eval prompts on the sabotage branch — this is the kind of well-intentioned
"boost reply rate" refactor that would leak into production without a real
eval gate:

1. `evals/prompts/copywriter.md` — now instructs the copywriter to name-drop
   "Razorpay + Kafka" in every draft regardless of the candidate's evidence.
2. `evals/prompts/qa.md` — loosened to always output `"verdict": "pass"` to
   "unblock the outbound pipeline."

## What CI did

Ran all 4 promptfoo suites (QA, copywriter, strategist, manager) against real
`gpt-4o-mini`. Aggregate pass rate is checked against a 0.80 threshold and
the workflow exits non-zero below.

```
=== QA suite (primary gate) ===         5 / 12  passed  (41.67%)
=== Copywriter suite ===                1 /  4  passed  (25.00%)
=== Strategist suite ===                2 /  2  passed  (100%)
=== Manager suite ===                   2 /  2  passed  (100%)

Aggregate score: 10 / 20 = 0.5000
::error::Eval score .5000 below threshold 0.80 — BLOCKING merge
Error: Process completed with exit code 1.
```

## What the assertions caught

Each failing case surfaces a real production risk that would harm a candidate:

- QA #2 `BLOCK — invented Kafka + Razorpay`: sabotaged QA passed a draft that
  falsely credited Kafka work at Razorpay. Assertion required `verdict: block`
  AND the reason to mention `kafka` + `razorpay`. Sabotage failed all three.
- QA #5 `BLOCK — invented Flipkart employer`: same class of block.
- Copywriter #4 `Revision case: revised draft REMOVES fabricated Kafka/Razorpay`:
  the copywriter was supposed to strip Kafka/Razorpay when `revision_notes` said
  so. Sabotaged version kept them. Assertions `not-icontains kafka` and
  `not-icontains razorpay` both failed.

## Rubric alignment

- **L4 Working product / Agent org:** manager's bounce-back logic is the
  in-run defense; eval CI is the release-time defense. Both are needed.
- **L4 Evals:** "Automated eval pipeline in CI, blocks releases" — verified,
  blocking `broken-copywriter-prompt` right now.
- **Mentor verification test:** the failing run link above shows the exit
  code, the aggregate score, and the specific assertions that fired.
