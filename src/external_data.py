"""external_data.py — Learn risk priors from public real-world datasets.

Downloads 11 public health/actuarial/credit datasets (cached locally),
fits a small calibrated logistic model on each against the risk factors
it shares with our applicant schema (age, BMI, smoker, diabetes,
systolic BP, cholesterol), and blends them into a single
"External Risk Prior" — the mean event probability across all
dataset models. That prior becomes an input feature to both production
risk models, so every retrain learns from real-world evidence, not just
synthetic data. Each model's parameters are also exported so the
dashboard can compute the identical prior in the browser.
"""
import io, json, os, urllib.request
import numpy as np
import pandas as pd

CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "external")

# canonical factor names shared between our applicants and the external datasets
CANON = ["age", "bmi", "smoker", "diabetes", "sys_bp", "chol", "sex"]  # sex: 1 = male


def _num(s):
    return pd.to_numeric(s, errors="coerce")

def _load_insurance(p):
    d = pd.read_csv(p)
    X = pd.DataFrame({"age": d.age, "bmi": d.bmi, "smoker": (d.smoker == "yes").astype(int)})
    return X, (d.charges > d.charges.median()).astype(int)

def _load_framingham(p):
    d = pd.read_csv(p)
    X = pd.DataFrame({"age": d.age, "bmi": _num(d.BMI), "smoker": d.currentSmoker,
                      "diabetes": d.diabetes, "sys_bp": _num(d.sysBP), "chol": _num(d.totChol),
                      "sex": d.male})
    return X, d.TenYearCHD

HEART_COLS = ["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang",
              "oldpeak","slope","ca","thal","num"]

def _load_cleveland(p):
    d = pd.read_csv(p, header=None, names=HEART_COLS, na_values="?")
    X = pd.DataFrame({"age": d.age, "sex": d.sex, "sys_bp": d.trestbps, "chol": d.chol})
    return X, (d.num > 0).astype(int)

def _load_hungarian(p):
    d = pd.read_csv(p, header=None, names=HEART_COLS, na_values="?")
    X = pd.DataFrame({"age": d.age, "sex": d.sex, "sys_bp": _num(d.trestbps), "chol": _num(d.chol)})
    return X, (d.num > 0).astype(int)

def _load_va(p):
    d = pd.read_csv(p, header=None, names=HEART_COLS, na_values="?")
    X = pd.DataFrame({"age": d.age, "sex": d.sex,
                      "sys_bp": _num(d.trestbps).replace(0, np.nan)})
    return X, (d.num > 0).astype(int)

def _load_statlog_heart(p):
    d = pd.read_csv(p, sep=r"\s+", header=None)
    X = pd.DataFrame({"age": d[0], "sex": d[1], "sys_bp": d[3], "chol": d[4]})
    return X, (d[13] == 2).astype(int)

def _load_mammographic(p):
    d = pd.read_csv(p, header=None, na_values="?",
                    names=["birads", "age", "shape", "margin", "density", "severity"])
    return pd.DataFrame({"age": _num(d.age)}), _num(d.severity)

def _load_hcv(p):
    d = pd.read_csv(p)
    X = pd.DataFrame({"age": d.Age, "sex": (d.Sex == "m").astype(int)})
    return X, (~d.Category.str.contains("Blood Donor")).astype(int)

def _load_thoracic(p):
    rows = []
    with open(p) as f:
        in_data = False
        for line in f:
            line = line.strip()
            if in_data and line:
                rows.append(line.split(","))
            elif line.lower().startswith("@data"):
                in_data = True
    d = pd.DataFrame(rows)
    X = pd.DataFrame({"age": _num(d[15]), "smoker": (d[13] == "T").astype(int)})
    return X, (d[16] == "T").astype(int)

def _load_pima(p):
    d = pd.read_csv(p, header=None)
    X = pd.DataFrame({"age": d[7], "bmi": d[5].replace(0, np.nan)})
    return X, d[8]

def _load_heart_failure(p):
    d = pd.read_csv(p)
    X = pd.DataFrame({"age": d.age, "smoker": d.smoking, "diabetes": d.diabetes, "sex": d.sex})
    return X, d.DEATH_EVENT

def _load_haberman(p):
    d = pd.read_csv(p, header=None, names=["age", "year", "nodes", "status"])
    return pd.DataFrame({"age": d.age}), (d.status == 2).astype(int)

def _load_german_credit(p):
    d = pd.read_csv(p, sep=" ", header=None)
    return pd.DataFrame({"age": _num(d[12])}), (d[20] == 2).astype(int)

def _load_cervical(p):
    d = pd.read_csv(p, na_values="?")
    X = pd.DataFrame({"age": _num(d["Age"]), "smoker": _num(d["Smokes"])})
    return X, _num(d["Biopsy"])

def _load_coimbra(p):
    d = pd.read_csv(p)
    return pd.DataFrame({"age": d.Age, "bmi": d.BMI}), (d.Classification == 2).astype(int)

def _load_hepatitis(p):
    d = pd.read_csv(p, header=None, na_values="?")
    return pd.DataFrame({"age": _num(d[1])}), (d[0] == 1).astype(int)

def _load_ilpd(p):
    d = pd.read_csv(p, header=None)
    return pd.DataFrame({"age": _num(d[0])}), (d[10] == 1).astype(int)


REGISTRY = [
    ("Medical Cost / Insurance Charges (Kaggle mirror)", "insurance.csv",
     "https://raw.githubusercontent.com/stedy/Machine-Learning-with-R-datasets/master/insurance.csv", _load_insurance),
    ("Framingham Heart Study — 10yr CHD", "framingham.csv",
     "https://raw.githubusercontent.com/TarekDib03/Analytics/master/Week3%20-%20Logistic%20Regression/Data/framingham.csv", _load_framingham),
    ("UCI Heart Disease (Cleveland)", "cleveland.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data", _load_cleveland),
    ("Pima Indians Diabetes", "pima.csv",
     "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv", _load_pima),
    ("UCI Heart Failure Clinical Records — mortality", "heart_failure.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00519/heart_failure_clinical_records_dataset.csv", _load_heart_failure),
    ("Haberman Cancer Survival", "haberman.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/haberman/haberman.data", _load_haberman),
    ("Statlog German Credit — default risk", "german.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data", _load_german_credit),
    ("UCI Cervical Cancer Risk Factors", "cervical.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00383/risk_factors_cervical_cancer.csv", _load_cervical),
    ("Breast Cancer Coimbra", "coimbra.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00451/dataR2.csv", _load_coimbra),
    ("UCI Hepatitis — mortality", "hepatitis.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/hepatitis/hepatitis.data", _load_hepatitis),
    ("Indian Liver Patient Dataset", "ilpd.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00225/Indian%20Liver%20Patient%20Dataset%20(ILPD).csv", _load_ilpd),
    ("Statlog Heart Disease", "statlog_heart.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/heart/heart.dat", _load_statlog_heart),
    ("UCI Heart Disease (Hungarian)", "hungarian.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.hungarian.data", _load_hungarian),
    ("UCI Heart Disease (VA Long Beach)", "va.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.va.data", _load_va),
    ("UCI Mammographic Mass — malignancy", "mammographic.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/mammographic-masses/mammographic_masses.data", _load_mammographic),
    ("UCI Hepatitis C Virus (HCV) panel", "hcv.csv",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00571/hcvdat0.csv", _load_hcv),
    ("UCI Thoracic Surgery — 1yr mortality", "thoracic.arff",
     "https://archive.ics.uci.edu/ml/machine-learning-databases/00277/ThoraricSurgery.arff", _load_thoracic),
]


def _fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return False
    req = urllib.request.Request(url, headers={"User-Agent": "underwriting-copilot-mvp/0.4"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    with open(path, "wb") as f:
        f.write(data)
    return True


def load_and_fit(seed=13):
    """Download (or reuse cached) datasets and fit one logistic prior model per dataset.

    Returns (models, report) where models is a list of dicts usable by prior_scores()
    and exportable to the dashboard for identical in-browser computation.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score

    os.makedirs(CACHE, exist_ok=True)
    models, report = [], []
    for title, fname, url, loader in REGISTRY:
        path = os.path.join(CACHE, fname)
        try:
            fetched = _fetch(url, path)
            X, y = loader(path)
            keep = X.notna().all(axis=1) & pd.notna(y)
            X, y = X[keep], np.asarray(y[keep], dtype=int)
            if len(X) < 50 or y.mean() in (0, 1):
                raise ValueError("degenerate dataset")
            feats = list(X.columns)
            Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=seed, stratify=y)
            sc = StandardScaler().fit(Xtr)
            lr = LogisticRegression(max_iter=2000).fit(sc.transform(Xtr), ytr)
            auc = float(roc_auc_score(yte, lr.predict_proba(sc.transform(Xte))[:, 1]))
            models.append({"name": title, "features": feats,
                           "coef": [float(v) for v in lr.coef_[0]],
                           "intercept": float(lr.intercept_[0]),
                           "mean": [float(v) for v in sc.mean_],
                           "std": [float(v) for v in sc.scale_]})
            report.append({"name": title, "rows": int(len(X)), "features": feats,
                           "auc": round(auc, 3), "event_rate": round(float(y.mean()), 3),
                           "source": url, "cached": not fetched})
        except Exception as e:
            report.append({"name": title, "error": str(e), "source": url})
    return models, report


def _canon_frame(df):
    """Map our applicant dataframe onto the canonical factor names."""
    sys_bp = df["Blood Pressure"].astype(str).str.split("/").str[0].astype(float)
    return pd.DataFrame({
        "age": df["Age"].astype(float), "bmi": df["BMI"].astype(float),
        "smoker": (df["Smoker Status"] == "Smoker").astype(float),
        "diabetes": df["Existing Conditions"].astype(str).str.lower().str.contains("diabetes").astype(float),
        "sys_bp": sys_bp, "chol": df["Cholesterol (mg/dL)"].astype(float),
        "sex": (df["Sex"] == "M").astype(float) if "Sex" in df else 0.5,
    })


def prior_scores(models, df):
    """External Risk Prior per applicant: mean event probability across dataset models."""
    C = _canon_frame(df)
    if not models:
        return np.full(len(df), 0.5)
    probs = []
    for m in models:
        Z = np.full(len(df), m["intercept"])
        for i, f in enumerate(m["features"]):
            Z += m["coef"][i] * (C[f].values - m["mean"][i]) / m["std"][i]
        probs.append(1.0 / (1.0 + np.exp(-Z)))
    return np.mean(probs, axis=0)


if __name__ == "__main__":
    models, report = load_and_fit()
    print(json.dumps(report, indent=2))
    print(f"{len(models)} of {len(REGISTRY)} datasets usable")
