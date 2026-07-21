"""prudential_validate.py — weigh and VALIDATE our risk metrics against real
insurer data (Kaggle Prudential Life Insurance Assessment: 59,381 real applicants,
each carrying Prudential's own 1-8 underwriting rating).

Two jobs:
  weights   — run the real ratings through the same treatment external_data.py
              gives every dataset (standardized logistic + gradient boosting),
              so each metric's importance is a comparable, evidence-backed weight.
  validate  — score the real applicants with our rule-engine weight table and
              measure how well that score agrees with Prudential's real rating
              (AUC on high-risk = Response<=4). This is the number that says
              whether our weights reflect a real insurer's or were guessed.

Data stays local (Kaggle rules forbid redistribution; data/prudential/ is
gitignored). Run:  python src/prudential_validate.py [weights|validate]
"""
import glob
import os
import sys
import zipfile

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
PRU = os.path.join(ROOT, "data", "prudential")


def load_train():
    csv = os.path.join(PRU, "train.csv")
    if not os.path.exists(csv):
        for z in glob.glob(os.path.join(PRU, "*.zip")):
            with zipfile.ZipFile(z) as zf:
                for n in zf.namelist():
                    if n.endswith(".zip") or n.endswith(".csv"):
                        zf.extract(n, PRU)
        for z in glob.glob(os.path.join(PRU, "*.csv.zip")):
            with zipfile.ZipFile(z) as zf:
                zf.extractall(PRU)
    if not os.path.exists(csv):
        raise SystemExit("train.csv not found — download the Prudential competition data into data/prudential/")
    return pd.read_csv(csv)


def _features(df):
    """Prudential's (partly anonymized) columns mapped to our risk vocabulary."""
    X = pd.DataFrame(index=df.index)
    X["Applicant age"] = pd.to_numeric(df["Ins_Age"], errors="coerce")
    X["Body mass index"] = pd.to_numeric(df["BMI"], errors="coerce")
    X["Build (weight)"] = pd.to_numeric(df["Wt"], errors="coerce")
    mh = df[[c for c in df.columns if c.startswith("Medical_History_")]].apply(pd.to_numeric, errors="coerce")
    med = ((mh - mh.mean()) / mh.std(ddof=0).replace(0, 1)).sum(axis=1)
    med += df[[c for c in df.columns if c.startswith("Medical_Keyword_")]].sum(axis=1)
    X["Medical burden"] = med
    X["Prior insurance history"] = df[[c for c in df.columns
                                       if c.startswith("Insurance_History_")]].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    return X.fillna(X.median())


def weights():
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    df = load_train()
    y = (df["Response"] <= 4).astype(int)
    X = _features(df)
    print(f"loaded {len(df):,} real Prudential applicants · high-risk (Response<=4) {y.mean():.1%}\n")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=13, stratify=y)
    gb = GradientBoostingClassifier(random_state=13, n_estimators=200).fit(Xtr, ytr)
    sc = StandardScaler().fit(Xtr)
    lr = LogisticRegression(max_iter=3000).fit(sc.transform(Xtr), ytr)
    print(f"GB AUC {roc_auc_score(yte, gb.predict_proba(Xte)[:,1]):.3f} · "
          f"LR AUC {roc_auc_score(yte, lr.predict_proba(sc.transform(Xte))[:,1]):.3f}\n")

    imp = pd.Series(gb.feature_importances_, index=X.columns)
    share = (imp / imp.sum() * 100).sort_values(ascending=False)
    print(f"{'factor':28} {'weight share':>13}")
    for k, v in share.items():
        print(f"{k:28} {v:12.1f}%")


def validate():
    """Does our rule-engine weight table agree with Prudential's real ratings?
    Score each applicant with our published points, compare to Response."""
    from sklearn.metrics import roc_auc_score
    import engine

    df = load_train()
    y = (df["Response"] <= 4).astype(int)
    age = pd.to_numeric(df["Ins_Age"], errors="coerce").fillna(0.5)      # 0-1 normalized
    bmi = pd.to_numeric(df["BMI"], errors="coerce").fillna(0.4)
    mh = df[[c for c in df.columns if c.startswith("Medical_History_")]].apply(pd.to_numeric, errors="coerce")
    med_kw = df[[c for c in df.columns if c.startswith("Medical_Keyword_")]].sum(axis=1)

    # apply OUR rule-engine point curves to the mapped features (age & BMI are
    # 0-1 normalized in Prudential, so translate to real units first)
    real_age = 18 + age * 60
    real_bmi = 15 + bmi * 35
    W = engine.RULE_WEIGHTS
    score = (
        real_age.apply(lambda a: engine._pts(a, W["age"]))
        + real_bmi.apply(lambda b: engine._pts_bmi(b, W["bmi"]))
        + med_kw.clip(0, 6) * (W["condition_each"] / 2)
    )
    auc = roc_auc_score(y, score)
    print(f"our weight table scored on {len(df):,} real Prudential applicants: AUC {auc:.3f}")
    print("(medical + age + BMI only — the factors Prudential exposes; "
          "smoker/behavioural/financial are masked in their rating)")


if __name__ == "__main__":
    (weights if len(sys.argv) < 2 or sys.argv[1] == "weights" else validate)()
