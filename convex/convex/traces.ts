import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("traces")
      .withIndex("by_trace_id", (q) => q.eq("trace_id", args.trace_id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return args.trace_id;
    }
    await ctx.db.insert("traces", args);
    return args.trace_id;
  },
});

export const listForRun = query({
  args: { run_id: v.string() },
  handler: async (ctx, args) => {
    const rows = await ctx.db
      .query("traces")
      .withIndex("by_run_id", (q) => q.eq("run_id", args.run_id))
      .collect();
    return rows.sort((a, b) => (a.started_at_iso < b.started_at_iso ? -1 : 1));
  },
});

export const list = query({
  args: {},
  handler: async (ctx) => {
    const rows = await ctx.db.query("traces").collect();
    return rows.sort((a, b) => (a.started_at_iso < b.started_at_iso ? -1 : 1));
  },
});
