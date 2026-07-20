"""Synthetic data generator + published/external priors."""
import numpy as np

import datagen
import external_data
import published_models


class TestDatagen:
    def test_reproducible_for_same_seed(self):
        a, b = datagen.generate(50, seed=5), datagen.generate(50, seed=5)
        assert a.equals(b)

    def test_different_seeds_differ(self):
        assert not datagen.generate(50, seed=5).equals(datagen.generate(50, seed=6))

    def test_high_risk_rate_is_35pct(self):
        df = datagen.generate(1000, seed=1)
        assert abs(df["High Risk Label"].mean() - 0.35) < 0.01

    def test_value_ranges(self):
        df = datagen.generate(500, seed=2)
        assert df["Age"].between(21, 70).all()
        assert df["BMI"].between(16, 46).all()
        assert df["Credit Score"].between(480, 850).all()
        assert (df["Coverage Amount Requested (USD)"] % 25000 == 0).all()
        assert df["Coverage Amount Requested (USD)"].between(25000, 1000000).all()

    def test_some_applicants_are_overinsured(self):
        df = datagen.generate(1000, seed=3)
        mult = df["Coverage Amount Requested (USD)"] / df["Annual Income (USD)"]
        assert (mult > 10).mean() > 0.03   # the deliberate over-insurance segment exists


class TestFramingham:
    def test_probabilities_in_unit_interval(self):
        p = published_models.framingham_cvd10([45], [True], [27], [130], [0], [0])
        assert 0 < p[0] < 1

    def test_smoking_and_diabetes_raise_risk(self):
        base = published_models.framingham_cvd10([50], [True], [26], [125], [0], [0])[0]
        smoke = published_models.framingham_cvd10([50], [True], [26], [125], [1], [0])[0]
        diab = published_models.framingham_cvd10([50], [True], [26], [125], [0], [1])[0]
        assert smoke > base and diab > base

    def test_inputs_clipped_to_validated_range(self):
        lo = published_models.framingham_cvd10([18], [False], [12], [70], [0], [0])[0]
        eq = published_models.framingham_cvd10([30], [False], [15], [90], [0], [0])[0]
        assert abs(lo - eq) < 1e-12


class TestExternalPrior:
    def test_no_models_returns_neutral_half(self):
        df = datagen.generate(5, seed=1)
        assert (external_data.prior_scores([], df) == 0.5).all()

    def test_weighted_mean_favours_strong_models(self):
        df = datagen.generate(20, seed=1)
        strong = {"name": "s", "features": ["age"], "coef": [2.0], "intercept": 0.0,
                  "mean": [45.0], "std": [10.0], "auc": 0.9, "weight": 0.4}
        weak = {"name": "w", "features": ["age"], "coef": [-2.0], "intercept": 0.0,
                "mean": [45.0], "std": [10.0], "auc": 0.55, "weight": 0.05}
        both = external_data.prior_scores([strong, weak], df)
        strong_only = external_data.prior_scores([strong], df)
        weak_only = external_data.prior_scores([weak], df)
        # the blend must sit much closer to the strong model than the weak one
        assert np.abs(both - strong_only).mean() < np.abs(both - weak_only).mean()
