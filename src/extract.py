"""extract.py — Document extraction layer.

Extractor interface with two implementations:
  LocalTextExtractor  — pdfplumber + label-anchored parsing (runs anywhere;
                        used for the MVP since our synthetic PDFs are text PDFs)
  DocumentAIExtractor — adapter stub for Google Document AI on GCP; same
                        output schema, so swapping it in later is one line.

Output schema per applicant (extracted_record):
  name, form_dob, paramed_dob, form_income, payslip_income,
  form_debt, bureau_debt, form_tobacco_yes, cotinine,
  height_cm, weight_kg, blood_pressure, cholesterol, conditions_yes,
  family_history_yes, bank_deposit_monthly, bank_outflow_monthly, tax_income
"""
import re
import pdfplumber


def _grab(text, label, pattern=r"([^\n]+)"):
    m = re.search(re.escape(label.upper()) + r"\s*\n" + pattern, text)
    return m.group(1).strip() if m else None

def _money(s):
    if s is None: return None
    m = re.search(r"[\d,]+(?:\.\d+)?", s)
    return float(m.group(0).replace(",", "")) if m else None

def _yesno_answer(text, qnum):
    """Return True/False for which checkbox is bold-selected. In our PDFs the
    selected box is filled; pdfplumber sees both labels, so we detect via the
    rects: filled rect x-position maps to Yes (x~68pt) vs No (x~126pt)."""
    return None  # resolved in extract_application via rects


class LocalTextExtractor:
    name = "local-pdfplumber"

    def extract_application(self, path):
        out = {}
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text() or ""
            lines = text.split("\n")
            def after(label):
                for i, ln in enumerate(lines):
                    if ln.upper().startswith(label.upper()):
                        return lines[i + 1] if i + 1 < len(lines) else None
                return None
            # two-column rows: value line holds both columns
            nd = after("FULL NAME") or ""
            dm = re.search(r"(\d{4}-\d{2}-\d{2})\s*$", nd)
            out["form_dob"] = dm.group(1) if dm else None
            out["name"] = nd[:dm.start()].strip() if dm else (nd.strip() or None)
            inc = after("DECLARED ANNUAL INCOME") or ""
            nums = re.findall(r"[\d,]+(?:\.\d+)?", inc)
            out["form_income"] = float(nums[0].replace(",", "")) if nums else None
            debt = after("DECLARED TOTAL DEBT") or ""
            nums = re.findall(r"[\d,]+(?:\.\d+)?", debt)
            out["form_debt"] = float(nums[0].replace(",", "")) if nums else None
            # yes/no questions: filled checkbox rects. Question order fixed: 4a,4b,4c,4d
            filled = [r for r in page.rects if r.get("fill")]
            # pair each question line's y with nearest filled rect; Yes box x ≈ 68.4pt, No ≈ 126pt
            answers = {}
            for q in ["4a.", "4b.", "4c.", "4d."]:
                qw = [w for w in page.extract_words() if w["text"] == q]
                if not qw: continue
                qy = qw[0]["top"]
                cands = [r for r in filled if qy < (page.height - r["y0"]) < qy + 40]
                if cands:
                    r = min(cands, key=lambda r: (page.height - r["y0"]) - qy)
                    answers[q[:2]] = r["x0"] < 100  # Yes box is the left one
            out["form_tobacco_yes"] = answers.get("4a")
            out["conditions_yes"] = answers.get("4b")
            out["family_history_yes"] = answers.get("4c")
            # detail line after 4b holds conditions text
            m = re.search(r"4b\..*?If yes, provide details:\n([^\n]+)", text, re.S)
            out["conditions_detail"] = m.group(1).strip() if (m and out.get("conditions_yes")) else None
        return out

    def extract_payslip(self, path):
        with pdfplumber.open(path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return {
            "payslip_name": _grab(text, "Employee"),
            "payslip_income": _money(_grab(text, "Annualized Gross Income")),
            "employment_status": _grab(text, "Employment Status"),
        }

    def extract_paramed(self, path):
        with pdfplumber.open(path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        hw = _grab(text, "Height / Weight") or ""
        hm = re.search(r"([\d.]+)\s*cm\s*/\s*([\d.]+)\s*kg", hw)
        return {
            "paramed_dob": _grab(text, "Date of Birth (per ID)"),
            "height_cm": float(hm.group(1)) if hm else None,
            "weight_kg": float(hm.group(2)) if hm else None,
            "blood_pressure": _grab(text, "Blood Pressure"),
            "cholesterol": _money(_grab(text, "Total Cholesterol")),
            "cotinine": (_grab(text, "Cotinine (nicotine metabolite)") or "").split()[0] or None,
            "bureau_debt": _money(_grab(text, "Credit-Bureau Debt Figure (attached consumer report)")),
        }

    def extract_bank_statement(self, path):
        with pdfplumber.open(path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return {
            "bank_deposit_monthly": _money(_grab(text, "Average Monthly Deposits")),
            "bank_outflow_monthly": _money(_grab(text, "Average Monthly Outflows")),
            "bank_closing_balance": _money(_grab(text, "Closing Balance (30 Jun 2026)")),
        }

    def extract_tax_slip(self, path):
        with pdfplumber.open(path) as pdf:
            text = pdf.pages[0].extract_text() or ""
        return {
            "tax_income": _money(_grab(text, "Total Income Reported (Box 1)")),
            "tax_year": _grab(text, "Tax Year"),
        }

    def extract_packet(self, packet_dir):
        import os
        rec = {}
        rec.update(self.extract_application(os.path.join(packet_dir, "application_form.pdf")))
        rec.update(self.extract_payslip(os.path.join(packet_dir, "payslip.pdf")))
        rec.update(self.extract_paramed(os.path.join(packet_dir, "paramed_report.pdf")))
        for fname, fn in (("bank_statement.pdf", self.extract_bank_statement),
                          ("tax_slip.pdf", self.extract_tax_slip)):
            p = os.path.join(packet_dir, fname)
            if os.path.exists(p):   # packets generated before the financial docs existed
                rec.update(fn(p))
        return rec


class DocumentAIExtractor:
    """Adapter for Google Document AI (Form Parser / Custom Extractor).

    On GCP: create a processor, then implement extract_packet() to call
    documentai.DocumentProcessorServiceClient.process_document per file and
    map entities into the same schema LocalTextExtractor returns. The rest
    of the pipeline is unchanged.
    """
    name = "google-document-ai"

    def __init__(self, project_id=None, location="us", processor_id=None):
        self.project_id, self.location, self.processor_id = project_id, location, processor_id

    def extract_packet(self, packet_dir):
        raise NotImplementedError("Wire to Document AI on GCP — see class docstring.")
