"""docgen.py — Synthetic document packet generator.

For each applicant produces a 3-document PDF packet modeled on real
underwriting inputs:
  1. application_form.pdf  — in-depth form: yes/no questions, each "Yes"
                             followed by a fill-in-the-blank detail line
                             (structure per manager feedback)
  2. payslip.pdf           — employer, gross pay, YTD income
  3. paramed_report.pdf    — exam vitals, cotinine (nicotine) result, DOB

Conflicts are injected at a controlled rate and logged to ground truth,
making conflict-detection *measurable*:
  income_mismatch      form declared income != payslip annualized income
  smoker_nondisclosure form says No tobacco, paramed cotinine POSITIVE
  dob_mismatch         form DOB != paramed report DOB
  debt_understated     form declared debt << credit-report debt figure
"""
import json, os
import numpy as np
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

W, H = LETTER
INK = (0.10, 0.16, 0.20)
MUTE = (0.42, 0.46, 0.52)

def _header(c, title, sub):
    c.setFillColorRGB(*INK); c.setFont("Helvetica-Bold", 13)
    c.drawString(0.8 * inch, H - 0.8 * inch, title)
    c.setFont("Helvetica", 8.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, H - 0.98 * inch, sub)
    c.line(0.8 * inch, H - 1.08 * inch, W - 0.8 * inch, H - 1.08 * inch)

def _kv(c, y, label, value, x=0.8):
    c.setFont("Helvetica", 8); c.setFillColorRGB(*MUTE)
    c.drawString(x * inch, y, label.upper())
    c.setFont("Helvetica", 10.5); c.setFillColorRGB(*INK)
    c.drawString(x * inch, y - 13, str(value))
    return y - 34

def _yesno(c, y, qnum, question, answer_yes, detail=None):
    c.setFont("Helvetica", 9.5); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, f"{qnum}. {question}")
    y -= 16
    for lab, sel in (("Yes", answer_yes), ("No", not answer_yes)):
        x = 0.95 * inch if lab == "Yes" else 1.75 * inch
        c.rect(x, y - 2, 9, 9, fill=1 if sel else 0)
        c.setFont("Helvetica-Bold" if sel else "Helvetica", 9)
        c.drawString(x + 14, y, lab)
    y -= 16
    if answer_yes:
        c.setFont("Helvetica-Oblique", 8); c.setFillColorRGB(*MUTE)
        c.drawString(0.95 * inch, y, "If yes, provide details:")
        y -= 14
        c.setFillColorRGB(*INK); c.rect(0.95 * inch, y - 4, 5.6 * inch, 16)
        c.setFont("Courier", 8.5)
        c.drawString(1.02 * inch, y, detail or "")
        y -= 24
    return y - 6

def application_form(path, a, printed):
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "LIFE INSURANCE APPLICATION — PART A & B", f"Application ID {a['Applicant ID']}  ·  Confidential")
    y = H - 1.45 * inch
    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "SECTION 1 — APPLICANT INFORMATION"); y -= 24
    y = _kv(c, y, "Full Name", printed["name"]);            y2 = y + 34
    _kv(c, y2, "Date of Birth", printed["form_dob"], x=4.2)
    y = _kv(c, y, "Occupation", a["Occupation"]);           y2 = y + 34
    _kv(c, y2, "Employer", a["Employer"], x=4.2)
    y = _kv(c, y, "City / State", f"{a['City']}, {a['State']}"); y2 = y + 34
    _kv(c, y2, "Policy Requested", a["Policy Type Requested"], x=4.2)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.8 * inch, y, "SECTION 2 — FINANCIAL DECLARATION"); y -= 24
    y = _kv(c, y, "Declared Annual Income (USD)", f"{printed['form_income']:,.0f}"); y2 = y + 34
    _kv(c, y2, "Coverage Amount Requested (USD)", f"{a['Coverage Amount Requested (USD)']:,.0f}", x=4.2)
    y = _kv(c, y, "Declared Total Debt (USD)", f"{printed['form_debt']:,.0f}"); y2 = y + 34
    _kv(c, y2, "Avg Bank Balance (USD)", f"{a['Avg Bank Balance (USD)']:,.0f}", x=4.2)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.8 * inch, y, "SECTION 4 — HEALTH & LIFESTYLE QUESTIONNAIRE"); y -= 22
    conds = a["Existing Conditions"]
    y = _yesno(c, y, "4a", "Have you used tobacco or nicotine products in the last 5 years?",
               printed["form_tobacco_yes"],
               "Cigarettes, approx. half pack daily" if printed["form_tobacco_yes"] else None)
    y = _yesno(c, y, "4b", "Have you ever been diagnosed with or treated for any chronic medical condition?",
               conds != "None", conds if conds != "None" else None)
    y = _yesno(c, y, "4c", "Is there a history of heart disease, cancer, or diabetes in your immediate family?",
               bool(a["Family History Flag"]), "Parent — see attending records" if a["Family History Flag"] else None)
    y = _yesno(c, y, "4d", "Do you participate in hazardous activities (aviation, diving, motorsport)?", False)
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, 0.7 * inch, "Synthetic document generated for prototype evaluation — not a real application.")
    c.save()

def payslip(path, a, printed):
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "EARNINGS STATEMENT", f"{a['Employer']}  ·  Pay period: 01 Jun 2026 – 30 Jun 2026")
    y = H - 1.5 * inch
    y = _kv(c, y, "Employee", printed["name"])
    y = _kv(c, y, "Employment Status", a["Employment Status"])
    monthly = printed["payslip_income"] / 12
    y = _kv(c, y, "Gross Pay (this period)", f"${monthly:,.2f}")
    y = _kv(c, y, "Annualized Gross Income", f"${printed['payslip_income']:,.2f}")
    y = _kv(c, y, "Years with Employer", a["Years Employed"])
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, 0.7 * inch, "Synthetic document generated for prototype evaluation.")
    c.save()

def paramed_report(path, a, printed):
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "PARAMEDICAL EXAMINATION REPORT", "Collected by licensed examiner · Lab panel attached")
    y = H - 1.5 * inch
    y = _kv(c, y, "Examinee", printed["name"])
    y = _kv(c, y, "Date of Birth (per ID)", printed["paramed_dob"])
    y = _kv(c, y, "Height / Weight", f"{a['Height (cm)']} cm / {a['Weight (kg)']} kg")
    y = _kv(c, y, "Blood Pressure", a["Blood Pressure"])
    y = _kv(c, y, "Total Cholesterol", f"{a['Cholesterol (mg/dL)']} mg/dL")
    y = _kv(c, y, "Cotinine (nicotine metabolite)", printed["cotinine"])
    y = _kv(c, y, "Credit-Bureau Debt Figure (attached consumer report)", f"${printed['bureau_debt']:,.0f}")
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, 0.7 * inch, "Synthetic document generated for prototype evaluation.")
    c.save()

def _shift_dob(dob, rng):
    y_, m, d = dob.split("-")
    return f"{y_}-{m}-{min(int(d) + int(rng.integers(1, 9)), 28):02d}"

def generate_packets(df, out_dir, conflict_rate=0.30, seed=7):
    rng = np.random.default_rng(seed)
    os.makedirs(out_dir, exist_ok=True)
    truth = {}
    for _, a in df.iterrows():
        aid = a["Applicant ID"]
        pdir = os.path.join(out_dir, aid); os.makedirs(pdir, exist_ok=True)
        is_smoker = a["Smoker Status"] == "Smoker"
        printed = {
            "name": a["Full Name"], "form_dob": a["Date of Birth"], "paramed_dob": a["Date of Birth"],
            "form_income": float(a["Annual Income (USD)"]), "payslip_income": float(a["Annual Income (USD)"]),
            "form_debt": float(a["Existing Debt (USD)"]), "bureau_debt": float(a["Existing Debt (USD)"]),
            "form_tobacco_yes": is_smoker,
            "cotinine": "POSITIVE" if is_smoker else "NEGATIVE",
        }
        injected = []
        if rng.random() < conflict_rate:
            kind = rng.choice(["income_mismatch", "smoker_nondisclosure", "dob_mismatch", "debt_understated"])
            if kind == "income_mismatch":
                printed["form_income"] = round(printed["payslip_income"] * float(rng.uniform(1.25, 1.7)), -2)
            elif kind == "smoker_nondisclosure":
                printed["form_tobacco_yes"] = False
                printed["cotinine"] = "POSITIVE"
            elif kind == "dob_mismatch":
                printed["paramed_dob"] = _shift_dob(a["Date of Birth"], rng)
            elif kind == "debt_understated":
                printed["bureau_debt"] = round(max(printed["form_debt"], 5000) * float(rng.uniform(1.8, 3.0)), -2)
            injected.append(str(kind))
        application_form(os.path.join(pdir, "application_form.pdf"), a, printed)
        payslip(os.path.join(pdir, "payslip.pdf"), a, printed)
        paramed_report(os.path.join(pdir, "paramed_report.pdf"), a, printed)
        truth[aid] = {"printed": printed, "injected_conflicts": injected}
    with open(os.path.join(out_dir, "doc_ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=1)
    return truth
