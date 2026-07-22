"""api.py — REST API for the Underwriting Copilot (FastAPI + SQLite).

Satisfies the brief's "REST APIs" + "SQL Database" tool-stack items:
  POST /score                submit one applicant → full engine verdict, persisted
  GET  /cases                every scored case (SQLite-backed, survives restarts)
  GET  /cases/{case_id}      one case
  POST /cases/{case_id}/decision   record the human underwriter's decision + rationale
  GET  /health               liveness + model provenance

Run:  uvicorn api:app --app-dir src --reload      (after `python src/run_pipeline.py`
has produced output/models.joblib — the API refuses to guess without trained models).
"""
import json
import os
import sqlite3
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import engine
import external_data
import published_models

ROOT = os.path.join(os.path.dirname(__file__), "..")
MODELS_PATH = os.path.join(ROOT, "output", "models.joblib")
REPORT_PATH = os.path.join(ROOT, "output", "evaluation_report.json")
PORTFOLIO_PATH = os.path.join(ROOT, "output", "portfolio.json")
DB_PATH = os.environ.get("COPILOT_DB", os.path.join(ROOT, "data", "copilot.db"))

_bundle = None
_thresholds = (engine.APPROVE_LINE, engine.DECLINE_LINE)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _load()
    _init_db()
    yield


app = FastAPI(title="Underwriting Copilot API", version="0.6",
              description="AI-assisted financial viability assessment — dual risk engine + affordability screen",
              lifespan=lifespan)

# The workbench is a static bundle that may be served from Cloudflare Pages,
# GitHub Pages, an embedded iframe or localhost, so it is always a different origin from this
# API. Origins are read from COPILOT_ALLOWED_ORIGINS (comma separated); the
# default is local development only — a deployment must name its own origins
# rather than inherit a wildcard.
_origins = [o.strip() for o in os.environ.get(
    "COPILOT_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:4173,http://localhost:8899",
).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _load():
    global _bundle, _thresholds
    if not os.path.exists(MODELS_PATH):
        raise RuntimeError("output/models.joblib not found — run `python src/run_pipeline.py` first")
    _bundle = joblib.load(MODELS_PATH)
    if os.path.exists(REPORT_PATH):
        thr = json.load(open(REPORT_PATH)).get("decisioning", {}).get("thresholds", {})
        _thresholds = (thr.get("a_line", engine.APPROVE_LINE), thr.get("d_line", engine.DECLINE_LINE))


@contextmanager
def _db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _init_db():
    with _db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS cases(
            case_id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
            payload TEXT NOT NULL, result TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS decisions(
            id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL REFERENCES cases(case_id),
            action TEXT NOT NULL, rationale TEXT NOT NULL,
            decided_by TEXT NOT NULL, decided_at TEXT NOT NULL)""")


class Applicant(BaseModel):
    """One application. Field names/defaults mirror the pipeline's schema."""
    name: str = "API Applicant"
    sex: str = Field("M", pattern="^[MF]$")
    age: int = Field(40, ge=18, le=85)
    occupation: str = "Unspecified"
    annual_income: float = Field(60000, gt=0)
    monthly_expenses: float = Field(2750, ge=0)
    existing_debt: float = Field(20000, ge=0)
    credit_score: int = Field(715, ge=300, le=850)
    coverage_requested: float = Field(300000, gt=0)
    existing_coverage: float = Field(0, ge=0)
    policy_type: str = "Term Life - 20yr"
    smoker_status: str = Field("Non-smoker", pattern="^(Smoker|Former smoker|Non-smoker)$")
    bmi: float = Field(25.0, ge=10, le=70)
    systolic_bp: int = Field(120, ge=70, le=250)
    cholesterol: int = Field(200, ge=80, le=500)
    conditions: str = "None"
    family_history: bool = False
    hazardous_activities: str = "None"
    driving_violations: int = Field(0, ge=0, le=10)
    alcohol_use: str = Field("Moderate", pattern="^(None|Moderate|Heavy)$")
    prior_decline: bool = False
    dangerous_driving: bool = False
    drug_use: bool = False
    criminal_record: bool = False
    bankruptcy: bool = False
    foreign_travel: bool = False
    weight_change: bool = False
    unique_circumstances: Optional[str] = None


class HumanDecision(BaseModel):
    action: str = Field(pattern="^(APPROVED|DECLINED|INFO_REQUESTED)$")
    rationale: str = Field(min_length=5)
    decided_by: str = Field(min_length=1)


def _to_row(a: Applicant) -> pd.Series:
    return pd.Series({
        "Full Name": a.name, "Sex": a.sex, "Age": a.age, "Occupation": a.occupation,
        "Annual Income (USD)": a.annual_income, "Monthly Expenses (USD)": a.monthly_expenses,
        "Existing Debt (USD)": a.existing_debt, "Credit Score": a.credit_score,
        "Debt-to-Income Ratio": round(a.existing_debt / a.annual_income, 3),
        "Coverage Amount Requested (USD)": a.coverage_requested,
        "Existing Coverage (USD)": a.existing_coverage,
        "Policy Type Requested": a.policy_type, "Smoker Status": a.smoker_status,
        "BMI": a.bmi, "Blood Pressure": f"{a.systolic_bp}/{int(a.systolic_bp * 0.64)}",
        "Cholesterol (mg/dL)": a.cholesterol, "Existing Conditions": a.conditions or "None",
        "Family History Flag": int(a.family_history),
        "Hazardous Activities": a.hazardous_activities or "None",
        "Driving Violations (3yr)": a.driving_violations, "Alcohol Use": a.alcohol_use,
        "Prior Application Declined": int(a.prior_decline),
        "Dangerous Driving (5yr)": int(a.dangerous_driving),
        "Drug/Alcohol Counselling (5yr)": int(a.drug_use),
        "Criminal Record": int(a.criminal_record),
        "Bankruptcy Declared": int(a.bankruptcy),
        "Foreign Travel Planned": int(a.foreign_travel),
        "Weight Change 10lb (12mo)": int(a.weight_change),
    })


@app.post("/score")
def score(applicant: Applicant):
    row = _to_row(applicant)
    df1 = pd.DataFrame([row])
    df1["External Risk Prior"] = external_data.prior_scores(_bundle["prior_models"], df1)
    df1["Published CVD Prior"] = published_models.prior_from_df(df1)
    row = df1.iloc[0]

    rule_s, factors = engine.rule_score(row)
    _, gb = engine.ml_scores(_bundle["models"], df1)
    ml_s = float(gb[0])
    afford = engine.afford_from_row(row)
    a_line, d_line = _thresholds
    decision = engine.decide(rule_s, ml_s, conflicts=[],   # single-app scoring has no cross-doc packet
                             unique=applicant.unique_circumstances,
                             a_line=a_line, d_line=d_line, afford=afford)

    case_id = f"API-{int(time.time() * 1000)}"
    result = {"case_id": case_id, "rule_score": rule_s,
              "rule_factors": [{"factor": f[0], "detail": f[1], "points": f[2]} for f in factors],
              "ml_score": round(ml_s, 1),
              "external_prior": round(float(row["External Risk Prior"]), 4),
              "published_cvd_prior": round(float(row["Published CVD Prior"]), 4),
              "affordability": afford, "thresholds": {"approve_below": a_line, "decline_at": d_line},
              **decision,
              "note": "Cross-document conflict screening requires a full PDF packet and is not applied to single-record API scoring."}
    with _db() as con:
        con.execute("INSERT INTO cases VALUES (?,?,?,?)",
                    (case_id, time.strftime("%Y-%m-%d %H:%M:%S"),
                     applicant.model_dump_json(), json.dumps(result)))
    return result


@app.get("/portfolio")
def portfolio():
    """The scored book and its evaluation report — what the workbench reads.

    This is the pipeline's output rather than anything in SQLite: the 200 cases
    come from a batch run, while the `cases` table below holds applications
    submitted through POST /score. Serving it here is what lets the front end
    run against a live backend instead of a bundle frozen at build time.
    """
    for path in (PORTFOLIO_PATH, REPORT_PATH):
        if not os.path.exists(path):
            raise HTTPException(
                503,
                f"{os.path.relpath(path, ROOT)} not found — run `python src/run_pipeline.py` first",
            )
    book = json.load(open(PORTFOLIO_PATH))
    return {
        "cases": book["cases"],
        "report": json.load(open(REPORT_PATH)),
        "served_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/cases")
def cases():
    with _db() as con:
        rows = con.execute("SELECT case_id, created_at, result FROM cases ORDER BY created_at DESC").fetchall()
    return [{"case_id": r["case_id"], "created_at": r["created_at"],
             **{k: json.loads(r["result"]).get(k) for k in ("decision", "rate_class", "risk_score")}}
            for r in rows]


@app.get("/cases/{case_id}")
def case(case_id: str):
    with _db() as con:
        r = con.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        decs = con.execute("SELECT action, rationale, decided_by, decided_at FROM decisions "
                           "WHERE case_id=? ORDER BY id", (case_id,)).fetchall()
    if r:
        return {"case_id": r["case_id"], "created_at": r["created_at"],
                "source": "api", "applicant": json.loads(r["payload"]),
                "result": json.loads(r["result"]),
                "human_decisions": [dict(d) for d in decs]}

    # fall back to the batch book so every id the workbench can show is
    # addressable here, not only the ones submitted through POST /score
    if os.path.exists(PORTFOLIO_PATH):
        for c in json.load(open(PORTFOLIO_PATH))["cases"]:
            if c["id"] == case_id:
                return {"case_id": case_id, "created_at": None, "source": "portfolio",
                        "result": c, "human_decisions": [dict(d) for d in decs]}
    raise HTTPException(404, "case not found")


def _portfolio_ids() -> set:
    """Case ids from the batch run. Read per call rather than cached so a fresh
    pipeline run is picked up without restarting the API."""
    if not os.path.exists(PORTFOLIO_PATH):
        return set()
    return {c["id"] for c in json.load(open(PORTFOLIO_PATH))["cases"]}


def _case_exists(con, case_id: str) -> bool:
    if con.execute("SELECT 1 FROM cases WHERE case_id=?", (case_id,)).fetchone():
        return True
    # a referral an underwriter actually works comes from the batch book, not
    # from POST /score, so those ids have to be recordable against too
    return case_id in _portfolio_ids()


@app.post("/cases/{case_id}/decision")
def record_decision(case_id: str, d: HumanDecision):
    with _db() as con:
        if not _case_exists(con, case_id):
            raise HTTPException(404, "case not found")
        con.execute("INSERT INTO decisions(case_id, action, rationale, decided_by, decided_at) "
                    "VALUES (?,?,?,?,?)",
                    (case_id, d.action, d.rationale, d.decided_by,
                     time.strftime("%Y-%m-%d %H:%M:%S")))
    return {"case_id": case_id, "recorded": d.action}


@app.get("/cases/{case_id}/decisions")
def case_decisions(case_id: str):
    """The human decision trail for one case — the audit record every AI
    governance regime in the model card asks for."""
    with _db() as con:
        rows = con.execute(
            "SELECT action, rationale, decided_by, decided_at FROM decisions "
            "WHERE case_id=? ORDER BY id", (case_id,)).fetchall()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    with _db() as con:
        n = con.execute("SELECT COUNT(*) c FROM cases").fetchone()["c"]
    return {"status": "ok", "models_loaded": _bundle is not None,
            "prior_models": len(_bundle["prior_models"]) if _bundle else 0,
            "thresholds": {"approve_below": _thresholds[0], "decline_at": _thresholds[1]},
            "cases_persisted": n}
