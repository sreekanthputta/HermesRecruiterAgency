import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const upsert = mutation({
  args: {
    run_id: v.string(),
    created_at_iso: v.string(),
    founder_request: v.string(),
    role_type: v.string(),
    location: v.optional(v.string()),
    plan: v.any(),
    rubric: v.optional(v.any()),
    status: v.string(),
    totals: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("runs")
      .withIndex("by_run_id", (q) => q.eq("run_id", args.run_id))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, args);
      return args.run_id;
    }
    await ctx.db.insert("runs", args);
    return args.run_id;
  },
});

export const getByRunId = query({
  args: { run_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("runs")
      .withIndex("by_run_id", (q) => q.eq("run_id", args.run_id))
      .first();
  },
});

export const list = query({
  args: {},
  handler: async (ctx) => {
    const all = await ctx.db.query("runs").collect();
    return all.sort((a, b) => (a.created_at_iso < b.created_at_iso ? 1 : -1));
  },
});
