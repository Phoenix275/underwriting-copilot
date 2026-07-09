"""datagen.py — Synthetic life-insurance applicant generator.

Generates realistic, correlated applicant records with a ground-truth
high-risk label. Schema matches the team's Life Insurance Sample Dataset
(Applicants / Medical Records / Financial Viability sheets) so the two
datasets are interchangeable.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

FIRST = ["Aisha","Marcus","Priya","David","Linda","James","Grace","Robert","Elena","Samuel",
         "Nina","Victor","Farah","Tomas","Ingrid","Kofi","Mei","Arjun","Sofia","Liam",
         "Yuki","Omar","Clara","Dmitri","Anya","Rahul","Beatriz","Chen","Amara","Jonas"]
LAST = ["Rahman","Bell","Nair","Kim","Torres","Whitfield","Odom","Nguyen","Vasquez","Osei",
        "Kaplan","Ivanov","Haddad","Lindqvist","Mensah","Tanaka","Sharma","Rossi","Okafor","Novak",
        "Fischer","Almeida","Wu","Petrov","Kowalski","Iyer","Santos","Zhang","Diallo","Berg"]
CITIES = [("Frisco","TX"),("McKinney","TX"),("Plano","TX"),("Dallas","TX"),("Austin","TX"),
          ("Houston","TX"),("Denver","CO"),("Phoenix","AZ"),("Atlanta","GA"),("Charlotte","NC")]
OCCUPATIONS = [("Marketing Coordinator","office",52000),("Construction Foreman","manual",64000),
               ("Small Business Owner","self",71000),("Accountant","office",92000),
               ("Registered Nurse","office",74000),("Truck Driver","manual",47000),
               ("Sales Manager","office",83000),("Teacher","office",48000),
               ("Software Engineer","office",115000),("Electrician","manual",61000),
               ("Retail Associate","office",34000),("Physician","office",210000)]
CONDITIONS = ["Hypertension","Type 2 Diabetes","High Cholesterol","Asthma","Hypothyroidism",
              "Sleep Apnea","Anxiety Disorder","GERD"]
POLICIES = ["Term Life - 20yr","Term Life - 30yr","Whole Life","Universal Life"]
HAZARDS = ["Scuba Diving","Rock Climbing","Skydiving","Motorcycle Racing","Private Aviation"]
CIRCUMSTANCES = ["Recent job change — income in transition","Primary caregiver for elderly parent",
                 "Bankruptcy discharged 3 years ago — finances rebuilt","Recent immigrant — thin US credit file",
                 "Employment gap for family caregiving","Seasonal income — agricultural work",
                 "Recently widowed — sole household earner","Active-duty military deployment pending"]


def generate(n: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        age = int(np.clip(rng.normal(42, 12), 21, 70))
        occ, occ_type, base_inc = OCCUPATIONS[rng.integers(len(OCCUPATIONS))]
        income = float(np.round(base_inc * rng.lognormal(0, 0.25), -2))
        smoker_p = 0.18 + 0.10 * (occ_type == "manual")
        r = rng.random()
        smoker = "Smoker" if r < smoker_p else ("Former smoker" if r < smoker_p + 0.18 else "Non-smoker")
        # BMI correlated with age, slightly with smoking cessation
        bmi = float(np.clip(rng.normal(25 + 0.06 * (age - 40) + (1.0 if smoker == "Former smoker" else 0), 4.3), 16, 46))
        height = int(np.clip(rng.normal(170, 9), 150, 198))
        weight = round(bmi * (height / 100) ** 2, 1)
        # conditions: probability rises with age, bmi, smoking
        cond_lambda = 0.25 + 0.02 * max(age - 35, 0) + 0.05 * max(bmi - 28, 0) + (0.4 if smoker == "Smoker" else 0)
        n_cond = min(rng.poisson(cond_lambda), 3)
        conds = list(rng.choice(CONDITIONS, size=n_cond, replace=False)) if n_cond else []
        fam = int(rng.random() < 0.42)
        sys_bp = int(np.clip(rng.normal(118 + 0.3 * (age - 40) + 1.2 * max(bmi - 25, 0) + (6 if "Hypertension" in conds else 0), 10), 95, 185))
        dia_bp = int(np.clip(sys_bp * 0.64 + rng.normal(0, 4), 60, 115))
        chol = int(np.clip(rng.normal(185 + 0.6 * (age - 40) + 1.5 * max(bmi - 25, 0), 28), 130, 330))
        monthly_exp = float(np.round(income / 12 * rng.uniform(0.35, 0.75), 2))
        debt = float(np.round(max(0, rng.normal(income * 0.35, income * 0.30)), -2))
        bank_bal = float(np.round(max(200, rng.normal(income * 0.30, income * 0.25)), 0))
        emp_status = "Self-Employed" if occ_type == "self" else ("Part-time" if rng.random() < 0.08 else "Full-time")
        years_emp = int(np.clip(rng.normal(min(age - 22, 15), 5), 0, age - 20))
        credit = int(np.clip(rng.normal(715 - 40 * (debt / max(income, 1)) + 15 * (years_emp > 5), 55), 480, 850))
        dti = round(debt / income, 3)
        # coverage in $25k increments, $25k–$1M (per Manulife OTIP application)
        coverage = int(np.clip(round(income * rng.uniform(3, 8) / 25000) * 25000, 25000, 1000000))
        birth_year = 2026 - age
        dob = f"{birth_year}-{rng.integers(1,13):02d}-{rng.integers(1,29):02d}"
        name = f"{FIRST[rng.integers(len(FIRST))]} {LAST[rng.integers(len(LAST))]}"
        city, state = CITIES[rng.integers(len(CITIES))]
        # lifestyle rating factors (standard avocation / MVR / alcohol questions)
        hazard = HAZARDS[rng.integers(len(HAZARDS))] if rng.random() < (0.11 if occ_type == "manual" else 0.07) else "None"
        violations = int(min(rng.poisson(0.35 + 0.25 * (occ_type == "manual")), 4))
        ra = rng.random()
        alcohol = "Heavy" if ra < 0.07 else ("Moderate" if ra < 0.55 else "None")
        unique = CIRCUMSTANCES[rng.integers(len(CIRCUMSTANCES))] if rng.random() < 0.12 else "None"
        # Section 6 personal declarations (per Manulife OTIP term-life application)
        sex = "M" if rng.random() < 0.5 else "F"
        prior_decline = int(rng.random() < 0.05)
        dangerous_driving = int(rng.random() < (0.10 if violations >= 2 else 0.03))
        foreign_travel = int(rng.random() < 0.14)
        drug_use = int(rng.random() < (0.18 if alcohol == "Heavy" else 0.03))
        criminal_record = int(rng.random() < 0.035)
        bankruptcy = int(rng.random() < (0.09 if credit < 600 else 0.03))
        weight_change = int(rng.random() < 0.12)
        # Section 2: existing/pending coverage with another carrier
        existing_cov = int(np.round(income * rng.uniform(1, 4), -4)) if rng.random() < 0.25 else 0
        replacing = int(existing_cov > 0 and rng.random() < 0.30)
        net_worth = float(np.round(bank_bal + income * rng.uniform(0.5, 4.0) - debt, -2))

        # latent ground-truth risk (what a mortality/lapse outcome would correlate with)
        z = (0.055 * (age - 42) + (1.35 if smoker == "Smoker" else 0.35 if smoker == "Former smoker" else 0)
             + 0.09 * max(bmi - 27, 0) + 0.10 * max(18.5 - bmi, 0) * 2
             + 0.55 * n_cond + 0.30 * fam + 1.1 * min(dti, 2.0) - 0.006 * (credit - 700)
             + (0.55 if hazard != "None" else 0) + 0.22 * violations
             + (0.65 if alcohol == "Heavy" else 0)
             + (0.25 if sex == "M" else 0)
             + 0.50 * prior_decline + 0.35 * dangerous_driving + 0.70 * drug_use
             + 0.25 * criminal_record + 0.45 * bankruptcy
             + 0.15 * weight_change + 0.05 * foreign_travel
             + rng.normal(0, 0.9))
        rows.append({
            "Applicant ID": f"APP-{1001 + i}", "Full Name": name, "Sex": sex, "Age": age, "Date of Birth": dob,
            "City": city, "State": state, "Occupation": occ, "Employer": ("Self-Employed" if occ_type == "self" else f"{city} {occ.split()[0]} Group"),
            "Employment Status": emp_status, "Years Employed": years_emp,
            "Annual Income (USD)": income, "Monthly Expenses (USD)": monthly_exp,
            "Policy Type Requested": POLICIES[rng.integers(len(POLICIES))],
            "Coverage Amount Requested (USD)": coverage,
            "Height (cm)": height, "Weight (kg)": weight, "BMI": round(bmi, 1),
            "Smoker Status": smoker, "Existing Conditions": ", ".join(conds) if conds else "None",
            "Family History Flag": fam, "Blood Pressure": f"{sys_bp}/{dia_bp}", "Cholesterol (mg/dL)": chol,
            "Existing Debt (USD)": debt, "Avg Bank Balance (USD)": bank_bal, "Credit Score": credit,
            "Debt-to-Income Ratio": dti,
            "Hazardous Activities": hazard, "Driving Violations (3yr)": violations,
            "Alcohol Use": alcohol, "Unique Circumstances": unique,
            "Net Worth (USD)": net_worth, "Existing Coverage (USD)": existing_cov,
            "Replacing Coverage": replacing,
            "Prior Application Declined": prior_decline, "Dangerous Driving (5yr)": dangerous_driving,
            "Foreign Travel Planned": foreign_travel, "Drug/Alcohol Counselling (5yr)": drug_use,
            "Criminal Record": criminal_record, "Bankruptcy Declared": bankruptcy,
            "Weight Change 10lb (12mo)": weight_change, "_z": z,
        })
    df = pd.DataFrame(rows)
    thresh = df["_z"].quantile(0.65)  # top 35% flagged high-risk
    df["High Risk Label"] = (df["_z"] >= thresh).astype(int)
    return df.drop(columns=["_z"])


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    df = generate(n)
    df.to_csv("output/applicants.csv", index=False)
    print(f"generated {len(df)} applicants | high-risk rate {df['High Risk Label'].mean():.3f}")
