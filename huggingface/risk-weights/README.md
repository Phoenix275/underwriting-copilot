---
license: mit
language:
  - en
pretty_name: Underwriting Copilot — Evidence-Anchored Mortality Risk Weights
tags:
  - insurance
  - underwriting
  - mortality
  - actuarial
  - health
size_categories:
  - n<1K
configs:
  - config_name: factor_weights
    data_files: risk_weights.csv
  - config_name: banded_lookups
    data_files: banded_lookups.csv
---

# Evidence-Anchored Mortality Risk Weights

The risk-scoring weights used by the **Underwriting Copilot** — a life-insurance
financial-viability workbench. Every weight is anchored to a real, cited
relative-mortality multiple. **No point value is a guess.**

- **Live app:** https://underwriting-copilot.pages.dev
- **Source code:** https://github.com/Phoenix275/underwriting-copilot
- Generated from [`src/calibration.py`](https://github.com/Phoenix275/underwriting-copilot/blob/main/src/calibration.py); reproduce the fit with `scripts/derive_weights.py`.

## Method

Mortality risk is multiplicative, so weights are additive in log space:

```
points = round(POINT_SCALE × ln(relative_mortality_multiple))     # POINT_SCALE = 28
```

`POINT_SCALE` is set so a current smoker (~2.4× mortality) earns ~24 points — the
conventional heavy debit — and every other factor scales from the same ruler. The
**ratios** between the points therefore reproduce the **ratios** between real
mortality multiples, instead of being hand-picked.

## Files

### `risk_weights.csv` — per-factor weights
| column | meaning |
|---|---|
| `factor` | risk factor key used by the engine |
| `relative_mortality_multiple` | all-cause relative mortality vs a comparable non-exposed adult |
| `points` | `round(28 × ln(multiple))` — the debit added to the 0–100 risk score |
| `source` | evidence tag (see below) |
| `note` | provenance / caveat |

### `banded_lookups.csv` — age & BMI banding
Age is the dominant factor and is read in bands anchored to the NHANES slope
(~2.84× all-cause mortality per decade — mortality roughly doubles every ~8 years,
the Gompertz law). BMI is banded from the same multiples.

## Evidence sources

| tag | source |
|---|---|
| **NHANES** | Our own age/sex-adjusted logistic fit on **20,435 real US adults with 2,293 linked deaths** — NHANES 2007–2014 exam/lab files joined to the NCHS Linked Mortality File. Smoking = serum-cotinine-confirmed; diabetes = HbA1c ≥ 6.5%. |
| **ERFC** | Emerging Risk Factors Collaboration, NEJM 2011 — diabetes, 820k people |
| **PSC** | Prospective Studies Collaboration, Lancet 2009 — BMI, 900k adults |
| **NHIS** | US NHIS Linked Mortality, Am J Prev Med 2018 — smoking 2.2–2.3× |
| **FHS** | D'Agostino Framingham general-CVD, Circulation 2008 |

Where our own NHANES fit and the large published cohort disagree, the more
conservative published value is used and flagged (e.g. BMI: NHANES 9-year
follow-up shows the short-horizon "obesity paradox", so obesity is anchored to
PSC's long-horizon +30%/5-units instead of our attenuated estimate).

## Validation

The rebased weights were cross-checked against **real applicant underwriting
ratings** (Kaggle Prudential Life Insurance Assessment): a logistic model using
only these weights separates the "standard-or-better vs rated" label at
**AUC ≈ 0.68–0.72** on held-out applicants — in line with what published
mortality-only models achieve, and honest about the ceiling of a risk-only score.

## Intended use & limits

Built for the **Tech Mahindra Global Learning Program internship (Finance
Project 1)** as a defensible prototype. It is **not** medical advice, **not** an
approved actuarial basis, and **not** affiliated with any insurer. Use it to
understand how transparent, source-cited underwriting weights can be constructed —
not to price real policies.

## Citation

```bibtex
@misc{underwriting_copilot_risk_weights,
  title  = {Evidence-Anchored Mortality Risk Weights (Underwriting Copilot)},
  author = {Bindra, Tegh},
  year   = {2026},
  url    = {https://github.com/Phoenix275/underwriting-copilot}
}
```
