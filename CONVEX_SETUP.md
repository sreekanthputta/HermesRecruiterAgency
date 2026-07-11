# Convex setup - 3 steps

Convex is the +25 power-up backend that stores all runs, candidates, and traces. The Python client falls back to `demo/data/*.json` files until you complete these steps, so the demo works even without live Convex.

## Steps

1. Install Convex CLI (or use `npx`):

   ```sh
   npm install -g convex
   # or just use `npx convex ...` below - no install needed
   ```

2. From the repo root, start the dev deployment:

   ```sh
   cd convex && npx convex dev
   ```

   - First run opens a browser: sign in with GitHub or Google.
   - Creates a project, pushes `schema.ts` + the mutation/query functions.
   - Prints `CONVEX_URL` (e.g. `https://xxxxx.convex.cloud`) and a deploy key.

3. Paste both values into `.env` at the repo root:

   ```
   CONVEX_URL=https://xxxxx.convex.cloud
   CONVEX_DEPLOY_KEY=prod:...  # optional, only for admin/CI
   ```

   Restart the demo. Python client will detect `CONVEX_URL` and switch to live mode automatically.

## Verifying it works

```sh
python -c "from hermes.integrations.convex_client import upsert_run; upsert_run({'run_id':'test','created_at_iso':'2026-07-11T00:00:00Z','founder_request':'hello','role_type':'test','plan':[],'status':'in_progress'}); print('ok')"
```

- With `CONVEX_URL` unset: prints `[convex_client] Local fallback mode` and writes to `demo/data/runs.json`.
- With `CONVEX_URL` set and reachable: prints `[convex_client] Convex live mode` and the row shows up in the Convex dashboard.

## Fallback behavior

Until step 3 is done, all writes go to:

- `demo/data/runs.json`
- `demo/data/candidates.json`
- `demo/data/traces.json`

Other builders can develop against the Python client immediately. The web board (Builder E) needs live Convex to render in real time.
