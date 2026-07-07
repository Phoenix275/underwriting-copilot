"""engine.py — Conflict detection, dual risk engine, decision logic."""
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
]

def detect_conflicts(rec):
    found = []
    for name, severity, fn, desc in CHECKS:
        try:
            if fn(rec):
                found.append({"type": name, "severity": severity, "description": desc})
        except Exception:
            pass
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
    total = min(sum(f[2] for f in factors), 100)
    return total, factors

def tier(score):
    return "low" if score <= 25 else "moderate" if score <= 50 else "elevated" if score <= 70 else "high"

# ---------------- ML engine --------------------------------------------------------
FEATURES = ["Age", "BMI", "smoker_now", "smoker_former", "n_conditions",
            "Family History Flag", "Debt-to-Income Ratio", "Credit Score"]

def featurize(df):
    X = pd.DataFrame({
        "Age": df["Age"], "BMI": df["BMI"],
        "smoker_now": (df["Smoker Status"] == "Smoker").astype(int),
        "smoker_former": (df["Smoker Status"] == "Former smoker").astype(int),
        "n_conditions": df["Existing Conditions"].apply(lambda s: 0 if s == "None" else len(s.split(","))),
        "Family History Flag": df["Family History Flag"],
        "Debt-to-Income Ratio": df["Debt-to-Income Ratio"].clip(0, 3),
        "Credit Score": df["Credit Score"],
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

    report = {
        "n_train": len(Xtr), "n_test": len(Xte), "positive_rate": round(float(y.mean()), 3),
        "logistic_regression": metrics(lr, scaler.transform(Xte)),
        "gradient_boosting": metrics(gb, Xte),
        "gb_feature_importance": dict(zip(FEATURES, [round(float(v), 4) for v in gb.feature_importances_])),
        "lr_coefficients": dict(zip(FEATURES, [round(float(v), 4) for v in lr.coef_[0]])),
    }
    return {"lr": lr, "gb": gb, "scaler": scaler}, report

def ml_scores(models, df):
    X = featurize(df)
    lr_p = models["lr"].predict_proba(models["scaler"].transform(X))[:, 1]
    gb_p = models["gb"].predict_proba(X)[:, 1]
    return (lr_p * 100).round(1), (gb_p * 100).round(1)

# ---------------- decision logic ---------------------------------------------------
TIER_META = {
    "low":      ("APPROVED", "Preferred Rate Class"),
    "moderate": ("APPROVED", "Standard Rate Class"),
    "elevated": ("REFERRED", "Substandard — Senior Underwriter Review"),
    "high":     ("REFER — APS REQUIRED", "Rated / Decline Pending Evidence"),
}

def decide(rule_s, ml_s, conflicts):
    t_rule, t_ml = tier(rule_s), tier(ml_s)
    reasons = []
    majors = [c for c in conflicts if c["severity"] == "major"]
    final_tier = t_ml
    decision, rate = TIER_META[final_tier]
    if majors:
        decision, rate = "REFERRED", "Manual Review — Data Conflict"
        reasons.append(f"{len(majors)} major data conflict(s): " + "; ".join(c["type"] for c in majors))
    if t_rule != t_ml and abs(rule_s - ml_s) > 20 and decision.startswith("APPROVED"):
        decision, rate = "REFERRED", "Manual Review — Model Disagreement"
        reasons.append(f"Rule tier '{t_rule}' vs ML tier '{t_ml}' disagree materially")
    if not reasons:
        reasons.append(f"Rule and ML tiers consistent ({t_ml}); no major conflicts detected")
    return {"decision": decision, "rate_class": rate, "tier": final_tier, "reasons": reasons,
            "referred": not decision.startswith("APPROVED")}
