import { useEffect, useMemo, useState } from 'react';
import { useQuery } from 'convex/react';
import { anyApi } from 'convex/server';
import sample from './sample.json';
import type { Candidate, Run, Trace, Specialist } from './types';

const ALL_SPECIALISTS: Specialist[] = [
  'manager',
  'role_strategist',
  'sourcer',
  'copywriter',
  'qa',
  'gmail_draft_writer',
];

const SPECIALIST_COLOR: Record<string, string> = {
  manager: 'bg-purple-500/20 border-purple-400 text-purple-200',
  role_strategist: 'bg-blue-500/20 border-blue-400 text-blue-200',
  sourcer: 'bg-emerald-500/20 border-emerald-400 text-emerald-200',
  copywriter: 'bg-amber-500/20 border-amber-400 text-amber-200',
  qa: 'bg-rose-500/20 border-rose-400 text-rose-200',
  gmail_draft_writer: 'bg-teal-500/20 border-teal-400 text-teal-200',
};

function formatUsd(n: number) {
  return `$${n.toFixed(3)}`;
}

function formatTokens(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return String(n);
}

export default function App({ demoMode }: { demoMode: boolean }) {
  // Live queries — these return undefined in demo mode (no provider)
  const liveRuns = demoMode ? undefined : (useQuery(anyApi.runs.list, {}) as Run[] | undefined);
  const liveCandidates = demoMode
    ? undefined
    : (useQuery(anyApi.candidates.list, {}) as Candidate[] | undefined);
  const liveTraces = demoMode ? undefined : (useQuery(anyApi.traces.list, {}) as Trace[] | undefined);

  const runs: Run[] = demoMode
    ? (sample.runs as Run[])
    : liveRuns ?? [];
  const candidatesAll: Candidate[] = demoMode
    ? (sample.candidates as Candidate[])
    : liveCandidates ?? [];
  const tracesAll: Trace[] = demoMode
    ? (sample.traces as Trace[])
    : liveTraces ?? [];

  const usingDemo = demoMode;
  const liveLoading = !demoMode && liveRuns === undefined;

  const [selectedRunId, setSelectedRunId] = useState<string>(runs[0]?.run_id ?? '');
  useEffect(() => {
    if (!selectedRunId && runs[0]) setSelectedRunId(runs[0].run_id);
  }, [runs, selectedRunId]);

  const [enabledSpecialists, setEnabledSpecialists] = useState<Set<Specialist>>(
    new Set(ALL_SPECIALISTS)
  );
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [rightTab, setRightTab] = useState<'candidates' | 'trace'>('candidates');

  const run = runs.find((r) => r.run_id === selectedRunId) ?? runs[0];
  const candidates = candidatesAll.filter((c) => c.run_id === run?.run_id);
  const traces = tracesAll.filter((t) => t.run_id === run?.run_id);
  const selectedTrace = traces.find((t) => t.trace_id === selectedTraceId) ?? null;

  const filteredTraces = traces.filter((t) => enabledSpecialists.has(t.specialist));

  function toggleSpecialist(s: Specialist) {
    setEnabledSpecialists((prev) => {
      const next = new Set(prev);
      if (next.has(s)) next.delete(s);
      else next.add(s);
      return next;
    });
  }

  return (
    <div className="min-h-screen flex flex-col">
      {usingDemo && (
        <div className="bg-yellow-500/20 border-b border-yellow-500/60 text-yellow-100 text-sm px-4 py-2">
          Demo data — live Convex not yet connected. Set <code className="bg-black/40 px-1 rounded">VITE_CONVEX_URL</code> in <code className="bg-black/40 px-1 rounded">web/.env.local</code> and redeploy.
        </div>
      )}

      <header className="border-b border-slate-800 px-6 py-4 flex items-center gap-6 flex-wrap">
        <div>
          <h1 className="text-xl font-bold">Hermes Recruiter Agency</h1>
          <p className="text-xs text-slate-400">Run Board · trace tree · candidates · cost</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400">Run</label>
          <select
            value={selectedRunId}
            onChange={(e) => {
              setSelectedRunId(e.target.value);
              setSelectedTraceId(null);
            }}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm"
          >
            {runs.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id} · {r.role_type}
              </option>
            ))}
          </select>
        </div>
        {run && (
          <div className="flex items-center gap-4 ml-auto text-sm">
            <span className="text-slate-400">
              Status:{' '}
              <span
                className={
                  run.status === 'done'
                    ? 'text-emerald-300'
                    : run.status === 'failed'
                    ? 'text-rose-300'
                    : 'text-amber-300'
                }
              >
                {run.status}
              </span>
            </span>
            <span className="text-slate-400">
              Cost: <span className="text-white font-semibold">{formatUsd(run.totals.cost_usd)}</span>
            </span>
            <span className="text-slate-400">
              Tokens:{' '}
              <span className="text-white">
                {formatTokens(run.totals.tokens_in)}/{formatTokens(run.totals.tokens_out)}
              </span>
            </span>
            <span className="text-slate-400">
              Duration: <span className="text-white">{run.totals.duration_sec}s</span>
            </span>
          </div>
        )}
      </header>

      {run && (
        <div className="px-6 py-3 border-b border-slate-800 text-sm text-slate-300 bg-slate-900/50">
          <span className="text-slate-500">Founder request:</span> {run.founder_request}
        </div>
      )}

      <div className="flex-1 grid grid-cols-1 md:grid-cols-[380px_1fr] gap-0 min-h-0">
        {/* LEFT: Trace tree */}
        <aside className="border-r border-slate-800 p-4 overflow-auto">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-sm text-slate-200">Trace tree</h2>
            <span className="text-xs text-slate-500">{filteredTraces.length} nodes</span>
          </div>

          <TraceTree
            traces={filteredTraces}
            onSelect={(t) => {
              setSelectedTraceId(t.trace_id);
              setRightTab('trace');
            }}
            selectedId={selectedTraceId}
          />

          <div className="mt-6 pt-4 border-t border-slate-800">
            <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-2">Filter by agent</h3>
            <div className="space-y-1">
              {ALL_SPECIALISTS.map((s) => (
                <label key={s} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enabledSpecialists.has(s)}
                    onChange={() => toggleSpecialist(s)}
                    className="accent-emerald-500"
                  />
                  <span
                    className={
                      'px-2 py-0.5 rounded text-xs border ' + (SPECIALIST_COLOR[s] ?? '')
                    }
                  >
                    {s}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </aside>

        {/* RIGHT: Details */}
        <section className="p-4 overflow-auto">
          <div className="flex items-center gap-2 mb-4 border-b border-slate-800">
            <TabButton active={rightTab === 'candidates'} onClick={() => setRightTab('candidates')}>
              Candidates ({candidates.length})
            </TabButton>
            <TabButton active={rightTab === 'trace'} onClick={() => setRightTab('trace')}>
              Trace detail
            </TabButton>
          </div>

          {rightTab === 'candidates' && <CandidatesTable candidates={candidates} />}
          {rightTab === 'trace' && <TraceDetail trace={selectedTrace} />}
        </section>
      </div>

      <footer className="border-t border-slate-800 px-6 py-2 text-xs text-slate-500 flex items-center justify-between">
        <span>Powered by Hermes · Convex · Linkup · Cloudflare Pages · ElevenLabs</span>
        <span>{usingDemo ? 'demo mode' : 'live'}</span>
      </footer>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: any;
}) {
  return (
    <button
      onClick={onClick}
      className={
        'px-3 py-2 text-sm border-b-2 -mb-px ' +
        (active
          ? 'border-emerald-500 text-white'
          : 'border-transparent text-slate-400 hover:text-slate-200')
      }
    >
      {children}
    </button>
  );
}

function TraceTree({
  traces,
  onSelect,
  selectedId,
}: {
  traces: Trace[];
  onSelect: (t: Trace) => void;
  selectedId: string | null;
}) {
  // Group children by parent_trace_id
  const byParent = useMemo(() => {
    const map = new Map<string | null, Trace[]>();
    for (const t of traces) {
      const key = t.parent_trace_id ?? null;
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(t);
    }
    // Sort each group by started_at
    for (const arr of map.values()) {
      arr.sort((a, b) => a.started_at_iso.localeCompare(b.started_at_iso));
    }
    return map;
  }, [traces]);

  const roots = byParent.get(null) ?? [];
  if (roots.length === 0) {
    return <p className="text-sm text-slate-500 italic">No traces yet for this run.</p>;
  }

  return (
    <div className="space-y-1">
      {roots.map((r) => (
        <TraceNode
          key={r.trace_id}
          trace={r}
          byParent={byParent}
          depth={0}
          onSelect={onSelect}
          selectedId={selectedId}
        />
      ))}
    </div>
  );
}

function TraceNode({
  trace,
  byParent,
  depth,
  onSelect,
  selectedId,
}: {
  trace: Trace;
  byParent: Map<string | null, Trace[]>;
  depth: number;
  onSelect: (t: Trace) => void;
  selectedId: string | null;
}) {
  const children = byParent.get(trace.trace_id) ?? [];
  const isBounced = trace.verdict === 'bounced_back';
  const isError = trace.verdict === 'error';
  const isRevision = !!trace.revision_of_trace_id;
  const isSelected = selectedId === trace.trace_id;

  const border = isBounced
    ? 'border-rose-500'
    : isError
    ? 'border-rose-700'
    : isSelected
    ? 'border-emerald-400'
    : 'border-slate-700';

  return (
    <div style={{ marginLeft: depth * 14 }} className="relative">
      <button
        onClick={() => onSelect(trace)}
        className={
          'w-full text-left border rounded px-2 py-1.5 hover:bg-slate-800/60 transition ' +
          border +
          ' ' +
          (isSelected ? 'bg-slate-800/80' : 'bg-slate-900/50')
        }
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={
              'text-xs px-1.5 py-0.5 rounded border ' + (SPECIALIST_COLOR[trace.specialist] ?? '')
            }
          >
            {trace.specialist}
          </span>
          {isBounced && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/30 text-rose-200 border border-rose-500/60">
              BOUNCED
            </span>
          )}
          {isRevision && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-500/30 text-yellow-100 border border-yellow-500/60">
              REVISION
            </span>
          )}
          {isError && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-700/40 text-rose-100 border border-rose-500">
              ERROR
            </span>
          )}
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex gap-3 flex-wrap">
          <span>{formatUsd(trace.cost_usd)}</span>
          <span>
            {formatTokens(trace.tokens_in)}/{formatTokens(trace.tokens_out)}t
          </span>
          <span>{trace.duration_ms}ms</span>
        </div>
        <div className="text-[11px] text-slate-300 mt-0.5 line-clamp-1">{trace.task_brief}</div>
      </button>
      {children.length > 0 && (
        <div className="mt-1 space-y-1 border-l border-slate-800 pl-2">
          {children.map((c) => (
            <TraceNode
              key={c.trace_id}
              trace={c}
              byParent={byParent}
              depth={depth + 1}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function CandidatesTable({ candidates }: { candidates: Candidate[] }) {
  if (candidates.length === 0) {
    return <p className="text-sm text-slate-500 italic">No candidates yet for this run.</p>;
  }
  return (
    <div className="overflow-auto">
      <table className="w-full text-sm">
        <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
          <tr>
            <th className="text-left py-2 px-2">Name</th>
            <th className="text-left py-2 px-2">QA</th>
            <th className="text-left py-2 px-2">Why match</th>
            <th className="text-left py-2 px-2">Evidence</th>
            <th className="text-left py-2 px-2">Gmail</th>
          </tr>
        </thead>
        <tbody>
          {candidates
            .slice()
            .sort((a, b) => b.rubric_score - a.rubric_score)
            .map((c) => (
              <tr key={c.candidate_id} className="border-b border-slate-800 hover:bg-slate-800/40">
                <td className="py-2 px-2">
                  <a
                    href={c.profile_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-300 hover:underline font-medium"
                  >
                    {c.name}
                  </a>
                  <div className="text-[11px] text-slate-500">{c.location}</div>
                </td>
                <td className="py-2 px-2">
                  {c.qa_verdict === 'pass' && (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-200 border border-emerald-500/60">
                      pass
                    </span>
                  )}
                  {c.qa_verdict === 'block' && (
                    <span
                      className="text-[11px] px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-200 border border-rose-500/60"
                      title={c.qa_reason}
                    >
                      block
                    </span>
                  )}
                  {!c.qa_verdict && (
                    <span className="text-[11px] text-slate-500">—</span>
                  )}
                </td>
                <td className="py-2 px-2 text-slate-300 max-w-[280px]">
                  <div className="line-clamp-2">{c.why_match}</div>
                </td>
                <td className="py-2 px-2">
                  <a
                    href={c.evidence_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-300 hover:underline text-xs"
                    title={c.evidence_summary}
                  >
                    link
                  </a>
                </td>
                <td className="py-2 px-2">
                  {c.gmail_draft_id ? (
                    <span className="text-[11px] px-2 py-0.5 rounded-full bg-teal-500/20 text-teal-200 border border-teal-500/60">
                      Draft in Gmail
                    </span>
                  ) : (
                    <span className="text-[11px] text-slate-500">—</span>
                  )}
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function TraceDetail({ trace }: { trace: Trace | null }) {
  if (!trace) {
    return <p className="text-sm text-slate-500 italic">Click a trace node to see details.</p>;
  }
  return (
    <div className="space-y-4 text-sm">
      <div className="flex items-center gap-3 flex-wrap">
        <span
          className={
            'text-xs px-2 py-0.5 rounded border ' + (SPECIALIST_COLOR[trace.specialist] ?? '')
          }
        >
          {trace.specialist}
        </span>
        <span
          className={
            'text-xs px-2 py-0.5 rounded border ' +
            (trace.verdict === 'accepted'
              ? 'bg-emerald-500/20 text-emerald-200 border-emerald-500/60'
              : trace.verdict === 'bounced_back'
              ? 'bg-rose-500/20 text-rose-200 border-rose-500/60'
              : 'bg-rose-700/40 text-rose-100 border-rose-500')
          }
        >
          {trace.verdict}
        </span>
        {trace.revision_of_trace_id && (
          <span className="text-xs px-2 py-0.5 rounded border bg-yellow-500/20 text-yellow-100 border-yellow-500/60">
            revision of {trace.revision_of_trace_id}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <Stat label="Model" value={trace.model} />
        <Stat label="Cost" value={formatUsd(trace.cost_usd)} />
        <Stat
          label="Tokens (in/out)"
          value={`${formatTokens(trace.tokens_in)} / ${formatTokens(trace.tokens_out)}`}
        />
        <Stat label="Duration" value={`${trace.duration_ms} ms`} />
      </div>

      <Section title="Task brief">{trace.task_brief}</Section>
      <Section title="Input summary">{trace.input_summary}</Section>
      <Section title="Output summary">{trace.output_summary}</Section>
      {trace.bounce_reason && (
        <Section title="Bounce reason" tone="danger">
          {trace.bounce_reason}
        </Section>
      )}
      {trace.output_full && <Section title="Output (full)">{trace.output_full}</Section>}

      <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-800">
        trace_id: <code>{trace.trace_id}</code> · started {trace.started_at_iso}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-slate-800 rounded px-3 py-2 bg-slate-900/50">
      <div className="text-slate-500 text-[10px] uppercase tracking-wider">{label}</div>
      <div className="text-slate-100 mt-0.5">{value}</div>
    </div>
  );
}

function Section({
  title,
  children,
  tone,
}: {
  title: string;
  children: any;
  tone?: 'danger';
}) {
  const border = tone === 'danger' ? 'border-rose-500/60 bg-rose-500/10' : 'border-slate-800';
  return (
    <div className={'border rounded p-3 ' + border}>
      <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">{title}</div>
      <div className="text-slate-100 whitespace-pre-wrap text-sm">{children}</div>
    </div>
  );
}
