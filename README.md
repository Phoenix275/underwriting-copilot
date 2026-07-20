# Underwriting Copilot — Working MVP

AI-assisted financial viability assessment for life insurance underwriting.
Pipeline: **PDF packet → extraction → conflict screen → dual risk engine + affordability screen → decision → grounded AI summary.**

> **Tech Mahindra — Global Learning Program (GLP) Internship · Finance Project 1**
> *AI-Powered Financial Viability Assessment Copilot.* Built during the Tech Mahindra GLP
> internship under managers **Rashmi Kubusada** and **Vasu Bheema Rao**. The applicant schema
> mirrors the real Manulife OTIP term-life application form; models learn from 17 public
> real-world datasets. Private prototype — not a production system and not affiliated with
> any insurer.

## Results (this build, seed-reproducible)

| Stage | Metric | Result |
|---|---|---|
| Extraction | Field-level accuracy vs printed ground truth (12 fields × 60 packets) | **100%** |
| Conflict screening | Recall on deliberately injected conflicts (6 check types) | **100%** |
| Conflict screening | Precision (false positives) | **100%** (0 FP) |
| Risk model | Logistic Regression AUC (held-out 20%) | **0.890** |
| Risk model | Gradient Boosting AUC | **0.885** |
| Affordability | Portfolio split (4-indicator financial screen) | **42% affordable · 36% strained · 22% not justified** |
| Decisioning | Straight-through rate — **evaluated on a held-out half**, thresholds tuned on the other | **43.2%** |
| Tests | Offline pytest suite (engine, affordability, doc round-trip, API), runs in CI | **54 passing** |

Extraction is 100% because generated PDFs are digital text; on real scans it will drop —
that is exactly the gap **Google Document AI** closes (adapter stub included, `DocumentAIExtractor`).
Both model AUCs beat the published academic benchmark of 0.79 for ML life-insurance risk
classification and approach the 0.86 XGBoost result in the literature.

## Run it

```bash
pip install -r requirements.txt
python src/run_pipeline.py        # ~7s: data → docs → extract → score → evaluate
python src/dashboard.py           # builds output/underwriting_copilot_mvp.html
uvicorn api:app --app-dir src     # REST API (POST /score, GET /cases, SQLite-backed)
pytest tests/ -q                  # 54 offline tests (also run in GitHub Actions CI)
docker build -t underwriting-copilot . && docker run -p 8501:8501 underwriting-copilot
```

Env knobs: `N_APPLICANTS` (default 4000), `N_PACKETS` (default 60).
Set `ANTHROPIC_API_KEY` to have case summaries written by Claude with a
groundedness check (every number must trace to a case fact); without a key
the deterministic template summaries are used — the pipeline never requires
network access or a paid key.

## Statistical honesty

- **Thresholds are tuned on half the portfolio and every reported STP /
  approve-zone-risk / decline-precision number comes from the held-out half**
  (`engine.optimize_thresholds`) — the headline rate is out-of-sample.
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
src/api.py           FastAPI REST API: POST /score → full engine verdict,
                     SQLite-persisted cases + human decisions (brief's
                     "REST APIs" + "SQL Database" items)
src/dashboard.py     single-file underwriter dashboard with embedded results
tests/               54 offline tests: conflicts, rule engine, decide branches,
                     affordability, premium, docgen→extract round trip, API
```

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
underwriting manuals (Week 3 manager session). No fairness audit yet — credit score can
proxy protected attributes; the auditable rule layer exists so that review is possible.
