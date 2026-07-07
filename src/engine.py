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
    hazard = a.get("Hazardous Activities", "None") if hasattr(a, "get") else a["Hazardous Activities"]
    p = 10 if hazard != "None" else 0
    factors.append(("Hazardous activities", hazard if p else "None disclosed", p))
    viol = int(a["Driving Violations (3yr)"])
    p = 0 if viol == 0 else 4 if viol <= 2 else 10
    factors.append(("Driving record", f"{viol} violation(s) in 3 years", p))
    alcohol = a["Alcohol Use"]
    p = 12 if alcohol == "Heavy" else 2 if alcohol == "Moderate" else 0
    factors.append(("Alcohol use", alcohol, p))
    total = min(sum(f[2] for f in factors), 100)
    return total, factors

def tier(score):
    return "low" if score <= 25 else "moderate" if score <= 50 else "elevated" if score <= 70 else "high"

# ---------------- ML engine --------------------------------------------------------
FEATURES = ["Age", "BMI", "smoker_now", "smoker_former", "n_conditions",
            "Family History Flag", "Debt-to-Income Ratio", "Credit Score",
            "hazardous_activity", "driving_violations", "alcohol_heavy",
            "external_prior"]

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
        # blended event probability learned from 11 public real-world datasets
        "external_prior": df["External Risk Prior"] if "External Risk Prior" in df else 0.5,
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
APPROVE_LINE = 40   # composite below this (with clean signals) auto-approves
DECLINE_LINE = 70   # composite at/above this declines

MISREP_TYPES = {"smoker_nondisclosure", "dob_mismatch"}

def decide(rule_s, ml_s, conflicts, unique=None):
    composite = int(round(0.5 * rule_s + 0.5 * ml_s))
    majors = [c for c in conflicts if c["severity"] == "major"]
    misrep = [c for c in majors if c["type"] in MISREP_TYPES]
    reasons = []
    if misrep:
        verdict, decision = "red", "DECLINE"
        rate = "Declined — Material Misrepresentation"
        reasons.append("Application contradicts medical/identity evidence: "
                       + "; ".join(c["type"].replace("_", " ") for c in misrep))
    elif composite >= DECLINE_LINE:
        verdict, decision = "red", "DECLINE"
        rate = "Declined — Risk Exceeds Appetite"
        reasons.append(f"Composite risk score {composite}/100 is in the {DECLINE_LINE}+ decline band")
    elif majors or unique or composite >= APPROVE_LINE or abs(rule_s - ml_s) > 20:
        verdict, decision = "yellow", "MANUAL REVIEW"
        rate = "Referred — Senior Underwriter Review"
        if majors:
            reasons.append(f"{len(majors)} major data conflict(s): " + "; ".join(c["type"] for c in majors))
        if unique:
            rate = "Referred — Unique Circumstances Disclosed"
            reasons.append(f"Applicant disclosed unique circumstances: {unique}")
        if composite >= APPROVE_LINE:
            reasons.append(f"Composite score {composite} sits in the {APPROVE_LINE}–{DECLINE_LINE - 1} referral band")
        if abs(rule_s - ml_s) > 20:
            reasons.append(f"Rule engine ({rule_s}) and ML model ({ml_s:.0f}) disagree materially")
    else:
        verdict, decision = "green", "APPROVE"
        rate = "Preferred Rate Class" if composite <= 25 else "Standard Rate Class"
        reasons.append(f"Composite score {composite} is below the {APPROVE_LINE}-point approval line; "
                       f"engines agree and no conflicts or special circumstances were found")
    return {"decision": decision, "rate_class": rate, "verdict": verdict, "risk_score": composite,
            "tier": tier(composite), "reasons": reasons, "referred": verdict != "green"}
