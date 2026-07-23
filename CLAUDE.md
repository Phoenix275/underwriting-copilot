# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Underwriting Copilot — an AI-assisted life-insurance underwriting workbench built on
**synthetic data** (private prototype, no real insurer). A Python pipeline scores
application packets and a single-file React workbench presents the book. See `README.md`
and `AI_CONTEXT.md` for the domain model, decision logic, and honest-limits framing —
this file covers only how to work in the repo.

## Two halves, one contract

The system is a Python pipeline (`src/`) and a browser app (`web/`) joined by a **shared
scoring contract**:

- `src/engine.py` is the source of truth: 6-check conflict screen, weighted rule engine,
  LR + GradientBoosting training, affordability screen, and decision logic.
- `src/run_pipeline.py` orchestrates everything and writes `output/portfolio.json` (all
  cases) + `output/evaluation_report.json` (metrics, thresholds, **full-precision model
  coefficients**) + `output/models.joblib` (consumed by the API).
- `src/webdata.py` copies those two JSON files into `web/src/data/`.
- `web/src/lib/score.ts` is a **hand port of `engine.py`** so the browser can score a new
  application with no server. The report's coefficients let it re-derive scores in-browser.

**The invariant that ties them together:** `npm --prefix web run verify` replays all 200
pipeline cases through `score.ts` and fails if rule-engine or affordability verdicts differ
from the Python output. **If you touch `engine.py`, port the change to `score.ts` and run
verify — CI enforces this.** Note: the browser composite uses logistic regression, not
gradient boosting, because a boosted ensemble can't ship as coefficients.

## Full rebuild (pipeline or front-end change)

```bash
./.venv/bin/python src/run_pipeline.py   # ~7s — needs the venv (joblib isn't on system python)
./.venv/bin/python src/webdata.py        # export results into web/src/data/
npm --prefix web run release             # verify → snapshot build → sync to dashboard/ and docs/
```

`npm run release` = `verify` + `build:snapshot` + `sync`. `sync` copies `web/dist/index.html`
to both `dashboard/underwriting_copilot_mvp.html` and `docs/index.html`. **CI fails if those
committed copies drift from a fresh build**, if the build emits more than one file, if any
tag references an external origin, or if a `localhost` API URL leaks into the snapshot.

## Tests

```bash
./.venv/bin/pytest tests/ -q                          # 54 offline tests, no network
./.venv/bin/pytest tests/test_engine.py -q            # one file
./.venv/bin/pytest tests/test_engine.py::test_name    # one test
npm --prefix web run typecheck                         # tsc -b --noEmit
npm --prefix web run verify                            # browser engine must match Python
npm --prefix web run test:e2e                          # Playwright: sign-in → plane → queue → decision
```

CI (`.github/workflows/`) runs the pytest suite (Python 3.13) and the full web chain
(typecheck → verify → snapshot build → single-file + no-external-origin checks → committed-copy
diff → Playwright) on Node 20.

## Snapshot vs live

The React app runs in two modes off the same source:

- **Snapshot (default, the shipped artifact):** `--mode snapshot` forces `VITE_API_URL`
  empty and inlines everything into one `dist/index.html`. This is what `release` builds
  and what deploys.
- **Live:** point `VITE_API_URL` at the FastAPI service to read `GET /portfolio` and write
  decisions via `POST /cases/{id}/decision` (SQLite-backed). Falls back to the bundled book
  on any API failure.

```bash
./.venv/bin/python -m uvicorn api:app --app-dir src --port 8000
echo 'VITE_API_URL=http://localhost:8000' > web/.env.local   # gitignored
npm --prefix web run dev
```

Routing is **hash-based** (`web/src/lib/router.ts`) — `#/case/APP-1008`,
`#/portfolio?filter=red` — so the same file resolves identically on Cloudflare Pages,
GitHub Pages, and `file://`. Deploy to Cloudflare Pages with `./scripts/deploy-cloudflare.sh`
(one-time `npx wrangler login`; needs Node ≥ 20.19).

## Gotchas

- **`run_pipeline.py` is stateful.** It appends each run to `data/training_pool.csv` and
  retrains on the whole pool, so AUC / thresholds / STP drift on every run. Both that file
  and `data/model_history.json` are gitignored; delete them to reproduce README figures.
- **Views must read data via `useData()`, never by importing the JSON directly** — a static
  import freezes the bundled book and ignores live API data. `score.ts` is the one exception
  (a pure module reading through `data/store.ts`).
- **Verdicts are recomputed client-side at load** using the exported thresholds, not just
  the values baked into `portfolio.json`.
- Demo sign-in is an honest role selector (no real auth): senior / review / analyst /
  oversight (manager). **Never use a real person's name as a demo login** — the oversight
  persona is intentionally fictional.
- **Do not reintroduce Streamlit anywhere** (including comments) — it was removed
  deliberately; the app is a static single file and the Dockerfile serves only the optional
  FastAPI backend.

## Risk weights are evidence-anchored

Rule-engine medical weights are `round(28 × ln(real relative-mortality multiple))`, derived
in `src/derive_weights.py` (NHANES + NCHS Linked Mortality File) and cross-validated in
`src/prudential_validate.py` against real Prudential applicants. Raw datasets are gitignored
(redistribution restricted); the derivation scripts and cited weight table are committed. Do
not replace these with hand-picked numbers.
