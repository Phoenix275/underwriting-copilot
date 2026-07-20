"""docgen.py — Synthetic document packet generator.

For each applicant produces a 5-document PDF packet modeled on real
underwriting inputs:
  1. application_form.pdf  — in-depth form: yes/no questions, each "Yes"
                             followed by a fill-in-the-blank detail line
                             (structure per manager feedback)
  2. payslip.pdf           — employer, gross pay, YTD income
  3. paramed_report.pdf    — exam vitals, cotinine (nicotine) result, DOB
  4. bank_statement.pdf    — 3-month deposits/outflows with expense categories
  5. tax_slip.pdf          — prior-year income reported to the tax authority

Conflicts are injected at a controlled rate and logged to ground truth,
making conflict-detection *measurable*:
  income_mismatch         form declared income != payslip annualized income
  smoker_nondisclosure    form says No tobacco, paramed cotinine POSITIVE
  dob_mismatch            form DOB != paramed report DOB
  debt_understated        form declared debt << credit-report debt figure
  income_deposit_mismatch bank deposits run far below payslip income
  tax_income_mismatch     tax-reported income << income declared on the form
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
    """Two-page application modeled on the Manulife OTIP term-life form:
    S1 applicant info, S2 insurance amount + financials, S4 health questions,
    page 2: S5 personal declarations (Manulife Section 6) + weight change."""
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "APPLICATION FOR TERM LIFE INSURANCE", f"Application ID {a['Applicant ID']}  ·  Confidential  ·  Page 1 of 2")
    y = H - 1.45 * inch
    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "SECTION 1 — APPLICANT INFORMATION"); y -= 24
    y = _kv(c, y, "Full Name", printed["name"]);            y2 = y + 34
    _kv(c, y2, "Date of Birth", printed["form_dob"], x=4.2)
    y = _kv(c, y, "Sex", {"M": "Male", "F": "Female"}.get(a.get("Sex", ""), "—")); y2 = y + 34
    _kv(c, y2, "Smoker Status (last 12 months)", "Smoker" if printed["form_tobacco_yes"] else "Non-Smoker", x=4.2)
    y = _kv(c, y, "Occupation", a["Occupation"]);           y2 = y + 34
    _kv(c, y2, "Employer", a["Employer"], x=4.2)
    y = _kv(c, y, "City / State", f"{a['City']}, {a['State']}"); y2 = y + 34
    _kv(c, y2, "Policy Requested", a["Policy Type Requested"], x=4.2)

    c.setFont("Helvetica-Bold", 9)
    c.drawString(0.8 * inch, y, "SECTION 2 — AMOUNT OF INSURANCE & FINANCIAL DECLARATION"); y -= 24
    y = _kv(c, y, "Declared Annual Income (USD)", f"{printed['form_income']:,.0f}"); y2 = y + 34
    _kv(c, y2, "Coverage Amount Requested (USD)", f"{a['Coverage Amount Requested (USD)']:,.0f}", x=4.2)
    y = _kv(c, y, "Declared Total Debt (USD)", f"{printed['form_debt']:,.0f}"); y2 = y + 34
    _kv(c, y2, "Avg Bank Balance (USD)", f"{a['Avg Bank Balance (USD)']:,.0f}", x=4.2)
    y = _kv(c, y, "Personal Net Worth (USD)", f"{a.get('Net Worth (USD)', 0):,.0f}"); y2 = y + 34
    exist = a.get("Existing Coverage (USD)", 0)
    _kv(c, y2, "Existing Coverage With Another Carrier",
        f"${exist:,.0f}" + (" — intends to replace" if a.get("Replacing Coverage") else "") if exist else "None", x=4.2)

    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "SECTION 4 — HEALTH & LIFESTYLE QUESTIONNAIRE"); y -= 22
    conds = a["Existing Conditions"]
    y = _yesno(c, y, "4a", "Have you used tobacco or tobacco cessation products in the past 12 months?",
               printed["form_tobacco_yes"],
               "Cigarettes, approx. half pack daily" if printed["form_tobacco_yes"] else None)
    y = _yesno(c, y, "4b", "Have you ever been diagnosed with or treated for any chronic medical condition?",
               conds != "None", conds if conds != "None" else None)
    y = _yesno(c, y, "4c", "Have any parents or siblings been diagnosed before age 60 with heart disease, stroke or cancer?",
               bool(a["Family History Flag"]), "Parent — see attending records" if a["Family History Flag"] else None)
    hazard = a.get("Hazardous Activities", "None")
    y = _yesno(c, y, "4d", "Any intention of piloting aircraft, scuba diving, parachuting, racing, climbing or other hazardous activity?",
               hazard != "None", hazard if hazard != "None" else None)
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, 0.7 * inch, "Synthetic document generated for prototype evaluation — not a real application.")
    c.showPage()

    _header(c, "APPLICATION FOR TERM LIFE INSURANCE", f"Application ID {a['Applicant ID']}  ·  Confidential  ·  Page 2 of 2")
    y = H - 1.45 * inch
    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "SECTION 5 — PERSONAL DECLARATIONS"); y -= 22
    g = lambda col: bool(a.get(col, 0))
    y = _yesno(c, y, "5a", "Ever applied for insurance that was declined, modified or rated?",
               g("Prior Application Declined"), "Prior application — see remarks" if g("Prior Application Declined") else None)
    y = _yesno(c, y, "5b", "In the past 5 years, charged with careless/dangerous driving or had your licence suspended?",
               g("Dangerous Driving (5yr)"), "See motor vehicle record" if g("Dangerous Driving (5yr)") else None)
    viol = int(a.get("Driving Violations (3yr)", 0))
    y = _yesno(c, y, "5c", "Within the past 2 years, charged with 2 or more moving or traffic violations?",
               viol >= 2, f"{viol} violations on record" if viol >= 2 else None)
    y = _yesno(c, y, "5d", "Within the next 12 months, any expectation to travel or reside outside the country?",
               g("Foreign Travel Planned"), "Travel planned — details on file" if g("Foreign Travel Planned") else None)
    y = _yesno(c, y, "5e", "In the past 5 years, used drugs other than medically, or been counselled for alcohol or drug use?",
               g("Drug/Alcohol Counselling (5yr)"), "See remarks" if g("Drug/Alcohol Counselling (5yr)") else None)
    y = _yesno(c, y, "5f", "Been convicted of a criminal offence, or currently charged with one?",
               g("Criminal Record"), "See remarks" if g("Criminal Record") else None)
    y = _yesno(c, y, "5g", "Declared, or currently contemplating, personal or business bankruptcy?",
               g("Bankruptcy Declared"), "Discharged — see remarks" if g("Bankruptcy Declared") else None)
    y = _yesno(c, y, "5h", "Has your weight changed by more than 10 lbs (4.5 kg) in the past 12 months?",
               g("Weight Change 10lb (12mo)"), "See health declaration" if g("Weight Change 10lb (12mo)") else None)
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

def bank_statement(path, a, printed, rng):
    """3-month personal account summary: deposits vs categorized outflows.
    The AVERAGE lines are the extraction ground truth; the per-month rows
    jitter around them for realism (display only)."""
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "PERSONAL ACCOUNT STATEMENT", "First Meridian Bank  ·  Statement period: 01 Apr 2026 – 30 Jun 2026")
    y = H - 1.5 * inch
    y = _kv(c, y, "Account Holder", printed["name"])
    dep, outf = printed["bank_deposit_monthly"], printed["bank_outflow_monthly"]
    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "MONTHLY ACTIVITY"); y -= 18
    c.setFont("Helvetica", 8.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, y, "MONTH"); c.drawString(2.6 * inch, y, "TOTAL DEPOSITS"); c.drawString(4.4 * inch, y, "TOTAL WITHDRAWALS")
    y -= 14; c.setFont("Helvetica", 9.5); c.setFillColorRGB(*INK)
    for mon in ("April 2026", "May 2026", "June 2026"):
        jd, jo = dep * float(rng.uniform(0.96, 1.04)), outf * float(rng.uniform(0.96, 1.04))
        c.drawString(0.8 * inch, y, mon)
        c.drawString(2.6 * inch, y, f"${jd:,.2f}")
        c.drawString(4.4 * inch, y, f"${jo:,.2f}")
        y -= 15
    y -= 8
    y = _kv(c, y, "Average Monthly Deposits", f"${dep:,.2f}")
    y = _kv(c, y, "Average Monthly Outflows", f"${outf:,.2f}")
    c.setFont("Helvetica-Bold", 9); c.setFillColorRGB(*INK)
    c.drawString(0.8 * inch, y, "OUTFLOWS BY CATEGORY (MONTHLY AVERAGE)"); y -= 18
    debt_pay = min(float(a["Existing Debt (USD)"]) * 0.025, outf * 0.55)
    housing = (outf - debt_pay) * 0.52
    utilities = (outf - debt_pay) * 0.11
    groceries = (outf - debt_pay) * 0.17
    transport = (outf - debt_pay) * 0.08
    disc = outf - debt_pay - housing - utilities - groceries - transport
    c.setFont("Helvetica", 9.5)
    for lab, v in (("Housing / Rent", housing), ("Loan & Debt Payments", debt_pay),
                   ("Utilities", utilities), ("Groceries", groceries),
                   ("Transport", transport), ("Discretionary", disc)):
        c.setFillColorRGB(*MUTE); c.drawString(0.8 * inch, y, lab)
        c.setFillColorRGB(*INK); c.drawString(3.4 * inch, y, f"${v:,.2f}")
        y -= 15
    y -= 10
    _kv(c, y, "Closing Balance (30 Jun 2026)", f"${a['Avg Bank Balance (USD)']:,.2f}")
    c.setFont("Helvetica-Oblique", 7.5); c.setFillColorRGB(*MUTE)
    c.drawString(0.8 * inch, 0.7 * inch, "Synthetic document generated for prototype evaluation.")
    c.save()

def tax_slip(path, a, printed):
    """Prior-year statement of income — the third-party check on declared income."""
    c = canvas.Canvas(path, pagesize=LETTER)
    _header(c, "STATEMENT OF INCOME — TAX YEAR 2025", "Issued by employer to the tax authority  ·  Copy B, for employee records")
    y = H - 1.5 * inch
    y = _kv(c, y, "Employee", printed["name"])
    y = _kv(c, y, "Employer", a["Employer"])
    y = _kv(c, y, "Employment Status", a["Employment Status"])
    y = _kv(c, y, "Total Income Reported (Box 1)", f"${printed['tax_income']:,.2f}")
    y = _kv(c, y, "Tax Year", "2025")
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
            kind = rng.choice(["income_mismatch", "smoker_nondisclosure", "dob_mismatch",
                               "debt_understated", "income_deposit_mismatch", "tax_income_mismatch"])
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
        # financial-doc figures are derived AFTER injection so each packet carries
        # exactly the one injected conflict (tax slip mirrors the form declaration;
        # deposits mirror the payslip) — keeps detection measurement orthogonal
        printed["bank_deposit_monthly"] = round(printed["payslip_income"] / 12, 2)
        printed["bank_outflow_monthly"] = round(float(a["Monthly Expenses (USD)"]), 2)
        printed["tax_income"] = round(printed["form_income"], 2)
        if injected and injected[0] == "income_deposit_mismatch":
            printed["bank_deposit_monthly"] = round(printed["bank_deposit_monthly"] * float(rng.uniform(0.50, 0.70)), 2)
        elif injected and injected[0] == "tax_income_mismatch":
            printed["tax_income"] = round(printed["form_income"] * float(rng.uniform(0.60, 0.80)), 2)
        application_form(os.path.join(pdir, "application_form.pdf"), a, printed)
        payslip(os.path.join(pdir, "payslip.pdf"), a, printed)
        paramed_report(os.path.join(pdir, "paramed_report.pdf"), a, printed)
        bank_statement(os.path.join(pdir, "bank_statement.pdf"), a, printed, rng)
        tax_slip(os.path.join(pdir, "tax_slip.pdf"), a, printed)
        truth[aid] = {"printed": printed, "injected_conflicts": injected}
    with open(os.path.join(out_dir, "doc_ground_truth.json"), "w") as f:
        json.dump(truth, f, indent=1)
    return truth
