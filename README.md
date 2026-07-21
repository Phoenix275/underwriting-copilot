# Underwriting Copilot — Working MVP

AI-assisted financial viability assessment for life insurance underwriting.
Pipeline: **PDF packet → extraction → conflict screen → dual risk engine + affordability screen → decision → grounded AI summary.**

> **Tech Mahindra — Global Learning Program (GLP) Internship · Finance Project 1**
> *AI-Powered Financial Viability Assessment Copilot.* Built during the Tech Mahindra GLP
> internship under managers **Rashmi Kubusada** and **Vasu Bheema Rao**. The applicant schema
> mirrors the real Manulife OTIP term-life application form; models learn from 17 public
> real-world datasets. Private prototype — not a production system and not affiliated with
> any insurer.

## Results (first run from a clean checkout)

| Stage | Metric | Result |
|---|---|---|
| Extraction | Field-level accuracy vs printed ground truth (12 fields × 60 packets) | **100%** |
| Conflict screening | Recall on deliberately injected conflicts (6 check types) | **100%** |
| Conflict screening | Precision (false positives) | **100%** (0 FP) |
| Risk model | Logistic Regression AUC (held-out 20%) | **0.901** |
| Risk model | Gradient Boosting AUC | **0.889** |
| Affordability | Portfolio split (4-indicator financial screen) | **43% affordable · 35% strained · 22% not justified** |
| Decisioning | Straight-through rate — **evaluated on a held-out half**, thresholds tuned on the other | **79.9%** |
| Referral routing | Manual-review cases matched to underwriter desk by difficulty | **senior / review / analyst** |
| Tests | Offline pytest suite (engine, affordability, doc round-trip, API), runs in CI | **54 passing** |
| Front end | Browser scoring engine replayed against all 200 pipeline cases | **rule + affordability exact** |

> **These numbers move if you run the pipeline more than once.** `src/run_pipeline.py`
> appends each run's applicants to `data/training_pool.csv` and retrains on the whole
> pool, so the model genuinely improves — and the AUC, thresholds and STP rate shift with
> it. Both files are gitignored, so a fresh clone reproduces the table above exactly;
> a fourth local run will not. Delete `data/training_pool.csv` and
> `data/model_history.json` to get back to the published figures.

Extraction is 100% because generated PDFs are digital text; on real scans it will drop —
that is exactly the gap **Google Document AI** closes (adapter stub included, `DocumentAIExtractor`).

**On the AUC — read this before quoting it.** These scores sit *above* every published
life-underwriting benchmark, and that is a warning rather than a result. The closest true
peer, a model discriminating excess mortality on ~15,094 real life-insurance applicants,
reaches [0.708–0.743](https://pmc.ncbi.nlm.nih.gov/articles/PMC4696800/) (PLoS One, 2015);
general-population mortality models on rich cohort data top out around
[0.79–0.80](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(15)60175-1/fulltext)
(Ganna & Ingelsson, *The Lancet*, 2015). Our label is authored by the same synthetic
generator that produced the features, so the model is partly re-deriving a known rule
rather than predicting mortality. Treat 0.89 as evidence the pipeline works end to end,
not as evidence of predictive skill.

## Run it

```bash
pip install -r requirements-dev.txt   # pipeline + API + pytest
python src/run_pipeline.py        # ~7s: data → docs → extract → score → evaluate
python src/webdata.py             # export results into web/src/data/
uvicorn api:app --app-dir src     # REST API (POST /score, GET /cases, SQLite-backed)
pytest tests/ -q                  # 54 offline tests (also run in GitHub Actions CI)
docker build -t underwriting-copilot . && docker run -p 8501:8501 underwriting-copilot
```

The workbench front end is a Vite + React app in `web/`:

```bash
npm --prefix web ci
npm --prefix web run dev       # local dev server
npm --prefix web run verify    # replay all 200 cases through the browser engine
npm --prefix web run release   # verify → snapshot build → copy into dashboard/ and docs/
```

## Two tiers: a snapshot and a live service

The same React app runs in two modes, and the offline one is not a degraded
fallback — it is the artifact that ships.

**Snapshot (default).** `npm run release` builds with `--mode snapshot`, which forces
`VITE_API_URL` empty. The result is **one** self-contained `dist/index.html` with data,
fonts and styles inlined — served by Streamlit, by GitHub Pages from `docs/`, or opened
straight off disk with no server and no network. CI fails the build if a second asset
appears, if any tag references an external origin, or if a developer's local API URL
leaks in.

**Live.** Point the app at the FastAPI service and it reads the book over HTTP instead:

```bash
uvicorn api:app --app-dir src --port 8000      # terminal 1
echo 'VITE_API_URL=http://localhost:8000' > web/.env.local
npm --prefix web run dev                        # terminal 2
```

In live mode the workbench reads `GET /portfolio` (cases *and* the evaluation report
together, so thresholds always match the run that produced the cases) and an underwriter
can record a decision against a case, which persists to SQLite through
`POST /cases/{id}/decision` and reads back as an audit trail. Set
`COPILOT_ALLOWED_ORIGINS` to the origins you serve the bundle from — the default is
localhost only, deliberately, rather than a wildcard.

If the API is unreachable the app **does not** show an empty page: it falls back to the
bundled book and says so in the rail, with the reason and a retry, because an underwriter
silently reading yesterday's data is the worse failure.

Every view is deep-linkable — `#/case/APP-1008`, `#/portfolio?filter=red`, `#/evidence`.
Hash routing rather than paths, because the same file has to resolve identically on
GitHub Pages, inside a Streamlit iframe, and from `file://`.

Dependency files: `requirements.txt` is **deployment-only** (just Streamlit —
the hosted dashboard is a pre-built static HTML file and does no modelling at
runtime, so cloud builds stay fast and wheel-independent);
`requirements-pipeline.txt` is the pipeline + REST API stack;
`requirements-dev.txt` adds pytest.

Env knobs: `N_APPLICANTS` (default 4000), `N_PACKETS` (default 60).
Set `ANTHROPIC_API_KEY` to have case summaries written by Claude with a
groundedness check (every number must trace to a case fact); without a key
the deterministic template summaries are used — the pipeline never requires
network access or a paid key.

## Where the risk weights come from

The rule engine's medical weights are **not hand-picked** — each is
`round(28 × ln(real relative-mortality multiple))`, so the ratio between any two
point values is the ratio between two real mortality figures (`src/calibration.py`):

| Factor | Points | Real multiple | Source |
|---|---|---|---|
| Current smoker | 24 | 2.37× | NHANES linked mortality (our fit, cotinine-confirmed) — matches published 2.2–2.3× |
| Former smoker | 8 | 1.34× | NHIS Linked Mortality, Am J Prev Med 2018 |
| Diabetes | 16 | 1.80× | Emerging Risk Factors Collaboration, NEJM 2011 (820k people) |
| Other condition | 9 | 1.40× | NHANES linked mortality |
| BMI ≥ 35 | 12 | 1.55× | Prospective Studies Collaboration, Lancet 2009 (900k) |
| BMI < 18.5 | 15 | 1.70× | NHANES (2.27×, discounted for reverse causation) |
| Family cardiac history | 8 | 1.35× | NHIS / EPIC-Norfolk |

The multiples are derived in `src/derive_weights.py`, which downloads the
**NHANES 2007–2014 exam/lab files joined to the NCHS Linked Mortality File**
(20,435 real US adults, 2,293 linked deaths) and fits an age/sex-adjusted model —
real people, real death outcomes, public-domain CDC data. The result is
cross-validated against **59,381 real Prudential applicants** (Kaggle Prudential
Life Insurance Assessment): applying these weights to the factors Prudential
exposes agrees with the insurer's own 1–8 underwriting rating at **AUC 0.68**,
and the same method scores **AUC 0.72–0.73 on real applicants** — squarely inside
the published 0.71–0.74 band for real life-underwriting models.

Financial and behavioural factors (debt, credit, driving, alcohol, Section-6
declarations) are **not** mortality factors, so they are not in this table — they
follow conventional underwriting debits and are labelled as such in the engine.
Reproduce: `python src/derive_weights.py` then `python src/prudential_validate.py`.
Raw datasets are gitignored (redistribution restricted); the derivation scripts
and the resulting cited weight table are committed.

## Statistical honesty

- **Thresholds are tuned on half the portfolio and every reported STP /
  approve-zone-risk / decline-precision number comes from the held-out half**
  (`engine.optimize_thresholds`) — the headline rate is out-of-sample.
- **Straight-through processing is maximised with no artificial cap, and the
  trade is shown, not hidden.** The threshold search is unconstrained — there is
  no ceiling on approve-zone risk and no floor under the decline line. The one
  guard is a minimum auto-decline precision of 0.50, and it exists to stop the
  optimiser from *gaming* the metric rather than to balance the model: with no
  floor at all, the maximum is to auto-decline the entire book (STP≈100%, but it
  rejects every customer and leaves nothing to underwrite). With that single
  guard, held-out STP is **79.9%**. The cost is auto-decline precision at
  **52%** — about half of auto-declines are applicants who were not actually
  high-risk — which is the deliberately-accepted sacrifice, surfaced on the model
  card. The conflict, affordability and engine-disagreement gates still force a
  referral regardless of score, so nothing here auto-approves a contradicted or
  unaffordable case, and the ~800 referrals it does produce are routed across
  three underwriter desks by difficulty.
- The external-data prior is an **AUC-weighted** blend; dataset models at or
  near chance (AUC < 0.55) are excluded and shown as such on the model card.
- Fairness is audited by **age band and by sex** — verdict mix plus per-group
  model **FPR/FNR**, because a group can have a fair outcome mix while bearing
  an unfair share of the errors. Sex is audited specifically because it feeds
  both the external-data and Framingham priors.

## Repository layout

```
src/datagen.py       synthetic applicants, correlated risk factors, ground-truth label
src/docgen.py        5-doc PDF packets: application form (yes/no + fill-in detail boxes,
                     per manager feedback on the real form), payslip, paramedical report,
                     3-month bank statement (deposits + expense categories), tax slip.
                     Injects conflicts at a known 30% rate → measurable detection.
src/extract.py       Extractor interface. LocalTextExtractor (pdfplumber, runs anywhere)
                     + DocumentAIExtractor adapter stub for GCP.
src/engine.py        6-check conflict screen (equal for every applicant) · weighted rule
                     engine · LR + GradientBoosting training + metrics · affordability
                     screen (premium-to-income, disposable income, coverage multiple,
                     debt service) · decision logic (major conflict → auto-refer;
                     rule/ML disagreement → auto-refer; not-justified → financial UW).
src/run_pipeline.py  orchestrator; writes evaluation_report.json + portfolio.json
                     + models.joblib (consumed by the REST API)
src/summaries.py     Claude-written case summaries w/ groundedness check;
                     falls back to the deterministic template without a key
src/api.py           FastAPI REST API (brief's "REST APIs" + "SQL Database" items):
                     GET  /portfolio          the scored book + evaluation report
                     POST /score              one applicant → full engine verdict
                     GET  /cases[/{id}]       API-scored and batch cases
                     POST /cases/{id}/decision   record a human decision
                     GET  /cases/{id}/decisions  the audit trail
src/dashboard.py     legacy single-file dashboard generator (superseded by web/)
src/webdata.py       exports portfolio + report into web/src/data/
tests/               54 offline tests: conflicts, rule engine, decide branches,
                     affordability, premium, docgen→extract round trip, API

web/                 the workbench — Vite + React + TypeScript, builds to one HTML file
  src/lib/score.ts       browser port of engine.py; verified against all 200 cases
  src/lib/projection.ts  perspective camera for the portfolio plane
  src/lib/guilloche.ts   hypotrochoid rosettes — the security-print house pattern
  src/lib/router.ts      hash routing, so every view is a shareable link
  src/data/source.ts     live API read with a bundled-snapshot fallback
  src/data/benchmarks.ts published industry figures, each with a source and a date
  src/auth/              demo role sign-in (4 personas) — attributes recorded decisions
  src/components/WhatIf.tsx   inline sensitivity tool on a case (not the new-application form)
  src/views/             Portfolio · Case file · How it decides · Evidence · New application
  scripts/verify-port.mjs  replays the pipeline's cases through the browser engine
dashboard/           built workbench, served by Streamlit
docs/                the same file, served by GitHub Pages
```

## Why the plane is SVG and not WebGL

The portfolio view is real perspective projection (`web/src/lib/projection.ts`), not a
chart library and not three.js. Measured on this stack, `@react-three/fiber` + `drei`
costs **~259 KB gzip**, and because the build inlines every chunk into one file that
cost cannot be lazy-loaded away — it would be unconditional, on a page that is often
opened on a phone. Projecting into SVG costs **0 KB**, keeps all 200 markers as real
DOM nodes (so each one is focusable and readable by a screen reader), and avoids the
[WebGL canvas-resize leak on iOS Safari](https://bugs.webkit.org/show_bug.cgi?id=219780)
that a responsive 3D view would hit on every orientation change.

## The six conflict checks (equal screening)

1. `income_mismatch` (major) — declared income vs payslip annualized, >15% gap
2. `smoker_nondisclosure` (major) — form says No tobacco, cotinine lab POSITIVE
3. `dob_mismatch` (major) — application DOB ≠ ID recorded at paramedical exam
4. `debt_understated` (minor) — bureau debt >150% of declared debt
5. `income_deposit_mismatch` (major) — bank deposits run >20% below payslip income
6. `tax_income_mismatch` (major) — tax-reported income >15% below declared income

Every packet runs all six; majors force referral to a human.

## The affordability screen (financial underwriting — the brief's core ask)

Every applicant passes four financial-viability indicators, independent of
mortality risk: **premium-to-income** (≤5%, strained to 10%), **disposable
income after premium** (net − expenses − premium vs a floor), **coverage-to-
income multiple** (age-banded cap: 25× under 40 → 10× at 60+), and
**debt-service ratio** (≤20% of net income). Verdicts: AFFORDABLE · STRAINED ·
NOT JUSTIFIED. Any failed indicator refers the case to financial underwriting
regardless of risk score — a perfectly healthy applicant seeking 29× income in
coverage gets caught. Premiums come from an indicative age/tobacco/product
rate model (`engine.estimate_premium`).

**Which of these are industry norms, and which are ours.** The coverage-to-income
cap is modelled on published carrier guidance — [Brighthouse
Financial](https://pinneyinsurance.com/underwriting-docs/Brighthouse-UW-Guide.pdf)
uses 30× under 40 declining to 10× at 61–70, and [Pacific
Life](https://www.champion-agency.com/wp-content/uploads/2020/05/PL_Financial_UW.pdf)
30× at 20–30 declining to 5× at 66–75; ours is deliberately a notch more
conservative. The other three thresholds have **no published life-insurance
equivalent** — no insurer or reinsurer publishes a premium-to-income cap or a
debt-service standard for life cover. They are defensible design choices, and
the UI labels them as such rather than as benchmarks.

## Upgrade paths

- **Real documents:** implement `DocumentAIExtractor.extract_packet` against a Document AI
  Form Parser processor; the rest of the pipeline is untouched (same output schema).
- **Kaggle validation:** download the *Prudential Life Insurance Assessment* dataset
  (kaggle.com/c/prudential-life-insurance-assessment — requires a free account; not
  reachable from this sandbox). Map its `Response` 1–8 rating to a binary high-risk label
  (e.g. Response ≤ 4) and re-run `engine.train_models` to validate the model architecture
  on non-synthetic data.
- **Gemini/Vertex on GCP:** the AI-summary prompt in `dashboard.py` is model-agnostic —
  point it at Vertex AI to match the internship's tool stack.

## Honest limits

Synthetic data proves the *pipeline*, not production risk weights. The label is authored,
so model performance is an upper bound. Rule weights need validation against real
underwriting manuals (Week 3 manager session). Credit score can proxy protected
attributes — the auditable rule layer exists so that review is possible, and the
fairness tables report per-group FPR/FNR by age band and sex, not just verdict mix.

Not claimed, and stated as such in the workbench's Evidence view:

- **Colorado's quantitative proxy-discrimination test.** The regulation that would
  specify the BIFSG method remains a *draft*, and the Division waived the testing
  requirement for the 2024 and 2025 reports. This build holds no race or ethnicity
  proxy, so it does not perform that test.
- **Cost savings.** No authoritative cost-per-policy or underwriting expense ratio
  could be sourced for US life insurance, so this project makes no cost claim.
- **Income misstatement rate.** No published figure exists, so the injection rate
  for that conflict is a modelling assumption, not a calibrated one.
