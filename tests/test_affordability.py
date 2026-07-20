"""Premium estimator + 4-indicator affordability screen."""
import engine


class TestPremium:
    def test_older_applicants_pay_more(self):
        assert engine.estimate_premium(55, "Non-smoker", 300000, "Term Life - 20yr") \
             > engine.estimate_premium(30, "Non-smoker", 300000, "Term Life - 20yr")

    def test_smokers_pay_more_than_former_than_never(self):
        s = engine.estimate_premium(40, "Smoker", 300000, "Term Life - 20yr")
        f = engine.estimate_premium(40, "Former smoker", 300000, "Term Life - 20yr")
        n = engine.estimate_premium(40, "Non-smoker", 300000, "Term Life - 20yr")
        assert s > f > n

    def test_whole_life_costs_most(self):
        prems = [engine.estimate_premium(40, "Non-smoker", 300000, p)
                 for p in ("Term Life - 20yr", "Term Life - 30yr", "Universal Life", "Whole Life")]
        assert prems == sorted(prems)

    def test_premium_scales_linearly_with_coverage(self):
        p1 = engine.estimate_premium(40, "Non-smoker", 250000, "Term Life - 20yr")
        p2 = engine.estimate_premium(40, "Non-smoker", 500000, "Term Life - 20yr")
        assert abs(p2 - 2 * p1) < 0.02


class TestAffordability:
    def test_comfortable_applicant_is_affordable(self):
        prem = engine.estimate_premium(35, "Non-smoker", 300000, "Term Life - 20yr")
        af = engine.affordability_assess(90000, 2800, 20000, 300000, 0, 35, prem)
        assert af["verdict"] == "pass" and af["label"] == "AFFORDABLE"
        assert all(i["status"] == "pass" for i in af["indicators"])

    def test_overinsured_low_income_fails_coverage_multiple(self):
        prem = engine.estimate_premium(31, "Non-smoker", 1500000, "Term Life - 20yr")
        af = engine.affordability_assess(52000, 2905, 30000, 1500000, 0, 31, prem)
        assert af["label"] == "NOT JUSTIFIED"
        cm = next(i for i in af["indicators"] if i["label"] == "Coverage-to-income multiple")
        assert cm["status"] == "fail"

    def test_negative_disposable_income_fails(self):
        af = engine.affordability_assess(40000, 2600, 10000, 200000, 0, 40,
                                         premium=3000)   # net ≈ $2600/mo − expenses − $250
        disp = next(i for i in af["indicators"] if i["label"] == "Disposable income after premium")
        assert disp["status"] == "fail" and af["verdict"] == "fail"

    def test_age_banded_coverage_caps_tighten_with_age(self):
        prem = 1000.0
        young = engine.affordability_assess(50000, 1500, 0, 50000 * 22, 0, 35, prem)
        older = engine.affordability_assess(50000, 1500, 0, 50000 * 22, 0, 62, prem)
        y = next(i for i in young["indicators"] if i["label"] == "Coverage-to-income multiple")
        o = next(i for i in older["indicators"] if i["label"] == "Coverage-to-income multiple")
        assert y["status"] == "pass"       # 22× under the 25× cap at 35
        assert o["status"] == "fail"       # 22× far over the 10× cap at 62

    def test_existing_coverage_counts_toward_the_multiple(self):
        prem = 800.0
        without = engine.affordability_assess(60000, 1800, 0, 60000 * 20, 0, 35, prem)
        with_ex = engine.affordability_assess(60000, 1800, 0, 60000 * 20, 60000 * 10, 35, prem)
        assert without["cov_mult"] < with_ex["cov_mult"]

    def test_every_fail_produces_a_reason(self):
        prem = engine.estimate_premium(31, "Smoker", 900000, "Whole Life")
        af = engine.affordability_assess(35000, 2000, 60000, 900000, 0, 31, prem)
        n_fail = sum(1 for i in af["indicators"] if i["status"] == "fail")
        assert n_fail >= 1 and len(af["reasons"]) >= n_fail

    def test_afford_from_row_matches_direct_call(self):
        row = {"Age": 45, "Smoker Status": "Non-smoker",
               "Coverage Amount Requested (USD)": 400000.0,
               "Policy Type Requested": "Term Life - 20yr",
               "Annual Income (USD)": 85000.0, "Monthly Expenses (USD)": 3000.0,
               "Existing Debt (USD)": 25000.0, "Existing Coverage (USD)": 0.0}
        af = engine.afford_from_row(row)
        prem = engine.estimate_premium(45, "Non-smoker", 400000.0, "Term Life - 20yr")
        direct = engine.affordability_assess(85000, 3000, 25000, 400000, 0, 45, prem)
        assert af == direct
