"""run_pipeline.py — End-to-end MVP pipeline.

  1. Generate N synthetic applicants (datagen)
  2. Train dual risk models on train split (engine)
  3. Generate PDF packets for a doc subset, with injected conflicts (docgen)
  4. Extract every packet (extract) and measure field-level accuracy
  5. Detect conflicts and measure detection vs injected ground truth
  6. Decide every case; compute STP rate
  7. Emit evaluation_report.json + portfolio.json (for the dashboard)
"""
import json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import datagen, docgen, engine
from extract import LocalTextExtractor

OUT = os.path.join(os.path.dirname(__file__), "..", "output")
DOCS = os.path.join(OUT, "packets")

N_APPLICANTS = int(os.environ.get("N_APPLICANTS", 4000))
N_PACKETS = int(os.environ.get("N_PACKETS", 60))
CONFLICT_RATE = 0.30

# comparable fields for extraction accuracy (extracted vs printed ground truth)
ACC_FIELDS = ["name", "form_dob", "paramed_dob", "form_income", "payslip_income",
              "form_debt", "bureau_debt", "form_tobacco_yes", "cotinine"]

def field_match(fname, ext, truth):
    if ext is None: return False
    if isinstance(truth, float):
        try: return abs(float(ext) - truth) < 0.51
        except (TypeError, ValueError): return False
    if fname == "cotinine":
        return str(ext).upper() == str(truth).upper()
    return str(ext).strip() == str(truth).strip()

def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)

    print(f"[1/6] generating {N_APPLICANTS} synthetic applicants…")
    df = datagen.generate(N_APPLICANTS)
    df.to_csv(os.path.join(OUT, "applicants.csv"), index=False)

    print("[2/6] training risk models (logistic regression + gradient boosting)…")
    models, model_report = engine.train_models(df)
    lr_scores, gb_scores = engine.ml_scores(models, df)
    df["ml_score_lr"], df["ml_score_gb"] = lr_scores, gb_scores

    print(f"[3/6] generating {N_PACKETS} PDF packets (conflict rate {CONFLICT_RATE:.0%})…")
    doc_df = df.head(N_PACKETS)
    truth = docgen.generate_packets(doc_df, DOCS, conflict_rate=CONFLICT_RATE)

    print("[4/6] extracting all packets + measuring accuracy…")
    ex = LocalTextExtractor()
    extractions, correct, total = {}, 0, 0
    per_field = {f: [0, 0] for f in ACC_FIELDS}
    for aid in doc_df["Applicant ID"]:
        rec = ex.extract_packet(os.path.join(DOCS, aid))
        extractions[aid] = rec
        for f in ACC_FIELDS:
            ok = field_match(f, rec.get(f), truth[aid]["printed"][f])
            per_field[f][0] += int(ok); per_field[f][1] += 1
            correct += int(ok); total += 1
    extraction_accuracy = correct / total

    print("[5/6] conflict detection + decisions…")
    tp = fp = fn = 0
    portfolio = []
    for _, a in df.iterrows():
        aid = a["Applicant ID"]
        rule_s, factors = engine.rule_score(a)
        ml_s = float(a["ml_score_gb"])
        if aid in extractions:
            conflicts = engine.detect_conflicts(extractions[aid])
            inj = set(truth[aid]["injected_conflicts"])
            det = set(c["type"] for c in conflicts)
            tp += len(inj & det); fp += len(det - inj); fn += len(inj - det)
        else:
            conflicts = []
        unique = None if a["Unique Circumstances"] == "None" else a["Unique Circumstances"]
        d = engine.decide(rule_s, ml_s, conflicts, unique=unique)
        portfolio.append({
            "id": aid, "name": a["Full Name"], "age": int(a["Age"]), "dob": a["Date of Birth"],
            "city": a["City"], "state": a["State"], "occupation": a["Occupation"], "employer": a["Employer"],
            "income": float(a["Annual Income (USD)"]), "policy": a["Policy Type Requested"],
            "coverage": float(a["Coverage Amount Requested (USD)"]),
            "height": int(a["Height (cm)"]), "weight": float(a["Weight (kg)"]), "bmi": float(a["BMI"]),
            "smoker": a["Smoker Status"], "conditions": a["Existing Conditions"],
            "family": int(a["Family History Flag"]), "bp": a["Blood Pressure"],
            "chol": int(a["Cholesterol (mg/dL)"]), "debt": float(a["Existing Debt (USD)"]),
            "expenses": float(a["Monthly Expenses (USD)"]), "bank": float(a["Avg Bank Balance (USD)"]),
            "emp_status": a["Employment Status"], "years_emp": int(a["Years Employed"]),
            "hazard": a["Hazardous Activities"], "violations": int(a["Driving Violations (3yr)"]),
            "alcohol": a["Alcohol Use"], "unique": unique,
            "credit": int(a["Credit Score"]), "dti": float(a["Debt-to-Income Ratio"]),
            "label": int(a["High Risk Label"]),
            "rule_score": rule_s, "rule_factors": factors, "ml_score": ml_s,
            "ml_score_lr": float(a["ml_score_lr"]),
            "has_docs": aid in extractions,
            "extraction": extractions.get(aid), "conflicts": conflicts,
            "injected": truth.get(aid, {}).get("injected_conflicts", []),
            **d,
        })

    stp = sum(1 for p in portfolio if not p["referred"]) / len(portfolio)
    conflict_recall = tp / max(tp + fn, 1)
    conflict_precision = tp / max(tp + fp, 1)
    agreement = np.mean([engine.tier(p["rule_score"]) == engine.tier(p["ml_score"]) for p in portfolio])

    print("[6/6] writing reports…")
    report = {
        "generated_at": "2026-07-07", "n_applicants": len(df), "n_packets": N_PACKETS,
        "extraction": {"field_level_accuracy": round(extraction_accuracy, 4),
                        "per_field": {f: round(c / t, 4) for f, (c, t) in per_field.items()}},
        "conflict_screening": {"injected_rate": CONFLICT_RATE,
                                "detection_recall": round(conflict_recall, 4),
                                "detection_precision": round(conflict_precision, 4),
                                "tp": tp, "fp": fp, "fn": fn},
        "risk_models": model_report,
        "decisioning": {"straight_through_rate": round(stp, 4),
                         "rule_ml_tier_agreement": round(float(agreement), 4)},
    }
    with open(os.path.join(OUT, "evaluation_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    # dashboard payload: all doc-backed cases + sample of the rest + metrics
    dash_cases = [p for p in portfolio if p["has_docs"]] + \
                 [p for p in portfolio if not p["has_docs"]][:140]
    with open(os.path.join(OUT, "portfolio.json"), "w") as f:
        json.dump({"metrics": report, "cases": dash_cases}, f)

    print(json.dumps(report, indent=2))
    print(f"done in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
