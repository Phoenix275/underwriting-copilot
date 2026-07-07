# AI-Powered Financial Viability Assessment Copilot
## 4-Week Execution Plan — Tech Mahindra GLP Internship (Jul 3 – Jul 31, 2026)

**Managers:** Rashmi Kubusada (primary) · Vasu Bheema Rao
**Cadence:** Progress presentation every Friday · Buddy sync 2×/week · Business Leader check-in fortnightly

---

## How the four weeks fit together

Each week ends with a Friday presentation and maps to one stage of the underwriting pipeline you defined in the brainstorming notes:

| Week | Theme | Pipeline stage covered | Friday deliverable |
|---|---|---|---|
| 1 (Jul 6–10) | Understand the problem | Framing, prior art, viability | Storyboard presentation |
| 2 (Jul 13–17) | Documents in, data out | Step 1 → Step 2 (input + extraction) | Working extraction demo with accuracy numbers |
| 3 (Jul 20–24) | Risk engine | Step 3 → Step 4 (assessment + evaluation) | Scoring engine demo: rule weightage + ML + conflict flags |
| 4 (Jul 27–31) | Decision support & final demo | Step 5 + AI output layer | End-to-end prototype demo + final presentation |

The guiding thread: by Week 4, a synthetic PDF application packet goes in one end and an underwriter-ready decision (summary, recommendation, accept/decline/refer with reasons) comes out the other — with **measurable parameters at every stage** (extraction accuracy, model AUC/precision/recall, conflict-detection hit rate) so nothing rests on vibes.

---

## Week 1 — Understanding the Problem (Jul 6–10)

**Goal:** Nail the "why" before the "how." Produce the storyboard: what underwriting is, why it's slow/inconsistent today, what's been done before, why this approach is viable, and what we'll build.

**Mon Jul 6 — Domain immersion.** Learn the life insurance underwriting process end to end: what an underwriter actually reviews (application form, paramedical exam, financial docs), what rate classes are (Preferred / Standard / Substandard / Decline), what "refer" and "APS" (Attending Physician Statement) mean. Write a one-page plain-English explanation of the 5-step workflow. List questions for Rashmi/Vasu — they have 36+ combined years in this domain; use them.

**Tue Jul 7 — Problem definition & pain points.** Document why manual underwriting is a problem worth solving: turnaround time, inconsistency between underwriters, subjective interpretation, cost per case. Find 3–5 concrete industry stats to cite (e.g., average days-to-decision for fully underwritten life policies, straight-through-processing rates). Draft the "why should we do this" section of the storyboard.

**Wed Jul 8 — Prior art & landscape.** Research what already exists: accelerated underwriting programs (John Hancock, Haven Life), vendor platforms (Swiss Re Magnum, Munich Re ALLFINANZ — note Vasu delivered for Munich Re, ask him), and how LLMs/Document AI are changing it. Identify the gap our copilot fills: explainable AI-assisted decision support, not a black-box replacement. Also cover the risks honestly — bias, regulation, explainability requirements — because the managers will ask.

**Thu Jul 9 — Solution storyboard + architecture sketch.** Draw the target architecture: PDF packet → Document AI extraction → structured record → risk weightage engine + ML model → decision + AI summary. Map each stage to a measurable parameter (this answers brainstorming note #4). Show the existing case-review prototype as proof-of-concept for stages 2–5, and frame Week 2's document-extraction work as the missing front end. Build the Friday deck.

**Fri Jul 10 — Presentation #1: Storyboard.** Present: problem → why it matters → what exists → our approach → 4-week plan → measurable success criteria. Dry-run in the morning, present, then capture manager feedback and adjust the Week 2–4 plan accordingly.

---

## Week 2 — Synthetic Documents & Data Extraction (Jul 13–17)

**Goal:** Close the biggest gap vs. the project spec: the pipeline currently starts from clean Excel; the spec starts from PDFs. Generate synthetic application documents, extract them back to structured data, and measure how well extraction works.

**Mon Jul 13 — Synthetic document generation, part 1.** Write a Python generator that turns each row of the Life Insurance Sample Dataset into a realistic PDF application form (ACORD-style layout). Since we generated the documents from known ground truth, extraction accuracy becomes exactly measurable — that's the trick that makes note #4 achievable.

**Tue Jul 14 — Synthetic document generation, part 2.** Extend the generator to supporting documents: payslip, 3-month bank statement summary, and a simple tax document per applicant, driven by the Financial Viability sheet. Deliberately inject a controlled percentage of conflicts (e.g., payslip income ≠ declared income, DOB mismatch between form and ID) so conflict detection can be tested later. Scale the dataset beyond 25 applicants if time allows.

**Wed Jul 15 — Extraction pipeline, part 1.** Set up Google Document AI (or OCR + Gemini structured extraction as fallback) on GCP. Extract fields from the application form PDFs into a defined JSON schema. Store results (BigQuery or SQL per the spec's tool list).

**Thu Jul 16 — Extraction pipeline, part 2 + measurement.** Extend extraction to the supporting docs. Build the accuracy harness: field-level precision/recall against ground truth, per-field error rates, and a cross-document consistency check (does payslip income match declared income?). This produces the first hard numbers of the project.

**Fri Jul 17 — Presentation #2: Extraction demo.** Show: PDF in → structured JSON out, with an accuracy table (e.g., "94% field-level accuracy across 200 documents; income fields hardest") and first conflict-detection results. State what Week 3 will do with the extracted data.

---

## Week 3 — Risk Assessment & Evaluation Engine (Jul 20–24)

**Goal:** Turn extracted data into a defensible risk score. Formalize the risk-weightage scheme from the notes (DOB low weight, lifestyle high weight), harden the ML model, and make conflicting data a first-class signal.

**Mon Jul 20 — Risk weightage design.** Take the rule engine already in the prototype and formalize it with the managers' input: which factors, what point weights, what tier thresholds. Document the rationale per factor — this is the "explainable" half of the system and the part insurance stakeholders will scrutinize. Validate weights against how real underwriting manuals treat each factor.

**Tue Jul 21 — ML model iteration.** Retrain on the expanded synthetic dataset. Try beyond logistic regression (gradient boosting) and compare AUC/precision/recall honestly. Keep the current side-by-side design — auditable rule score next to ML score — it's a genuinely good pattern for regulated domains. Add calibration so the score reads as a real probability.

**Wed Jul 22 — Conflict scoping & equal screening.** Build the "screen everything equally" layer from note #4: every applicant passes through the identical checklist; every discrepancy found in Week 2's consistency checks gets logged with severity and routed (minor → note on file, major → automatic Refer). Measure detection rate against the conflicts we deliberately injected.

**Thu Jul 23 — Decision logic + evaluation run.** Wire scores + conflicts into the 5-step decision output: Accept (preferred/standard), Refer (with named manual checkpoint and reason), Decline-pending-evidence. Run the full batch of synthetic applicants through and produce the evaluation report: tier distribution, agreement rate between rule and ML scores, conflict catch rate, and cases where the two disagree (the interesting ones).

**Fri Jul 24 — Presentation #3: Risk engine demo.** Walk one clean case and one conflict-laden case through assessment live. Present the metrics dashboard. Confirm scope for the final week with managers — this is the last chance to cut scope safely.

---

## Week 4 — Decision Support, Integration & Final Demo (Jul 27–31)

**Goal:** Assemble everything into the end-to-end copilot, add the AI narrative layer, evaluate, polish, and land the final presentation.

**Mon Jul 27 — AI output layer.** Build the four-part AI output from the notes: (1) case summary, (2) recommendation, (3) accept/decline with explicit reasons tied to factors, (4) refer with named manual checkpoint. Ground every generated sentence in extracted fields only — no invented numbers (the prototype's prompt already does this well; extend it). Add a groundedness spot-check: sample summaries, verify every claim traces to a source field.

**Tue Jul 28 — End-to-end integration.** Connect the chain: upload PDF packet → extraction → risk engine → decision → AI summary, in one interface (extend the existing case-review dashboard). Handle failure modes gracefully (unreadable document → flag for manual entry, not silent zeros).

**Wed Jul 29 — Full evaluation + buffer.** Run the complete pipeline on the full synthetic portfolio. Compile the final metrics story: extraction accuracy → conflict detection rate → model performance → end-to-end straight-through-processing rate. This day doubles as slack for anything that slipped.

**Thu Jul 30 — Final presentation build + dry run.** Deck structure: recap the Week 1 storyboard → what was built each week → live demo → metrics → limitations (synthetic data, prototype-stage model, regulatory considerations) → what a production roadmap would look like. Dry-run with buddy; incorporate feedback.

**Fri Jul 31 — Presentation #4: Final demo.** Deliver the working prototype demo and final presentation to managers and business leader. Hand over: code repo, documentation, evaluation report, and the roadmap slide.

---

## Measurable parameters (running list — brainstorming note #4)

| Stage | Metric | Target/baseline |
|---|---|---|
| Extraction | Field-level accuracy vs. ground truth | Establish Week 2; aim >90% |
| Extraction | Per-document-type error rate | Tracked per doc type |
| Conflict screening | Injected-conflict detection rate | Aim >95% on major conflicts |
| Conflict screening | False-positive conflict rate | Keep low enough to avoid alert fatigue |
| Risk model | AUC / precision / recall on held-out set | Current baseline: AUC 0.750 |
| Risk model | Rule-vs-ML tier agreement rate | Track; disagreements auto-flag for review |
| Decision | Straight-through-processing rate | % of cases decided without referral |
| AI summary | Groundedness (claims traceable to source fields) | Spot-check sample, aim 100% |

## Week 1 storyboard skeleton (Friday Jul 10 deck)

1. **The problem** — what life insurance underwriting is, the 5-step process, and where it hurts today (time, inconsistency, subjectivity, cost).
2. **Why now** — Document AI + LLMs make step 1→2 (documents → data) automatable in a way it wasn't three years ago.
3. **What exists** — accelerated underwriting programs and vendor rule engines; the gap: explainable, document-grounded AI decision *support* (copilot, not autopilot).
4. **Our approach** — pipeline diagram: PDF packet → extraction → weighted risk assessment (rule + ML side by side) → decision → grounded AI narrative. Show the current prototype as early proof of stages 2–5.
5. **How we'll know it works** — the measurable-parameters table above.
6. **Risks & honesty slide** — synthetic data limits, bias/fairness, explainability and regulatory context.
7. **The 4-week plan** — the week-by-week table from this document.
