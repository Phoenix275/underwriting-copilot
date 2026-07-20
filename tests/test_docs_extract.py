"""Docgen → extraction round trip: the PDFs we write must read back exactly,
and every injected conflict type must be detected with no false positives."""
import numpy as np
import pytest

import datagen
import docgen
import engine
from extract import LocalTextExtractor

N = 14  # applicants per round-trip run (5 PDFs each)


@pytest.fixture(scope="module")
def packets(tmp_path_factory):
    out = tmp_path_factory.mktemp("packets")
    df = datagen.generate(N, seed=99)
    truth = docgen.generate_packets(df, str(out), conflict_rate=0.5, seed=3)
    ex = LocalTextExtractor()
    recs = {aid: ex.extract_packet(str(out / aid)) for aid in df["Applicant ID"]}
    return df, truth, recs


FIELDS = ["name", "form_dob", "paramed_dob", "form_income", "payslip_income",
          "form_debt", "bureau_debt", "form_tobacco_yes", "cotinine",
          "bank_deposit_monthly", "bank_outflow_monthly", "tax_income"]


def test_all_five_documents_extract_all_fields(packets):
    _, truth, recs = packets
    for aid, rec in recs.items():
        for f in FIELDS:
            got, want = rec.get(f), truth[aid]["printed"][f]
            if isinstance(want, float):
                assert got is not None and abs(float(got) - want) < 0.51, (aid, f, got, want)
            elif f == "cotinine":
                assert str(got).upper() == str(want).upper(), (aid, f)
            elif f == "form_tobacco_yes":
                assert bool(got) == bool(want), (aid, f)
            else:
                assert str(got).strip() == str(want).strip(), (aid, f)


def test_injected_conflicts_are_detected_with_no_false_positives(packets):
    _, truth, recs = packets
    for aid, rec in recs.items():
        detected = {c["type"] for c in engine.detect_conflicts(rec)}
        injected = set(truth[aid]["injected_conflicts"])
        assert detected == injected, (aid, detected, injected)


def test_conflict_rate_zero_produces_clean_packets(tmp_path):
    df = datagen.generate(4, seed=7)
    truth = docgen.generate_packets(df, str(tmp_path), conflict_rate=0.0, seed=1)
    assert all(not t["injected_conflicts"] for t in truth.values())


def test_packet_contains_five_pdfs(packets, tmp_path_factory):
    df, truth, _ = packets
    root = tmp_path_factory.getbasetemp() / "packets0"
    aid = df["Applicant ID"].iloc[0]
    names = sorted(p.name for p in (root / aid).glob("*.pdf"))
    assert names == ["application_form.pdf", "bank_statement.pdf",
                     "paramed_report.pdf", "payslip.pdf", "tax_slip.pdf"]
