"""REST API: score → persist → retrieve → human decision, on a temp DB."""
import joblib
import pytest
from fastapi.testclient import TestClient

import api
import datagen
import engine
import published_models


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("api")
    df = datagen.generate(400, seed=11)
    df["External Risk Prior"] = 0.5
    df["Published CVD Prior"] = published_models.prior_from_df(df)
    models, _ = engine.train_models(df)
    joblib.dump({"models": models, "prior_models": [], "features": engine.FEATURES},
                tmp / "models.joblib")
    api.MODELS_PATH = str(tmp / "models.joblib")
    api.REPORT_PATH = str(tmp / "missing.json")
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


def test_validation_rejects_bad_input(client):
    assert client.post("/score", json={"age": 200}).status_code == 422
    assert client.post("/score", json={"smoker_status": "Sometimes"}).status_code == 422
