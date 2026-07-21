"""summaries.py — AI-generated case summaries via the Claude API, grounded
strictly in extracted fields (the brief's "design prompts to summarize
customer financial positions and highlight potential concerns").

Graceful degradation: if ANTHROPIC_API_KEY is not set (or a call fails),
callers fall back to the deterministic template in dashboard.case_summary,
so the pipeline never depends on network access or a paid key.

Enable with:  export ANTHROPIC_API_KEY=sk-ant-…  (and optionally
LLM_SUMMARY_LIMIT to cap how many cases are LLM-written per build).
"""
import json
import os

import httpx

API_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/") + "/v1/messages"
MODEL = os.environ.get("LLM_SUMMARY_MODEL", "claude-haiku-4-5-20251001")

SYSTEM_PROMPT = """You are an underwriting copilot writing a case summary for a licensed life-insurance underwriter.

Hard rules — violating any of these makes the summary unusable:
1. Use ONLY facts present in the CASE_FACTS JSON. Never invent, estimate, or infer numbers that are not in it.
2. Every number you write must appear verbatim in CASE_FACTS (formatting like $ and % is fine).
3. Cover, in order: (a) who the applicant is and what they're applying for; (b) medical/lifestyle risk picture; (c) financial position and the affordability screen result with the specific failing/strained indicators; (d) any cross-document conflicts or disclosures; (e) the system decision and why.
4. Flag concerns explicitly — an underwriter must not have to hunt for them.
5. 5–8 sentences of plain prose. No headers, no bullet lists, no hedging filler.
6. Do not recommend overriding the system decision; the human decides."""


def _case_facts(c):
    """The grounding payload: everything the model may cite, nothing else."""
    af = c.get("afford") or {}
    return {
        "applicant": {"name": c["name"], "age": c["age"], "sex": c.get("sex"),
                      "occupation": c["occupation"], "location": f"{c['city']}, {c['state']}"},
        "application": {"policy": c["policy"], "coverage_usd": c["coverage"],
                        "annual_income_usd": c["income"], "existing_coverage_usd": c.get("existing_cov", 0)},
        "medical": {"smoker": c["smoker"], "bmi": c["bmi"], "conditions": c["conditions"],
                    "blood_pressure": c.get("bp"), "family_history": bool(c.get("family"))},
        "financial": {"credit_score": c["credit"], "dti_pct": round(c["dti"] * 100, 1),
                      "monthly_expenses_usd": c.get("expenses"), "debt_usd": c.get("debt"),
                      "net_worth_usd": c.get("net_worth")},
        "affordability": {"verdict": af.get("label"), "premium_usd_yr": af.get("premium"),
                          "premium_pct_income": round(af.get("pti", 0) * 100, 1),
                          "coverage_multiple": af.get("cov_mult"), "cap": af.get("cov_cap"),
                          "disposable_usd_mo": af.get("disposable"),
                          "indicators": [{"label": i["label"], "status": i["status"], "value": i["value"]}
                                         for i in af.get("indicators", [])]},
        "screening": {"conflicts": c.get("conflicts", []), "unique_circumstances": c.get("unique")},
        "scores": {"composite": c["risk_score"], "rule": c["rule_score"], "ml": round(c["ml_score"], 1)},
        "decision": {"decision": c["decision"], "rate_class": c["rate_class"], "reasons": c["reasons"]},
    }


def llm_summary(case, timeout=30.0):
    """One grounded summary via the Claude API, or None if unavailable/failed."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        r = httpx.post(
            API_URL,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": MODEL, "max_tokens": 600, "system": SYSTEM_PROMPT,
                  "messages": [{"role": "user", "content":
                                "CASE_FACTS:\n" + json.dumps(_case_facts(case), indent=1)
                                + "\n\nWrite the case summary now."}]},
            timeout=timeout,
        )
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json().get("content", []))
        return text.strip() or None
    except Exception:
        return None   # caller falls back to the template summary


def _money(n):
    return "$" + format(int(round(float(n))), ",")


def template_summary(c, a_line, d_line):
    """Deterministic underwriter narrative, grounded strictly in case fields.
    The zero-cost, zero-network fallback for llm_summary — same job: an
    underwriter reads the exact situation in prose instead of reconstructing
    it from twenty fields."""
    risk = c["risk_score"]
    smoker = c["smoker"].lower()
    smoke_txt = ("a current smoker" if smoker == "smoker"
                 else "a former smoker" if "former" in smoker else "a non-smoker")
    cond = c["conditions"]
    cond_txt = ("no declared medical conditions" if str(cond).strip().lower() in ("none", "nan", "")
                else f"declared conditions of {cond}")
    band = ("green approval band" if risk < a_line
            else "yellow manual-review band" if risk < d_line else "red decline band")
    life = []
    if c.get("hazard") and c["hazard"] != "None":
        life.append(f"participates in {c['hazard'].lower()}")
    if c.get("violations"):
        life.append(f"has {c['violations']} driving violation(s) in the last three years")
    if c.get("alcohol") == "Heavy":
        life.append("reports heavy alcohol use")
    decl = c.get("decl") or {}
    decl_names = {"prior_decline": "a previously declined/rated insurance application",
                  "dangerous_driving": "careless or dangerous driving within five years",
                  "drug_use": "drug use or alcohol/drug counselling",
                  "criminal": "a criminal offence", "bankruptcy": "a declared bankruptcy",
                  "foreign_travel": "planned foreign travel", "weight_change": "a >10 lb weight change this year"}
    yes = [decl_names[k] for k, v in decl.items() if v and k in decl_names]
    if yes:
        life.append("answered Yes on the Section 6 declarations to " + ", ".join(yes))
    s = [
        f"{c['name']} is a {c['age']}-year-old {c['occupation']} applying for a "
        f"{c['policy']} policy with {_money(c['coverage'])} in requested coverage.",
        f"The applicant is {smoke_txt} with a BMI of {c['bmi']:.1f} and {cond_txt}"
        + (", and " + "; ".join(life) if life else "") + ".",
        f"Financially, the file shows a credit score of {c['credit']} and a "
        f"debt-to-income ratio of {c['dti'] * 100:.1f}%.",
        f"The composite risk score is {risk}/100 "
        f"(rule engine {c['rule_score']}, gradient boosting {c['ml_score']:.0f}), "
        f"placing the case in the {band}.",
    ]
    af = c.get("afford")
    if af:
        s.append(f"On financial viability, the estimated premium of {_money(af['premium'])}/yr "
                 f"is {af['pti']*100:.1f}% of income and the coverage sought is "
                 f"{af['cov_mult']:.1f}× income — the affordability screen reads {af['label']}."
                 + (f" {af['reasons'][0]}." if af["verdict"] == "fail" and af.get("reasons") else ""))
    if c.get("unique"):
        s.append(f"The applicant disclosed unique circumstances — “{c['unique']}” — "
                 f"which routes the file to a human underwriter for whole-person review.")
    if c["conflicts"]:
        det = "; ".join(f"{k['severity']} {k['type'].replace('_', ' ')} — {k['description']}"
                        for k in c["conflicts"])
        s.append(f"The cross-document screen flagged {len(c['conflicts'])} conflict(s): {det}. "
                 f"These discrepancies independently support routing the file to a human underwriter.")
    elif c.get("has_docs"):
        s.append("The cross-document conflict screen found no discrepancies across the packet.")
    s.append(f"System decision: {c['decision']} — {c['rate_class']} "
             f"({'; '.join(c['reasons'])}).")
    return " ".join(s)


def summary_for(case, a_line, d_line):
    """The case summary the underwriter reads: Claude-written when a key is
    present (grounded by SYSTEM_PROMPT's hard rules), template otherwise."""
    return llm_summary(case) or template_summary(case, a_line, d_line)


def groundedness_check(summary, case):
    """Spot-check: every dollar figure in the summary must trace to a case fact.
    Returns (ok, untraceable_numbers) — the Week-4 groundedness metric."""
    import re
    facts = json.dumps(_case_facts(case))
    fact_nums = set(re.findall(r"\d[\d,]*\.?\d*", facts.replace(",", "")))
    out = []
    for tok in re.findall(r"\$?([\d,]+(?:\.\d+)?)", summary):
        n = tok.replace(",", "")
        if len(n) >= 3 and n not in fact_nums and n.rstrip("0").rstrip(".") not in fact_nums:
            out.append(tok)
    return (not out, out)
