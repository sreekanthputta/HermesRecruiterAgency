export type Specialist =
  | 'manager'
  | 'role_strategist'
  | 'sourcer'
  | 'copywriter'
  | 'qa'
  | 'gmail_draft_writer';

export interface Run {
  run_id: string;
  created_at_iso: string;
  founder_request: string;
  role_type: string;
  location: string;
  plan: Array<{ step: number; specialist: string; task: string }>;
  rubric: {
    must_have: string[];
    nice_to_have: string[];
    ignore: string[];
    weights: Record<string, number>;
  };
  status: 'in_progress' | 'done' | 'failed';
  totals: {
    tokens_in: number;
    tokens_out: number;
    cost_usd: number;
    duration_sec: number;
  };
}

export interface Candidate {
  candidate_id: string;
  run_id: string;
  name: string;
  profile_url: string;
  evidence_url: string;
  evidence_summary: string;
  location: string;
  rubric_score: number;
  rubric_breakdown: Record<string, number>;
  why_match: string;
  outreach_draft: string;
  qa_verdict: 'pass' | 'block' | '';
  qa_reason: string;
  gmail_draft_id: string;
  status: string;
}

export interface Trace {
  trace_id: string;
  run_id: string;
  parent_trace_id: string | null;
  specialist: Specialist;
  task_brief: string;
  input_summary: string;
  output_summary: string;
  output_full?: string;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number;
  model: string;
  duration_ms: number;
  started_at_iso: string;
  verdict: 'accepted' | 'bounced_back' | 'error';
  bounce_reason: string;
  revision_of_trace_id: string | null;
}
