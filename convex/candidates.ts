import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("candidates")
      .withIndex("by_candidate_id", (q) => q.eq("candidate_id", args.candidate_id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return args.candidate_id;
    }
    await ctx.db.insert("candidates", args);
    return args.candidate_id;
  },
});

export const listForRun = query({
  args: { run_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("candidates")
      .withIndex("by_run_id", (q) => q.eq("run_id", args.run_id))
      .collect();
  },
});
