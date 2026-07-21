"""Conflict checks, rule engine, decision logic, threshold search."""
import engine


BASE_REC = {
    "name": "Test Person", "form_dob": "1990-01-01", "paramed_dob": "1990-01-01",
    "form_income": 80000.0, "payslip_income": 80000.0,
    "form_debt": 20000.0, "bureau_debt": 20000.0,
    "form_tobacco_yes": False, "cotinine": "NEGATIVE",
    "bank_deposit_monthly": 80000.0 / 12, "bank_outflow_monthly": 3000.0,
    "tax_income": 80000.0,
}


def _conflicts(**over):
    return {c["type"] for c in engine.detect_conflicts({**BASE_REC, **over})}


class TestConflictChecks:
    def test_clean_packet_has_no_conflicts(self):
        assert _conflicts() == set()

    def test_income_mismatch_fires_above_15pct(self):
        assert "income_mismatch" in _conflicts(form_income=100000.0)

    def test_income_within_tolerance_passes(self):
        assert "income_mismatch" not in _conflicts(form_income=88000.0)  # 10% gap

    def test_smoker_nondisclosure(self):
        assert "smoker_nondisclosure" in _conflicts(cotinine="POSITIVE")

    def test_declared_smoker_with_positive_lab_is_consistent(self):
        assert _conflicts(form_tobacco_yes=True, cotinine="POSITIVE") == set()

    def test_dob_mismatch(self):
        assert "dob_mismatch" in _conflicts(paramed_dob="1990-01-05")

    def test_debt_understated_minor(self):
        found = engine.detect_conflicts({**BASE_REC, "bureau_debt": 50000.0})
        m = [c for c in found if c["type"] == "debt_understated"]
        assert m and m[0]["severity"] == "minor"

    def test_income_deposit_mismatch(self):
        assert "income_deposit_mismatch" in _conflicts(bank_deposit_monthly=4000.0)

    def test_tax_income_mismatch(self):
        assert "tax_income_mismatch" in _conflicts(tax_income=60000.0)

    def test_missing_fields_do_not_crash_or_fire(self):
        rec = {k: v for k, v in BASE_REC.items() if k not in ("tax_income", "bank_deposit_monthly")}
        types = {c["type"] for c in engine.detect_conflicts(rec)}
        assert "tax_income_mismatch" not in types
        assert "income_deposit_mismatch" not in types


ROW = {
    "Age": 25, "BMI": 24.0, "Smoker Status": "Non-smoker", "Existing Conditions": "None",
    "Family History Flag": 0, "Debt-to-Income Ratio": 0.15, "Credit Score": 780,
    "Hazardous Activities": "None", "Driving Violations (3yr)": 0, "Alcohol Use": "None",
    "Prior Application Declined": 0, "Dangerous Driving (5yr)": 0,
    "Drug/Alcohol Counselling (5yr)": 0, "Criminal Record": 0, "Bankruptcy Declared": 0,
    "Foreign Travel Planned": 0, "Weight Change 10lb (12mo)": 0,
}


class TestRuleEngine:
    def test_clean_applicant_scores_zero(self):
        total, _ = engine.rule_score(ROW)
        assert total == 0

    def test_smoker_weight_matches_calibration(self):
        # weight is round(28 * ln(2.37)) from real cotinine-confirmed mortality
        import calibration
        total, _ = engine.rule_score({**ROW, "Smoker Status": "Smoker"})
        assert total == calibration.points("smoker_current") == 24

    def test_diabetes_weighs_more_than_other_conditions(self):
        # diabetes anchored to ERFC 1.80x, generic condition to NHANES 1.40x
        diab, _ = engine.rule_score({**ROW, "Existing Conditions": "Type 2 Diabetes"})
        other, _ = engine.rule_score({**ROW, "Existing Conditions": "Asthma"})
        assert diab > other
        assert diab == 16 and other == 9

    def test_score_capped_at_100(self):
        worst = {**ROW, "Age": 60, "BMI": 44, "Smoker Status": "Smoker",
                 "Existing Conditions": "Type 2 Diabetes, Hypertension, Sleep Apnea",
                 "Family History Flag": 1, "Debt-to-Income Ratio": 0.9, "Credit Score": 500,
                 "Hazardous Activities": "Skydiving", "Driving Violations (3yr)": 4,
                 "Alcohol Use": "Heavy", "Prior Application Declined": 1,
                 "Dangerous Driving (5yr)": 1, "Drug/Alcohol Counselling (5yr)": 1,
                 "Criminal Record": 1, "Bankruptcy Declared": 1, "Foreign Travel Planned": 1,
                 "Weight Change 10lb (12mo)": 1}
        total, _ = engine.rule_score(worst)
        assert total == 100


class TestDecide:
    def test_low_clean_score_approves(self):
        d = engine.decide(10, 12, [], a_line=50, d_line=90)
        assert d["decision"] == "APPROVE" and d["referred"] is False

    def test_misrepresentation_declines_even_with_low_score(self):
        conf = [{"type": "smoker_nondisclosure", "severity": "major", "description": ""}]
        d = engine.decide(5, 5, conf, a_line=50, d_line=90)
        assert d["decision"] == "DECLINE" and "Misrepresentation" in d["rate_class"]

    def test_score_at_decline_line_declines(self):
        d = engine.decide(95, 95, [], a_line=50, d_line=90)
        assert d["decision"] == "DECLINE"

    def test_model_disagreement_refers(self):
        d = engine.decide(10, 45, [], a_line=50, d_line=90)
        assert d["decision"] == "MANUAL REVIEW"

    def test_unique_circumstances_refer(self):
        d = engine.decide(5, 5, [], unique="Recent job change", a_line=50, d_line=90)
        assert d["decision"] == "MANUAL REVIEW"

    def test_failed_affordability_refers_to_financial_underwriting(self):
        prem = engine.estimate_premium(31, "Non-smoker", 1500000, "Term Life - 20yr")
        afford = engine.affordability_assess(52000, 2905, 30000, 1500000, 0, 31, prem)
        assert afford["verdict"] == "fail"
        d = engine.decide(10, 12, [], a_line=50, d_line=90, afford=afford)
        assert d["decision"] == "MANUAL REVIEW"
        assert d["rate_class"] == "Referred — Financial Underwriting Review"

    def test_only_yellow_counts_as_referred(self):
        assert engine.decide(95, 95, [], a_line=50, d_line=90)["referred"] is False
        assert engine.decide(60, 60, [], a_line=50, d_line=90)["referred"] is True


class TestOptimizeThresholds:
    def test_reports_holdout_stats_and_valid_lines(self):
        import numpy as np
        rng = np.random.default_rng(0)
        comp = rng.integers(0, 100, 2000)
        labels = (comp + rng.normal(0, 18, 2000) > 60).astype(int)
        clean = rng.random(2000) < 0.7
        a, d, stats = engine.optimize_thresholds(comp, labels, clean)
        # the search is unconstrained now, so the lines can land anywhere valid
        assert 1 <= a < d <= 100
        assert stats["evaluation"].startswith("holdout")
        assert 0 <= stats["stp_est"] <= 1

    def test_small_sample_falls_back_to_in_sample(self):
        a, d, stats = engine.optimize_thresholds([10, 80], [0, 1], [True, True])
        assert "in-sample" in stats["evaluation"]

    def test_unconstrained_default_beats_a_capped_search(self):
        # the default search is uncapped, so its STP must be >= any constrained one
        import numpy as np
        rng = np.random.default_rng(2)
        comp = rng.integers(0, 100, 3000)
        labels = (comp + rng.normal(0, 16, 3000) > 55).astype(int)
        clean = rng.random(3000) < 0.6
        _, _, free = engine.optimize_thresholds(comp, labels, clean)
        _, _, capped = engine.optimize_thresholds(comp, labels, clean, decline_prec_min=0.85)
        assert free["stp_est"] >= capped["stp_est"]

    def test_lower_decline_floor_raises_stp(self):
        # the decline floor is the strongest STP lever: letting the auto-decline
        # line reach further down the score should never *reduce* straight-through
        import numpy as np
        rng = np.random.default_rng(1)
        comp = rng.integers(0, 100, 3000)
        labels = (comp + rng.normal(0, 16, 3000) > 55).astype(int)
        clean = rng.random(3000) < 0.6
        _, d_hi, hi = engine.optimize_thresholds(comp, labels, clean, decline_floor=60)
        _, d_lo, lo = engine.optimize_thresholds(comp, labels, clean, decline_floor=40)
        assert d_lo <= d_hi
        assert lo["stp_est"] >= hi["stp_est"]


class TestReferralRouting:
    def _refer(self, **kw):
        base = dict(rule_s=40, ml_s=45, composite=42, conflicts=[], unique=None,
                    afford={"verdict": "pass"}, a_line=25, d_line=26)
        base.update(kw)
        return engine.route_referral(**base)

    def test_harder_cases_route_to_senior(self):
        easy = self._refer()
        hard = self._refer(
            conflicts=[{"type": "smoker_nondisclosure", "severity": "major"}],
            unique="Recent job change", afford={"verdict": "fail"})
        assert hard["difficulty"] > easy["difficulty"]
        assert hard["assigned_desk"] == "senior"
        assert hard["difficulty_drivers"]  # names why it is hard

    def test_desk_thresholds_are_monotonic(self):
        assert engine.assign_underwriter(10) == "analyst"
        assert engine.assign_underwriter(28) == "review"
        assert engine.assign_underwriter(60) == "senior"
