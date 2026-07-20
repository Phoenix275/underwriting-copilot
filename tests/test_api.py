"""REST API: score → persist → retrieve → human decision, on a temp DB."""
import json

import joblib
import pytest
from fastapi.testclient import TestClient

import api
import datagen
import engine
import published_models

# a stand-in for output/portfolio.json — the batch book the workbench reads
PORTFOLIO_CASE = {"id": "APP-9001", "name": "Batch Betty", "risk_score": 41,
                  "decision": "MANUAL REVIEW", "verdict": "yellow"}


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    df = datagen.generate(400, seed=11)
    df["External Risk Prior"] = 0.5
    df["Published CVD Prior"] = published_models.prior_from_df(df)
    models, _ = engine.train_models(df)
    joblib.dump({"models": models, "prior_models": [], "features": engine.FEATURES},
                tmp / "models.joblib")

    (tmp / "portfolio.json").write_text(json.dumps({"cases": [PORTFOLIO_CASE]}))
    (tmp / "report.json").write_text(json.dumps(
        {"generated_at": "2026-01-01 00:00", "decisioning": {"thresholds": {"a_line": 35, "d_line": 62}}}))

    api.MODELS_PATH = str(tmp / "models.joblib")
    api.REPORT_PATH = str(tmp / "report.json")
    api.PORTFOLIO_PATH = str(tmp / "portfolio.json")
    api.DB_PATH = str(tmp / "test.db")
    with TestClient(api.app) as c:
        yield c


def test_health(client):
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["models_loaded"] is True


def test_score_clean_applicant(client):
    r = client.post("/score", json={"name": "Clean Carl", "age": 32, "annual_income": 95000,
                                    "coverage_requested": 400000, "monthly_expenses": 2500,
                                    "existing_debt": 10000})
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] in ("APPROVE", "MANUAL REVIEW", "DECLINE")
    assert body["affordability"]["label"] == "AFFORDABLE"
    assert body["case_id"].startswith("API-")


def test_score_overinsured_applicant_refers_to_financial_uw(client):
    r = client.post("/score", json={"name": "Over Insured", "age": 31, "annual_income": 52000,
                                    "coverage_requested": 1500000, "monthly_expenses": 2905,
                                    "existing_debt": 30000})
    body = r.json()
    assert body["affordability"]["label"] == "NOT JUSTIFIED"
    assert body["decision"] == "MANUAL REVIEW"
    assert body["rate_class"] == "Referred — Financial Underwriting Review"


def test_cases_persist_and_accept_human_decision(client):
    cases = client.get("/cases").json()
    assert len(cases) >= 2
    cid = cases[0]["case_id"]
    r = client.post(f"/cases/{cid}/decision",
                    json={"action": "APPROVED", "rationale": "Financials verified on call",
                          "decided_by": "mrivera"})
    assert r.status_code == 200
    detail = client.get(f"/cases/{cid}").json()
    assert detail["human_decisions"][0]["action"] == "APPROVED"


def test_unknown_case_404s(client):
    assert client.get("/cases/API-nope").status_code == 404


# ---- the workbench's data contract ------------------------------------------

def test_portfolio_serves_the_book_and_the_report(client):
    """The front end reads both together — cases from one run and thresholds
    from another would silently mis-score."""
    body = client.get("/portfolio").json()
    assert [c["id"] for c in body["cases"]] == ["APP-9001"]
    assert body["report"]["decisioning"]["thresholds"]["a_line"] == 35
    assert body["served_at"]


def test_batch_case_is_addressable_and_decidable(client):
    """A referral an underwriter actually works comes from the batch book, not
    from POST /score, so those ids must accept a recorded decision."""
    detail = client.get("/cases/APP-9001").json()
    assert detail["source"] == "portfolio"
    assert detail["result"]["name"] == "Batch Betty"

    r = client.post("/cases/APP-9001/decision",
                    json={"action": "INFO_REQUESTED", "rationale": "Bank statements requested",
                          "decided_by": "ewong"})
    assert r.status_code == 200

    trail = client.get("/cases/APP-9001/decisions").json()
    assert trail[-1]["action"] == "INFO_REQUESTED"
    assert trail[-1]["decided_by"] == "ewong"


def test_decision_on_unknown_case_404s(client):
    r = client.post("/cases/APP-0000/decision",
                    json={"action": "APPROVED", "rationale": "no such case", "decided_by": "x"})
    assert r.status_code == 404


def test_cors_allows_the_workbench_origin(client):
    """The workbench is always a different origin from the API — a bundle on
    Pages or in a Streamlit iframe cannot read it without this header."""
    r = client.get("/portfolio", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_validation_rejects_bad_input(client):
    assert client.post("/score", json={"age": 200}).status_code == 422
    assert client.post("/score", json={"smoker_status": "Sometimes"}).status_code == 422
