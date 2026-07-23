# Underwriting Copilot — Presenter's Guide

Everything you need to understand and present the product. Read top-to-bottom once; the
**5-Minute Demo Script** (§8) and **Q&A** (§9) are what you'll actually lean on live.

**Live app:** https://underwriting-copilot.pages.dev
**One-line pitch:** An AI-assisted life-insurance underwriting workbench that scores every
application, auto-decides the clear-cut ones, and routes the rest to a human — with a full
audit trail and honest, evidence-anchored risk weights.

---

## 1. The 30-second version (say this first)

> "Life insurers get thousands of applications. Most are straightforward, but a human
> underwriter has to touch each one, and evidence-gathering takes weeks. Our Copilot
> extracts the application, screens it for fraud/conflicts, scores the risk with a blend of
> auditable rules and machine learning, and then either auto-approves, auto-declines, or
> routes it to the right underwriter. The human still makes every borderline call — the AI
> just does the reading and ranking so they spend their time where it matters. Everything is
> logged, so a regulator can always ask 'why?' and get a straight answer."

---

## 2. The problem it solves

- **Underwriter capacity.** Every application needs a human touch today; the workforce is
  ageing and shrinking.
- **Cycle time.** A manual review is hundreds of pages; ordering medical evidence (an APS)
  costs ~$350 and takes weeks.
- **Consistency & defensibility.** Regulators (the NAIC AI model bulletin) now expect every
  AI-influenced decision — especially declines — to be explainable and auditable.

The Copilot attacks all three: it automates the reading, ranks the human's work by what
matters, and records why every decision was made.

---

## 3. What the product actually is (two halves)

1. **A Python pipeline** (`src/`) — takes 200 synthetic application packets, extracts the
   fields, runs a 6-check conflict screen, trains the models, scores every case, and writes
   the results to JSON.
2. **A browser workbench** — a single self-contained HTML file (no server needed) that
   presents the scored book with role-based views. **This is what you demo.**

> **Important honesty point:** the data is **100% synthetic** — no real applicants. That's a
> *strength* to mention: because every case has a known ground-truth answer, we can actually
> measure how accurate the model is.

---

## 4. How to run / access it

- **Easiest (for the presentation):** just open the live URL —
  https://underwriting-copilot.pages.dev — in any browser. No login server; it's a demo
  role-selector.
- **Locally:** open the file `output/underwriting_copilot_mvp.html` directly in a browser
  (it's fully self-contained). To regenerate it from the pipeline:
  ```
  ./.venv/bin/python src/run_pipeline.py    # ~7s — scores all cases
  ./.venv/bin/python src/dashboard.py       # writes output/underwriting_copilot_mvp.html
  ```
- **Tip:** if the live site looks stale after an update, hard-refresh (Cmd+Shift+R).

---

## 5. The scoring engine — the heart of the demo

Every applicant gets one **Composite Risk Score, 0–100**:

```
Composite Score = 50% × Rule Engine + 50% × Machine Learning
```

- **Rule engine** — a fully auditable checklist. Every point traces to a documented weight.
  The medical weights aren't made up: they're `round(28 × ln(relative-mortality multiple))`
  derived from real public health data (NHANES + national mortality files). **Say this** — it's
  what makes the model defensible.
- **ML model** — a gradient-boosting model trained on the outcomes; it catches interactions
  the rules miss. AUC ≈ 89% on held-out cases.
- **Why blend them?** One bad model can never single-handedly approve a risky case, and the
  rules can never miss a pattern the data learned.

### The traffic light (memorize these three numbers: 51 and 90)

| Score | Band | Outcome |
|---|---|---|
| **0–50** | 🟢 Green | **APPROVE** — auto-approved, no human touch |
| **51–89** | 🟡 Yellow | **MANUAL REVIEW** — a human underwriter decides |
| **90–100** | 🔴 Red | **DECLINE** — risk exceeds appetite |

**The score alone sets the band.** A 22 is always green; a 95 is always red. The one hard
override is **material misrepresentation** (the application contradicts the medical/ID
evidence — e.g. said non-smoker but the lab says otherwise) → declined regardless of score,
because that's fraud, not risk. Other flags (affordability, conflicts) are shown to the
reviewer but don't move the band.

---

## 6. The six roles (this is the backbone of the demo)

Sign in with any of these — it's an honest role selector, no real passwords:

| Role | Login | What they see / do |
|---|---|---|
| **Senior underwriter** | `mrivera / senior` | Works the manual-review queue; gets the biggest / highest-authority cases |
| **Mid-tier underwriter** | `ewong / review` | Same, mid-tier cases |
| **New analyst** | `dpark / analyst` | Same, but only lower-coverage cases (authority limit) |
| **Manager** | `nsethi / oversight` | Portfolio & Model Card, oversight dashboard, and can **reopen/override** any decision |
| **Executive (CUO)** | `mvale / executive` | Money view only — coverage accepted/declined, YoY, appetite. No individual cases |
| **Operations admin** | `panand / admin` | Every recorded decision + outstanding evidence requests, for audit/compliance |

> The **light/dark toggle** is the ☀️/🌙 button top-right — flip it once for effect.

---

## 7. The underwriter's day (the core workflow to walk through)

1. **Sign in as `mrivera / senior`.** You land on the **Review Queue** — only the yellow-band
   cases (the ones needing a human). Auto-approvals and auto-declines are filed in separate
   spaces on the left.
2. **The queue is ranked by coverage + time-in-queue, NOT by risk score.** Big, ageing cases
   float to the top. (Why not score? Sorting by the model's opinion would defeat human
   oversight — a $1M case waiting 16 hours matters more than a slightly-riskier $50k one.)
3. **Each row shows an actionable AI recommendation** — "Order APS", "Refer — financial
   underwriting", "Lean approve" — not just a band. The underwriter triages a screen in
   seconds.
4. **Click a case.** The case file leads with the risk score, coverage, and — if there's a
   problem — a **red conflict alert** naming exactly what's wrong (e.g. the two mismatched
   dates of birth). The **Top drivers** card explains the score/decision right under the name.
5. **Tabs:** Application · Documents · Extraction & Conflicts · Risk Score · Decision.
   Documents open inline; you can **request more evidence** (APS, labs, MVR, pharmacy…) with a
   mandatory reason and an AI pre-check that flags duplicate/unnecessary orders.
6. **Decide.** Approve / Decline with a rationale, or send back for more info. Every action is
   logged to the audit trail and the case moves to Completed.
7. **Next ›** button moves through the queue case-by-case without going back.

---

## 8. The 5-minute demo script (follow this live)

1. **(30s) Open live URL.** "This is the sign-in — it's a role selector; the product shows a
   different view to each role." Flip the ☀️/🌙 toggle once.
2. **(90s) Sign in as `mrivera / senior`.** "This is the underwriter's queue — only cases that
   need a human. Notice it's ranked by coverage and how long it's been waiting, and each has
   an AI recommendation." Open the top case. "The score, the coverage, and the AI's suggested
   next step are right up top."
3. **(60s) Show a conflict case.** Open a declined case with a DOB mismatch (search the queue
   or use the Completed/Auto-Declined spaces). "See the red alert — the system caught that the
   birth date on the form doesn't match the medical record. That's flagged as material
   misrepresentation and it's why this was declined, shown right under the name — the
   underwriter doesn't have to hunt for it."
4. **(45s) Request evidence.** On a case, Documents tab → "Request more information" → pick APS
   → "Every request needs a reason, and the AI pre-checks whether it's even necessary before
   it costs $350 and three weeks."
5. **(45s) Sign in as `mvale / executive`.** "The executive never sees individual cases — just
   the money: total coverage accepted vs declined, year-over-year, and how the book is
   tracking against its monthly appetite. No other role has this."
6. **(30s) Sign in as `nsethi / oversight` (manager).** "The manager can reopen or override any
   decision an underwriter made — with a logged reason. And the model card documents exactly
   how the score works and how it performs, for a regulator."
7. **(20s) Close:** "Synthetic data, so every number is verifiable, and the whole thing is one
   self-contained file — no backend needed to run the demo."

---

## 9. Questions you'll get (and good answers)

- **"Is it fully automated / does AI decide?"** No — and that's deliberate. The AI
  auto-decides only the clear-cut cases; every borderline case keeps a human. That's the
  regulator-preferred "human-in-the-loop" model.
- **"How do you know the model is accurate?"** The data is synthetic with known answers, so we
  measure it directly — ~89% AUC. In production you'd validate on the carrier's real book.
- **"Where do the risk weights come from — did you just pick them?"** No — the medical weights
  are derived from real public mortality data (`points = round(28 × ln(mortality multiple))`)
  and cross-validated. That's on the Model Card.
- **"What about fraud?"** The 6-check conflict screen compares declared values against
  extracted evidence — mismatched DOB, undisclosed smoking, understated income/debt — and
  flags them in red. Material misrepresentation auto-declines.
- **"Is this production-ready?"** It's a **production-grade proof-of-concept**. The scoring,
  governance, and workflow are real; the data is synthetic and state is browser-local. The
  next step is wiring it to a carrier's real data and evidence vendors.
- **"What's EHR vs APS?"** An APS is a manually-compiled physician statement (~$350, weeks).
  An EHR pull is the patient's existing digital record — fast and cheap but less complete.
  Best practice is to tier them, not replace one with the other.

---

## 10. Honest limits (say these — credibility comes from candor)

- **Synthetic data** — proves the pipeline works; not trained on a real book yet.
- **Browser-local state** — decisions/overrides are saved in the browser for the demo, not a
  shared database. The optional API tier makes it shared.
- **No real document extraction** — extraction accuracy is measured on machine-generated PDFs;
  scanned documents would need a production OCR/extraction service.
- **ROI figures are estimates** — the business case depends on a real time study, which we
  flag as the #1 thing to measure.

---

## 11. The tech, in one breath

Python pipeline (rule engine + logistic regression + gradient boosting, evidence-anchored
weights) → JSON → a single self-contained HTML/JS workbench, deployed as a static file on
Cloudflare Pages. The browser re-scores new applications with a hand-port of the same engine,
so it runs with no backend. A shared "verify" test guarantees the browser and the pipeline
always agree.

---

*For the exact decision logic in one page, see `DECISION_PROCESS.md` / `.pdf`. For the full
product roadmap and requirements, see `PRD.md`.*
