# How the Copilot Decides: Approve, Manual Review, or Decline

A quick reference for how every case lands in a bucket.

## 1. The score

Every applicant gets one **Composite Risk Score (0–100)**:

```
Composite Score = 50% × Rule Engine score + 50% × ML model score
```

- **Rule engine** — a fully auditable, hand-documented checklist (age, tobacco, BMI, medical
  conditions, credit, driving record, etc.). Every point traces to a written weight.
- **ML model** — a gradient-boosting model trained on historical outcomes. It catches
  interactions between factors the rules can't (e.g. "smoker + high BMI + young age" behaving
  differently than any one factor alone).

Blending them means one bad model can never single-handedly approve a risky case, and the
rules alone can never miss a pattern the data has learned.

## 2. The score sets the band — nothing else

| Score | Band | Outcome |
|---|---|---|
| **0–50** | 🟢 Green | **APPROVE** — straight-through, no human touch |
| **51–89** | 🟡 Yellow | **MANUAL REVIEW** — a human underwriter decides |
| **90–100** | 🔴 Red | **DECLINE** — risk exceeds appetite |

The band is **score-driven only**. A 22 is always green; a 95 is always red — regardless of
anything else on the file. This is deliberate: it keeps the line defensible and auditable
("why was this declined?" always has the same one-line answer — the score).

## 3. The one exception: material misrepresentation

If the application **contradicts the medical or identity evidence** (e.g. the applicant said
non-smoker but the lab came back positive, or the DOB doesn't match records), the case is
**declined regardless of score**. This isn't a risk judgment — it's fraud/integrity, and it
overrides everything else.

## 4. Flags: informative, not decisive

These show up on the case as **flags for the reviewer** — they explain context, but they do
**not** move the case between bands:

- A major cross-document conflict (non-fraud)
- The affordability screen failing (can't justify the coverage on the applicant's income)
- The applicant disclosing unique circumstances
- The rule engine and ML model disagreeing sharply

A 40-score case with a affordability flag is still **green/APPROVE** — the flag just tells the
underwriter (or whoever opens the file later) that something's worth a second look, without
silently re-routing a clean-scoring case into someone's queue.

## 5. Who sees what

| Role | View |
|---|---|
| **Underwriter** | Works the manual-review queue only — the yellow-band cases, ranked by coverage + time waiting, not by score |
| **Manager** | Portfolio & Model Card — the score bands, formula, and full case list |
| **Executive** | Aggregate money view — coverage accepted/declined, approval rate, appetite tracking. No individual cases |
| **Admin** | Every recorded decision + outstanding evidence requests, for audit/compliance |

## 6. Why underwriters don't rank by risk score

The manual-review queue is sorted by **coverage size + how long it's been waiting**, not by
score. Sorting by score would mean the model's opinion decides who gets looked at first —
which defeats the point of human oversight. A $1M case sitting for 16 hours jumps the queue
ahead of a $50k case that just arrived, even if the $50k case scores higher.
