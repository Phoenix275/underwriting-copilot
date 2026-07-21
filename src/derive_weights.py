"""Build one person-level NHANES table (2007-2014) with measured risk factors +
linked mortality, then estimate each factor's real all-cause-mortality multiple
by logistic regression. Real people, real deaths."""
import numpy as np, pandas as pd, glob, os

D = "data/nhanes"
CYC = ["E", "F", "G", "H"]

def xpt(name, s):
    return pd.read_sas(f"{D}/{name}_{s}.XPT")

frames = []
for s in CYC:
    demo = xpt("DEMO", s)[["SEQN", "RIAGENDR", "RIDAGEYR"]]
    bmx = xpt("BMX", s)[["SEQN", "BMXBMI"]]
    bpx = xpt("BPX", s)[["SEQN", "BPXSY1"]]
    tc = xpt("TCHOL", s)[["SEQN", "LBXTC"]]
    ghb = xpt("GHB", s)[["SEQN", "LBXGH"]]        # HbA1c %
    cot = xpt("COT", s)[["SEQN", "LBXCOT"]]       # serum cotinine ng/mL
    # linked mortality: fixed-width public-use layout
    # official NCHS public-use LMF fixed-width layout
    mort = pd.read_fwf(f"{D}/MORT_{s}.dat", header=None,
                       colspecs=[(0, 6), (14, 15), (15, 16), (45, 48)],
                       names=["SEQN", "ELIGSTAT", "MORTSTAT", "PERMTH_EXM"])
    for col in ("SEQN", "ELIGSTAT", "MORTSTAT", "PERMTH_EXM"):
        mort[col] = pd.to_numeric(mort[col], errors="coerce")
    df = demo
    for f in (bmx, bpx, tc, ghb, cot, mort):
        df = df.merge(f, on="SEQN", how="left")
    frames.append(df)

d = pd.concat(frames, ignore_index=True)
d = d[(d.ELIGSTAT == 1) & d.MORTSTAT.notna()]        # mortality-eligible only
d = d[d.RIDAGEYR >= 18]
d["dead"] = d.MORTSTAT.astype(int)
d["male"] = (d.RIAGENDR == 1).astype(int)
d["age"] = d.RIDAGEYR
d["bmi"] = d.BMXBMI
d["sbp"] = d.BPXSY1
d["chol"] = d.LBXTC
d["diabetic"] = (d.LBXGH >= 6.5).astype(float)       # HbA1c >=6.5% = diabetes
d["smoker"] = (d.LBXCOT >= 10).astype(float)         # cotinine >=10 ng/mL = active smoker
core = d.dropna(subset=["age", "bmi", "sbp", "chol", "diabetic", "smoker"])
print(f"NHANES 2007-2014: {len(core):,} adults, {core.dead.sum():,} linked deaths "
      f"({core.dead.mean():.1%}), median follow-up {core.PERMTH_EXM.median()/12:.0f} yr")
core.to_parquet("/private/tmp/claude-501/-Users-tegh-underwriting-copilot/8c86d8e5-baed-46a0-8b78-8a704e7f2e80/scratchpad/nhanes.parquet")

# real all-cause-mortality odds ratios (age/sex-adjusted logistic — the multiples)
import statsmodels.api as sm
X = pd.DataFrame({
    "age10": core.age / 10,
    "male": core.male,
    "smoker": core.smoker,
    "bmi_obese": (core.bmi >= 30).astype(int),
    "bmi_low": (core.bmi < 18.5).astype(int),
    "htn2": (core.sbp >= 140).astype(int),
    "diabetic": core.diabetic,
    "chol_high": (core.chol >= 240).astype(int),
})
X = sm.add_constant(X)
m = sm.Logit(core.dead.values, X).fit(disp=0)
OR = np.exp(m.params)
print("\nreal all-cause-mortality odds ratios (age/sex-adjusted, NHANES linked deaths):")
for k in X.columns:
    if k == "const":
        continue
    print(f"  {k:12} OR {OR[k]:.2f}   (95% CI {np.exp(m.conf_int().loc[k,0]):.2f}-{np.exp(m.conf_int().loc[k,1]):.2f})")
