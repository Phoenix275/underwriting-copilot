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

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import datagen, docgen, engine, external_data, published_models
from extract import LocalTextExtractor

OUT = os.path.join(os.path.dirname(__file__), "..", "output")
DOCS = os.path.join(OUT, "packets")
DATA = os.path.join(os.path.dirname(__file__), "..", "data")
POOL = os.path.join(DATA, "training_pool.csv")
HISTORY = os.path.join(DATA, "model_history.json")
OVERRIDES = os.path.join(DATA, "overrides.json")

N_APPLICANTS = int(os.environ.get("N_APPLICANTS", 4000))
N_PACKETS = int(os.environ.get("N_PACKETS", 60))
CONFLICT_RATE = 0.30

# comparable fields for extraction accuracy (extracted vs printed ground truth)
ACC_FIELDS = ["name", "form_dob", "paramed_dob", "form_income", "payslip_income",
              "form_debt", "bureau_debt", "form_tobacco_yes", "cotinine",
              "bank_deposit_monthly", "bank_outflow_monthly", "tax_income"]

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
    os.makedirs(DATA, exist_ok=True)
    history = json.load(open(HISTORY)) if os.path.exists(HISTORY) else []
    run_no = len(history) + 1

    print(f"[1/7] learning priors from {len(external_data.REGISTRY)} public real-world datasets…")
    prior_models, ext_report = external_data.load_and_fit()
    usable = [d for d in ext_report if "error" not in d]
    print(f"      {len(usable)}/{len(external_data.REGISTRY)} datasets usable, "
          f"{sum(d['rows'] for d in usable):,} real records")

    print(f"[2/7] generating {N_APPLICANTS} synthetic applicants (run #{run_no}, fresh seed)…")
    df = datagen.generate(N_APPLICANTS, seed=42 + run_no)
    df["External Risk Prior"] = external_data.prior_scores(prior_models, df)
    # already-built, peer-reviewed model used as-is (no training): Framingham office CVD
    df["Published CVD Prior"] = published_models.prior_from_df(df)
    df.to_csv(os.path.join(OUT, "applicants.csv"), index=False)

    # continuous learning: every run adds a fresh batch to a growing training pool
    if os.path.exists(POOL):
        # keep_default_na=False so the literal string "None" (conditions, hazards,
        # unique circumstances) survives the CSV round-trip instead of becoming NaN
        prev = pd.read_csv(POOL, keep_default_na=False, na_values=[])
        if set(df.columns) - set(prev.columns):
            print("      applicant schema changed — starting a fresh training pool")
            pool = df
        else:
            pool = pd.concat([prev, df], ignore_index=True)
    else:
        pool = df
    pool.to_csv(POOL, index=False)

    # underwriter feedback: overrides exported from the dashboard become labeled
    # training rows, so human decisions steer every retrain
    n_overrides = 0
    train_df = pool
    if os.path.exists(OVERRIDES):
        ov = json.load(open(OVERRIDES))
        if ov:
            ov_df = pd.DataFrame([{**o["fields"], "High Risk Label": int(o["label"])} for o in ov])
            train_df = pd.concat([pool, ov_df], ignore_index=True)
            for col, dflt in (("External Risk Prior", 0.5), ("Published CVD Prior", 0.1)):
                if col in train_df:
                    train_df[col] = pd.to_numeric(train_df[col], errors="coerce").fillna(dflt)
            n_overrides = len(ov_df)

    print(f"[3/7] training risk models on pool of {len(train_df):,} records "
          f"({len(pool) - len(df):,} accumulated from previous runs, "
          f"{n_overrides} human underwriter overrides)…")
    models, model_report = engine.train_models(train_df)
    lr_scores, gb_scores = engine.ml_scores(models, df)
    df["ml_score_lr"], df["ml_score_gb"] = lr_scores, gb_scores

    # persist the trained models + dataset prior models for the REST API (src/api.py)
    joblib.dump({"models": models, "prior_models": prior_models, "features": engine.FEATURES},
                os.path.join(OUT, "models.joblib"))

    history.append({"run": run_no, "date": time.strftime("%Y-%m-%d"), "n_train_pool": len(train_df),
                    "n_overrides": n_overrides,
                    "gb_auc": model_report["gradient_boosting"]["auc"],
                    "lr_auc": model_report["logistic_regression"]["auc"],
                    "external_datasets": len(usable),
                    "external_rows": sum(d["rows"] for d in usable)})
    with open(HISTORY, "w") as f:
        json.dump(history, f, indent=2)

    print(f"[4/7] generating {N_PACKETS} PDF packets (conflict rate {CONFLICT_RATE:.0%})…")
    doc_df = df.head(N_PACKETS)
    truth = docgen.generate_packets(doc_df, DOCS, conflict_rate=CONFLICT_RATE)

    print("[5/7] extracting all packets + measuring accuracy…")
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

    print("[6/7] conflict detection + decisions…")
    tp = fp = fn = 0
    # pass 1 — score every applicant, collect conflicts and clean flags
    scored = []
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
        afford = engine.afford_from_row(a)
        clean = not unique and not any(c["severity"] == "major" for c in conflicts) \
                and abs(rule_s - ml_s) <= 20 and afford["verdict"] != "fail"
        scored.append((a, rule_s, factors, ml_s, conflicts, unique, clean, afford))

    # STP optimiser — pick approve/decline lines that maximise straight-through
    # subject to safety constraints checked against ground truth
    composites = [round(0.5 * s[1] + 0.5 * s[3]) for s in scored]
    labels = [int(s[0]["High Risk Label"]) for s in scored]
    cleans = [s[6] for s in scored]
    a_line, d_line, thr_stats = engine.optimize_thresholds(composites, labels, cleans)
    print(f"      STP-optimised thresholds: approve <{a_line} · decline ≥{d_line} "
          f"(est STP {thr_stats['stp_est']:.0%}, approve-zone risk "
          f"{thr_stats['approve_risk_rate']:.1%}, decline precision {thr_stats['decline_precision']:.0%})")

    # pass 2 — decide with the optimised lines
    portfolio = []
    for a, rule_s, factors, ml_s, conflicts, unique, clean, afford in scored:
        aid = a["Applicant ID"]
        d = engine.decide(rule_s, ml_s, conflicts, unique=unique, a_line=a_line, d_line=d_line,
                          afford=afford)
        portfolio.append({
            "id": aid, "name": a["Full Name"], "sex": a["Sex"], "age": int(a["Age"]), "dob": a["Date of Birth"],
            "net_worth": float(a["Net Worth (USD)"]), "existing_cov": float(a["Existing Coverage (USD)"]),
            "replacing": int(a["Replacing Coverage"]),
            "decl": {"prior_decline": int(a["Prior Application Declined"]),
                      "dangerous_driving": int(a["Dangerous Driving (5yr)"]),
                      "foreign_travel": int(a["Foreign Travel Planned"]),
                      "drug_use": int(a["Drug/Alcohol Counselling (5yr)"]),
                      "criminal": int(a["Criminal Record"]),
                      "bankruptcy": int(a["Bankruptcy Declared"]),
                      "weight_change": int(a["Weight Change 10lb (12mo)"])},
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
            "ext_prior": round(float(a["External Risk Prior"]), 4),
            "pub_prior": round(float(a["Published CVD Prior"]), 4),
            "premium": afford["premium"], "afford": afford,
            "credit": int(a["Credit Score"]), "dti": float(a["Debt-to-Income Ratio"]),
            "label": int(a["High Risk Label"]),
            "rule_score": rule_s, "rule_factors": factors, "ml_score": ml_s,
            "ml_score_lr": float(a["ml_score_lr"]),
            "has_docs": aid in extractions,
            "extraction": extractions.get(aid), "conflicts": conflicts,
            "injected": truth.get(aid, {}).get("injected_conflicts", []),
            **d,
        })

    # fairness slices — verdict mix AND model error rates per group.
    # Verdict mix answers "who gets approved"; FPR/FNR answer "who does the
    # model get WRONG" — a group can have a fair outcome mix but bear an
    # unfair share of the errors. Sex is audited because it feeds both priors.
    def fairness_slice(name, grp):
        n = len(grp)
        fp = sum(1 for p in grp if p["ml_score"] >= 50 and p["label"] == 0)
        neg = sum(1 for p in grp if p["label"] == 0)
        fn = sum(1 for p in grp if p["ml_score"] < 50 and p["label"] == 1)
        pos = sum(1 for p in grp if p["label"] == 1)
        return {"band": name, "n": n,
                "green": round(sum(1 for p in grp if p["verdict"] == "green") / n, 3),
                "yellow": round(sum(1 for p in grp if p["verdict"] == "yellow") / n, 3),
                "red": round(sum(1 for p in grp if p["verdict"] == "red") / n, 3),
                "model_fpr": round(fp / neg, 3) if neg else None,
                "model_fnr": round(fn / pos, 3) if pos else None}

    fairness = [fairness_slice(f"{lo}–{hi}", grp)
                for lo, hi in [(21, 30), (31, 40), (41, 50), (51, 60), (61, 70)]
                if (grp := [p for p in portfolio if lo <= p["age"] <= hi])]
    fairness_sex = [fairness_slice(label, grp)
                    for sex, label in [("M", "Male"), ("F", "Female")]
                    if (grp := [p for p in portfolio if p["sex"] == sex])]

    stp = sum(1 for p in portfolio if not p["referred"]) / len(portfolio)
    conflict_recall = tp / max(tp + fn, 1)
    conflict_precision = tp / max(tp + fp, 1)
    agreement = np.mean([engine.tier(p["rule_score"]) == engine.tier(p["ml_score"]) for p in portfolio])

    # affordability / financial viability metrics (the brief's core success metric)
    n = len(portfolio)
    aff_counts = {"pass": 0, "strain": 0, "fail": 0}
    for p in portfolio:
        aff_counts[p["afford"]["verdict"]] += 1
    afford_metrics = {
        "affordable_rate": round(aff_counts["pass"] / n, 4),
        "strained_rate": round(aff_counts["strain"] / n, 4),
        "not_justified_rate": round(aff_counts["fail"] / n, 4),
        "n_affordable": aff_counts["pass"], "n_strained": aff_counts["strain"],
        "n_not_justified": aff_counts["fail"],
        "avg_premium_to_income": round(float(np.mean([p["afford"]["pti"] for p in portfolio])), 4),
        "avg_annual_premium": round(float(np.mean([p["premium"] for p in portfolio])), 2),
        "indicator_fail_rates": {
            ind["label"]: round(sum(1 for p in portfolio
                                    if p["afford"]["indicators"][i]["status"] == "fail") / n, 4)
            for i, ind in enumerate(portfolio[0]["afford"]["indicators"])},
    }

    print("[7/7] writing reports…")
    model_report["prior_export"] = prior_models
    report = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"), "n_applicants": len(df), "n_packets": N_PACKETS,
        "external_learning": {"datasets": ext_report,
                              "n_usable": len(usable),
                              "total_rows": sum(d["rows"] for d in usable)},
        "model_history": history,
        "extraction": {"field_level_accuracy": round(extraction_accuracy, 4),
                        "per_field": {f: round(c / t, 4) for f, (c, t) in per_field.items()}},
        "conflict_screening": {"injected_rate": CONFLICT_RATE,
                                "detection_recall": round(conflict_recall, 4),
                                "detection_precision": round(conflict_precision, 4),
                                "tp": tp, "fp": fp, "fn": fn},
        "risk_models": model_report,
        "affordability": afford_metrics,
        "decisioning": {"straight_through_rate": round(stp, 4),
                         "rule_ml_tier_agreement": round(float(agreement), 4),
                         "n_overrides_learned": n_overrides,
                         "thresholds": {"a_line": int(a_line), "d_line": int(d_line), **thr_stats}},
        "fairness_by_age": fairness,
        "fairness_by_sex": fairness_sex,
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
