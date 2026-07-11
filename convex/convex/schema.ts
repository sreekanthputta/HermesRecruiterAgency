import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  runs: defineTable({
    run_id: v.string(),
    created_at_iso: v.string(),
    founder_request: v.string(),
    role_type: v.string(),
    location: v.optional(v.string()),
    plan: v.any(),
    rubric: v.optional(v.any()),
    status: v.string(),
    totals: v.optional(v.any()),
  }).index("by_run_id", ["run_id"]),

  candidates: defineTable({
    candidate_id: v.string(),
    run_id: v.string(),
    name: v.string(),
    profile_url: v.string(),
    evidence_url: v.optional(v.string()),
    evidence_summary: v.optional(v.string()),
    location: v.optional(v.string()),
    rubric_score: v.optional(v.number()),
    rubric_breakdown: v.optional(v.any()),
    why_match: v.optional(v.string()),
    outreach_draft: v.optional(v.string()),
    qa_verdict: v.optional(v.string()),
    qa_reason: v.optional(v.string()),
    gmail_draft_id: v.optional(v.string()),
    status: v.string(),
  })
    .index("by_run_id", ["run_id"])
    .index("by_candidate_id", ["candidate_id"]),

  traces: defineTable({
    trace_id: v.string(),
    run_id: v.string(),
    parent_trace_id: v.optional(v.string()),
    specialist: v.string(),
    task_brief: v.optional(v.string()),
    input_summary: v.optional(v.string()),
    output_summary: v.optional(v.string()),
    output_full: v.optional(v.string()),
    tokens_in: v.optional(v.number()),
    tokens_out: v.optional(v.number()),
    cost_usd: v.optional(v.number()),
    model: v.optional(v.string()),
    duration_ms: v.optional(v.number()),
    started_at_iso: v.string(),
    verdict: v.optional(v.string()),
    bounce_reason: v.optional(v.string()),
    revision_of_trace_id: v.optional(v.string()),
  })
    .index("by_run_id", ["run_id"])
    .index("by_trace_id", ["trace_id"])
    .index("by_parent", ["parent_trace_id"]),
});
