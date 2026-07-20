"""published_models.py — Already-built, peer-reviewed risk models used as-is.

Instead of training everything ourselves, we score every applicant with the
Framingham Heart Study *office-based* (non-laboratory) general cardiovascular
disease model — D'Agostino et al., Circulation 2008. It is a published,
validated model (reported c-statistics ≈ 0.75–0.79 across cohorts) whose
coefficients are public, so no training is required. Inputs are all fields the
application already collects: age, sex, BMI, systolic blood pressure, current
smoking, and diabetes.

10-year CVD risk = 1 − S0 ** exp(Σ βx − mean)   (per sex)

The resulting probability is exposed as the `published_cvd_prior` feature to
the production models, and its parameters are exported so the dashboard can
compute the identical value in the browser for live scoring.
"""
import numpy as np

# D'Agostino 2008, Table — office-based (BMI) model, untreated blood pressure
FRAMINGHAM_OFFICE = {
    "F": {"b_lnage": 2.72107, "b_lnbmi": 0.51125, "b_lnsbp": 2.81291,
          "b_smoker": 0.61868, "b_diabetes": 0.77763,
          "s0": 0.94833, "mean": 26.0145},
    "M": {"b_lnage": 3.11296, "b_lnbmi": 0.79277, "b_lnsbp": 1.85508,
          "b_smoker": 0.70953, "b_diabetes": 0.53160,
          "s0": 0.88431, "mean": 23.9802},
}


def framingham_cvd10(age, sex_is_male, bmi, sbp, smoker_now, diabetes):
    """Vectorised 10-year general-CVD risk (0–1). All args array-like."""
    age = np.clip(np.asarray(age, dtype=float), 30, 74)   # model's validated range
    bmi = np.clip(np.asarray(bmi, dtype=float), 15, 50)
    sbp = np.clip(np.asarray(sbp, dtype=float), 90, 200)
    male = np.asarray(sex_is_male, dtype=bool)
    smoker = np.asarray(smoker_now, dtype=float)
    diab = np.asarray(diabetes, dtype=float)
    out = np.empty(age.shape, dtype=float)
    for is_m, key in ((True, "M"), (False, "F")):
        p = FRAMINGHAM_OFFICE[key]
        mask = male == is_m
        s = (p["b_lnage"] * np.log(age[mask]) + p["b_lnbmi"] * np.log(bmi[mask])
             + p["b_lnsbp"] * np.log(sbp[mask]) + p["b_smoker"] * smoker[mask]
             + p["b_diabetes"] * diab[mask])
        out[mask] = 1.0 - p["s0"] ** np.exp(s - p["mean"])
    return out


def prior_from_df(df):
    """Framingham office CVD prior for our applicant dataframe."""
    sbp = df["Blood Pressure"].astype(str).str.split("/").str[0].astype(float)
    return framingham_cvd10(
        df["Age"], df["Sex"] == "M", df["BMI"], sbp,
        (df["Smoker Status"] == "Smoker").astype(int),
        df["Existing Conditions"].astype(str).str.lower().str.contains("diabetes").astype(int),
    )
