"""engine.py — Conflict detection, dual risk engine, affordability, decision logic."""
import math
import warnings
import numpy as np
import pandas as pd

# ---------------- conflict detection (equal screening: every packet, same checks) --
CHECKS = [
    ("income_mismatch", "major",
     lambda r: r.get("form_income") and r.get("payslip_income")
               and abs(r["form_income"] - r["payslip_income"]) / max(r["payslip_income"], 1) > 0.15,
     "Declared income differs from payslip annualized income by >15%"),
    ("smoker_nondisclosure", "major",
     lambda r: r.get("form_tobacco_yes") is False and (r.get("cotinine") or "").upper() == "POSITIVE",
     "Form declares no tobacco use but paramedical cotinine test is POSITIVE"),
    ("dob_mismatch", "major",
     lambda r: r.get("form_dob") and r.get("paramed_dob") and r["form_dob"] != r["paramed_dob"],
     "Date of birth on application differs from ID recorded at paramedical exam"),
    ("debt_understated", "minor",
     lambda r: r.get("form_debt") is not None and r.get("bureau_debt")
               and r["bureau_debt"] > max(r["form_debt"], 1000) * 1.5,
     "Credit-bureau debt figure exceeds declared debt by >50%"),
    ("income_deposit_mismatch", "major",
     lambda r: r.get("payslip_income") and r.get("bank_deposit_monthly")
               and r["bank_deposit_monthly"] * 12 < r["payslip_income"] * 0.80,
     "Bank-statement deposits run >20% below payslip income — stated income is not evidenced in the account"),
    ("tax_income_mismatch", "major",
     lambda r: r.get("form_income") and r.get("tax_income")
               and r["tax_income"] < r["form_income"] * 0.85,
     "Income reported to the tax authority is >15% below the income declared on the application"),
]

def detect_conflicts(rec):
    found = []
    for name, severity, fn, desc in CHECKS:
        try:
            if fn(rec):
                found.append({"type": name, "severity": severity, "description": desc})
        except Exception as e:
            # a crashing check must never silently pass a packet — surface it
            warnings.warn(f"conflict check '{name}' errored on record "
                          f"{rec.get('name', '?')}: {e}", stacklevel=2)
    return found

# ---------------- rule engine (explainable, weighted per brainstorming notes) ------
def rule_score(a):
    factors = []
    age = a["Age"]; bmi = a["BMI"]; dti = a["Debt-to-Income Ratio"]
    smoker = a["Smoker Status"]; credit = a["Credit Score"]
    conds = [] if a["Existing Conditions"] == "None" else [c.strip() for c in a["Existing Conditions"].split(",")]
    p = 0 if age < 30 else 5 if age <= 45 else 10 if age <= 55 else 18
    factors.append(("Applicant age", f"{age} years", p))
    p = 25 if smoker == "Smoker" else 8 if smoker == "Former smoker" else 0
    factors.append(("Tobacco use", smoker, p))
    p = 15 if (bmi < 18.5 or bmi >= 35) else 8 if bmi >= 30 else 3 if bmi >= 25 else 0
    factors.append(("Body mass index", f"{bmi} BMI", p))
    p = sum(15 if "diabetes" in c.lower() else 8 for c in conds)
    factors.append(("Medical conditions", ", ".join(conds) or "None", p))
    p = 6 if a["Family History Flag"] else 0
    factors.append(("Family medical history", "Notable" if p else "None disclosed", p))
    p = 0 if dti < 0.2 else 5 if dti < 0.35 else 12 if dti < 0.5 else 20
    factors.append(("Debt-to-income ratio", f"{dti*100:.1f}%", p))
    p = 0 if credit > 750 else 3 if credit >= 700 else 8 if credit >= 650 else 15
    factors.append(("Credit score", str(credit), p))
    hazard = a.get("Hazardous Activities", "None") if hasattr(a, "get") else a["Hazardous Activities"]
    p = 10 if hazard != "None" else 0
    factors.append(("Hazardous activities", hazard if p else "None disclosed", p))
    viol = int(a["Driving Violations (3yr)"])
    p = 0 if viol == 0 else 4 if viol <= 2 else 10
    factors.append(("Driving record", f"{viol} violation(s) in 3 years", p))
    alcohol = a["Alcohol Use"]
    p = 12 if alcohol == "Heavy" else 2 if alcohol == "Moderate" else 0
    factors.append(("Alcohol use", alcohol, p))
    # Section 6 personal declarations (per Manulife OTIP application)
    for col, label, pts in [
        ("Prior Application Declined", "Prior insurance declined/modified/rated (Q6-1)", 8),
        ("Dangerous Driving (5yr)", "Careless/dangerous driving or licence suspension (Q6-2a)", 12),
        ("Drug/Alcohol Counselling (5yr)", "Drug use or alcohol/drug counselling (Q6-5a)", 15),
        ("Criminal Record", "Criminal offence charged or convicted (Q6-5b)", 8),
        ("Bankruptcy Declared", "Personal/business bankruptcy (Q6-5c)", 10),
        ("Foreign Travel Planned", "Foreign travel planned, next 12 months (Q6-4a)", 3),
        ("Weight Change 10lb (12mo)", "Weight change >10 lb in past 12 months (Q7)", 4),
    ]:
        flag = int(a[col])
        factors.append((label, "Yes" if flag else "No", pts if flag else 0))
    total = min(sum(f[2] for f in factors), 100)
    return total, factors

def tier(score):
    return "low" if score <= 25 else "moderate" if score <= 50 else "elevated" if score <= 70 else "high"

# ---------------- affordability / financial viability (financial underwriting) -----
# The project brief is an *affordability* copilot: can this applicant sustain the
# premium, and is the requested face amount financially justified? These are the
# standard financial-underwriting screens, separate from mortality risk.

POLICY_PREMIUM_MULT = {"Term Life - 20yr": 1.0, "Term Life - 30yr": 1.45,
                       "Universal Life": 5.0, "Whole Life": 8.5}

def estimate_premium(age, smoker, coverage, policy):
    """Indicative annual premium in USD: rate per $1k of face amount, term-20
    non-smoker baseline, exponential in age, loaded for tobacco and for
    permanent products. Indicative only — a real quote engine replaces this."""
    rate = 0.9 * math.exp(0.045 * (age - 30))
    if smoker == "Smoker":
        rate *= 2.3
    elif smoker == "Former smoker":
        rate *= 1.25
    return round(coverage / 1000.0 * rate * POLICY_PREMIUM_MULT.get(policy, 1.0), 2)

# max justified (coverage + existing) / income multiple by age — standard
# financial-underwriting income-replacement table
COVERAGE_CAPS = [(40, 25), (50, 20), (60, 15), (999, 10)]

NET_INCOME_FACTOR = 0.78   # after-tax take-home approximation
DEBT_SERVICE_RATE = 0.025  # blended monthly payment as a share of debt balance

def affordability_assess(income, monthly_expenses, debt, coverage, existing_cov,
                         age, premium):
    """Four-indicator financial viability screen. Returns verdict
    'pass' (AFFORDABLE) / 'strain' (STRAINED) / 'fail' (NOT JUSTIFIED),
    with every indicator, its benchmark, and plain-English reasons."""
    income = max(float(income), 1.0)
    net_monthly = income * NET_INCOME_FACTOR / 12
    prem_monthly = premium / 12
    pti = premium / income
    disposable = net_monthly - float(monthly_expenses) - prem_monthly
    debt_pay = float(debt) * DEBT_SERVICE_RATE
    dsr = debt_pay / net_monthly
    cap = next(m for a, m in COVERAGE_CAPS if age < a)
    cov_mult = (float(coverage) + float(existing_cov)) / income

    ind, reasons = [], []
    def add(label, value, status, detail):
        ind.append({"label": label, "value": value, "status": status, "detail": detail})
        if status == "fail":
            reasons.append(f"{label}: {detail}")

    s = "pass" if pti <= 0.05 else "strain" if pti <= 0.10 else "fail"
    add("Premium-to-income", f"{pti*100:.1f}%", s,
        f"annual premium {_usd(premium)} is {pti*100:.1f}% of gross income (benchmark ≤5%, strained to 10%)")

    floor = max(0.05 * net_monthly, 150.0)
    s = "fail" if disposable < 0 else "strain" if disposable < floor else "pass"
    add("Disposable income after premium", _usd(disposable) + "/mo", s,
        f"net {_usd(net_monthly)}/mo − expenses {_usd(monthly_expenses)}/mo − premium {_usd(prem_monthly)}/mo "
        f"leaves {_usd(disposable)}/mo (floor {_usd(floor)})")

    s = "pass" if cov_mult <= cap else "strain" if cov_mult <= cap * 1.1 else "fail"
    add("Coverage-to-income multiple", f"{cov_mult:.1f}×", s,
        f"total coverage sought is {cov_mult:.1f}× income against an age-{age} cap of {cap}×")

    s = "pass" if dsr <= 0.20 else "strain" if dsr <= 0.35 else "fail"
    add("Debt-service ratio", f"{dsr*100:.0f}%", s,
        f"estimated debt payments {_usd(debt_pay)}/mo consume {dsr*100:.0f}% of net income (benchmark ≤20%)")

    statuses = [i["status"] for i in ind]
    verdict = "fail" if "fail" in statuses else "strain" if "strain" in statuses else "pass"
    label = {"pass": "AFFORDABLE", "strain": "STRAINED", "fail": "NOT JUSTIFIED"}[verdict]
    if verdict == "strain":
        reasons.append("Affordability indicators are within tolerance but strained: "
                       + "; ".join(i["label"] for i in ind if i["status"] == "strain"))
    return {"verdict": verdict, "label": label, "premium": round(premium, 2),
            "premium_monthly": round(prem_monthly, 2), "pti": round(pti, 4),
            "disposable": round(disposable, 2), "cov_mult": round(cov_mult, 2),
            "cov_cap": cap, "dsr": round(dsr, 4), "indicators": ind, "reasons": reasons}

def _usd(n):
    return "$" + format(int(round(float(n))), ",")

def afford_from_row(a):
    """Affordability assessment straight from an applicant row."""
    premium = estimate_premium(int(a["Age"]), a["Smoker Status"],
                               float(a["Coverage Amount Requested (USD)"]),
                               a["Policy Type Requested"])
    return affordability_assess(a["Annual Income (USD)"], a["Monthly Expenses (USD)"],
                                a["Existing Debt (USD)"], a["Coverage Amount Requested (USD)"],
                                a.get("Existing Coverage (USD)", 0) if hasattr(a, "get") else a["Existing Coverage (USD)"],
                                int(a["Age"]), premium)

# ---------------- ML engine --------------------------------------------------------
FEATURES = ["Age", "BMI", "smoker_now", "smoker_former", "n_conditions",
            "Family History Flag", "Debt-to-Income Ratio", "Credit Score",
            "hazardous_activity", "driving_violations", "alcohol_heavy",
            "prior_decline", "dangerous_driving", "drug_use", "criminal_record",
            "bankruptcy", "foreign_travel", "weight_change",
            "external_prior", "published_cvd_prior"]

def featurize(df):
    X = pd.DataFrame({
        "Age": df["Age"], "BMI": df["BMI"],
        "smoker_now": (df["Smoker Status"] == "Smoker").astype(int),
        "smoker_former": (df["Smoker Status"] == "Former smoker").astype(int),
        "n_conditions": df["Existing Conditions"].apply(lambda s: 0 if s == "None" else len(s.split(","))),
        "Family History Flag": df["Family History Flag"],
        "Debt-to-Income Ratio": df["Debt-to-Income Ratio"].clip(0, 3),
        "Credit Score": df["Credit Score"],
        "hazardous_activity": (df["Hazardous Activities"] != "None").astype(int),
        "driving_violations": df["Driving Violations (3yr)"],
        "alcohol_heavy": (df["Alcohol Use"] == "Heavy").astype(int),
        "prior_decline": df["Prior Application Declined"].astype(int),
        "dangerous_driving": df["Dangerous Driving (5yr)"].astype(int),
        "drug_use": df["Drug/Alcohol Counselling (5yr)"].astype(int),
        "criminal_record": df["Criminal Record"].astype(int),
        "bankruptcy": df["Bankruptcy Declared"].astype(int),
        "foreign_travel": df["Foreign Travel Planned"].astype(int),
        "weight_change": df["Weight Change 10lb (12mo)"].astype(int),
        # blended event probability learned from public real-world datasets
        "external_prior": df["External Risk Prior"] if "External Risk Prior" in df else 0.5,
        # Framingham office-based general-CVD model (published, zero-training)
        "published_cvd_prior": df["Published CVD Prior"] if "Published CVD Prior" in df else 0.1,
    })
    return X[FEATURES]

def train_models(df, seed=13):
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score

    X, y = featurize(df), df["High Risk Label"].values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=seed, stratify=y)
    scaler = StandardScaler().fit(Xtr)
    lr = LogisticRegression(max_iter=2000).fit(scaler.transform(Xtr), ytr)
    gb = GradientBoostingClassifier(random_state=seed).fit(Xtr, ytr)

    def metrics(model, Xs):
        proba = model.predict_proba(Xs)[:, 1]
        pred = (proba >= 0.5).astype(int)
        return {"auc": round(float(roc_auc_score(yte, proba)), 4),
                "accuracy": round(float(accuracy_score(yte, pred)), 4),
                "precision": round(float(precision_score(yte, pred)), 4),
                "recall": round(float(recall_score(yte, pred)), 4)}

    # calibration: does a predicted risk of X% actually mean X% of those cases are high-risk?
    gb_proba = gb.predict_proba(Xte)[:, 1]
    bins = np.clip((gb_proba * 10).astype(int), 0, 9)
    calibration = []
    for b in range(10):
        mask = bins == b
        if mask.sum() >= 5:
            calibration.append({"bin": f"{b*10}–{b*10+10}%",
                                "predicted": round(float(gb_proba[mask].mean()), 4),
                                "actual": round(float(yte[mask].mean()), 4),
                                "n": int(mask.sum())})

    report = {
        "n_train": len(Xtr), "n_test": len(Xte), "positive_rate": round(float(y.mean()), 3),
        "calibration": calibration,
        "logistic_regression": metrics(lr, scaler.transform(Xte)),
        "gradient_boosting": metrics(gb, Xte),
        "gb_feature_importance": dict(zip(FEATURES, [round(float(v), 4) for v in gb.feature_importances_])),
        "lr_coefficients": dict(zip(FEATURES, [round(float(v), 4) for v in lr.coef_[0]])),
        # exported so the dashboard can score new applications live in the browser
        "lr_export": {"features": FEATURES,
                      "coef": [round(float(v), 6) for v in lr.coef_[0]],
                      "intercept": round(float(lr.intercept_[0]), 6),
                      "scaler_mean": [round(float(v), 6) for v in scaler.mean_],
                      "scaler_std": [round(float(v), 6) for v in scaler.scale_]},
    }
    return {"lr": lr, "gb": gb, "scaler": scaler}, report

def ml_scores(models, df):
    X = featurize(df)
    lr_p = models["lr"].predict_proba(models["scaler"].transform(X))[:, 1]
    gb_p = models["gb"].predict_proba(X)[:, 1]
    return (lr_p * 100).round(1), (gb_p * 100).round(1)

# ---------------- decision logic (three-verdict traffic light) ---------------------
# green  = APPROVE        — clear-cut acceptable risk, auto-approve
# yellow = MANUAL REVIEW  — a human underwriter must look at the whole person
# red    = DECLINE        — application contradicts evidence, or risk clearly exceeds appetite
APPROVE_LINE = 50   # defaults; run_pipeline passes STP-optimised lines instead
DECLINE_LINE = 90

MISREP_TYPES = {"smoker_nondisclosure", "dob_mismatch"}

def decide(rule_s, ml_s, conflicts, unique=None, a_line=APPROVE_LINE, d_line=DECLINE_LINE,
           afford=None):
    composite = int(round(0.5 * rule_s + 0.5 * ml_s))
    majors = [c for c in conflicts if c["severity"] == "major"]
    misrep = [c for c in majors if c["type"] in MISREP_TYPES]
    afford_fail = bool(afford and afford["verdict"] == "fail")
    reasons = []
    if misrep:
        verdict, decision = "red", "DECLINE"
        rate = "Declined — Material Misrepresentation"
        reasons.append("Application contradicts medical/identity evidence: "
                       + "; ".join(c["type"].replace("_", " ") for c in misrep))
    elif composite >= d_line:
        verdict, decision = "red", "DECLINE"
        rate = "Declined — Risk Exceeds Appetite"
        reasons.append(f"Composite risk score {composite}/100 is in the {d_line}+ decline band")
    elif majors or unique or afford_fail or composite >= a_line or abs(rule_s - ml_s) > 20:
        verdict, decision = "yellow", "MANUAL REVIEW"
        rate = "Referred — Senior Underwriter Review"
        if majors:
            reasons.append(f"{len(majors)} major data conflict(s): " + "; ".join(c["type"] for c in majors))
        if unique:
            rate = "Referred — Unique Circumstances Disclosed"
            reasons.append(f"Applicant disclosed unique circumstances: {unique}")
        if afford_fail:
            rate = "Referred — Financial Underwriting Review"
            reasons.extend(afford["reasons"])
        if composite >= a_line:
            reasons.append(f"Composite score {composite} sits in the {a_line}–{d_line - 1} referral band")
        if abs(rule_s - ml_s) > 20:
            reasons.append(f"Rule engine ({rule_s}) and ML model ({ml_s:.0f}) disagree materially")
    else:
        verdict, decision = "green", "APPROVE"
        rate = "Preferred Rate Class" if composite <= 25 else "Standard Rate Class"
        reasons.append(f"Composite score {composite} is below the {a_line}-point approval line; "
                       f"engines agree and no conflicts or special circumstances were found")
        if afford and afford["verdict"] == "strain":
            reasons.append("Affordability is strained but within tolerance — flagged on the financial viability panel")
    # straight-through = any auto decision (approve OR decline); only yellow needs a human
    return {"decision": decision, "rate_class": rate, "verdict": verdict, "risk_score": composite,
            "tier": tier(composite), "reasons": reasons, "referred": verdict == "yellow"}


def _threshold_stats(a, d, comp, y, cl, ceiling):
    appr = cl & (comp < a); decl = comp >= d
    return {"stp_est": round(float((appr.sum() + decl.sum()) / len(comp)), 4),
            "approve_risk_rate": round(float(y[appr].mean()) if appr.sum() else 0.0, 4),
            "decline_precision": round(float(y[decl].mean()) if decl.sum() else 1.0, 4),
            "n_auto_approve": int(appr.sum()), "n_auto_decline": int(decl.sum()),
            "approve_risk_ceiling_used": ceiling}

def _search_thresholds(comp, y, cl, approve_risk_max, decline_prec_min, decline_floor):
    """Grid-search the (approve, decline) lines maximising STP on the given set,
    relaxing the approve-zone risk ceiling in steps if the strict one is infeasible.

    `decline_floor` is how far the auto-decline line may reach down the score:
    the lower it is the more cases decline automatically, so it is the strongest
    lever on STP — held in check by `decline_prec_min`, the precision the
    auto-decline zone must still clear against ground truth."""
    # relax the approve-zone risk ceiling only upward from what was asked, so a
    # deliberately loose setting is never tightened by the fallback ladder
    ladder = sorted({approve_risk_max, approve_risk_max + 0.03,
                     approve_risk_max + 0.06, approve_risk_max + 0.10, 0.15})
    ladder = [r for r in ladder if r >= approve_risk_max]
    for risk_max in ladder:
        best, best_stp = None, -1.0
        for a in range(30, 71):
            appr = cl & (comp < a)
            if appr.sum() and y[appr].mean() > risk_max:
                continue
            for d in range(max(a + 10, decline_floor), 101):
                decl = comp >= d
                if decl.sum() and y[decl].mean() < decline_prec_min:
                    continue
                stp = (appr.sum() + decl.sum()) / len(comp)
                if stp > best_stp:
                    best_stp, best = stp, (a, d, risk_max)
        if best is not None:
            return best
    return (APPROVE_LINE, DECLINE_LINE, None)

def optimize_thresholds(composites, labels, clean, approve_risk_max=0.16,
                        decline_prec_min=0.70, decline_floor=40, seed=13):
    """Pick the approve/decline lines that MAXIMISE straight-through processing,
    subject to safety constraints measured against ground truth:
      - auto-approve zone must contain ≤ approve_risk_max actual high-risk cases
      - auto-decline zone must be ≥ decline_prec_min actual high-risk (precision)
      - the auto-decline line may reach down to `decline_floor`
    `clean` marks cases with no conflicts/disclosures (only those can auto-approve).

    Straight-through processing is the headline operational metric — the share
    of applications decided without a human — so the defaults deliberately trade
    a higher auto-approve risk tolerance and a lower decline floor for more
    automation. Both costs are measured on held-out data and surfaced in the
    model card rather than hidden; nothing here relaxes the conflict, affordability
    or engine-disagreement gates, which still force a referral regardless.

    Leakage control: the grid search runs on a random HALF of the portfolio and
    every reported statistic is computed on the other, held-out half — the STP
    number is out-of-sample, not tuned-on-itself.
    Returns (a_line, d_line, stats).
    """
    comp = np.asarray(composites); y = np.asarray(labels); cl = np.asarray(clean, dtype=bool)
    rng = np.random.default_rng(seed)
    tune = rng.random(len(comp)) < 0.5
    hold = ~tune
    if tune.sum() < 50 or hold.sum() < 50:   # tiny portfolios: no split possible
        a, d, ceiling = _search_thresholds(comp, y, cl, approve_risk_max, decline_prec_min, decline_floor)
        return a, d, {**_threshold_stats(a, d, comp, y, cl, ceiling), "evaluation": "in-sample (n too small to split)"}
    a, d, ceiling = _search_thresholds(comp[tune], y[tune], cl[tune], approve_risk_max, decline_prec_min, decline_floor)
    stats = _threshold_stats(a, d, comp[hold], y[hold], cl[hold], ceiling)
    stats["evaluation"] = f"holdout (tuned on {int(tune.sum())}, evaluated on {int(hold.sum())})"
    return a, d, stats
