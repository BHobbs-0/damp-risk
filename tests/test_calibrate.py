"""Tests for the margin-calibrated logistic model on synthetic data with a known answer."""

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from src.models.calibrate import MarginModel, margin_table, summarise

TRUE = {
    "intercept": -2.8,
    "age": {"old": 1.1, "mid": 0.3, "new": -0.6},
    "rating": {"good": -0.5, "poor": 0.9},
    "size": {"small": -0.2, "large": 0.25},
}


@pytest.fixture(scope="module")
def population():
    """Correlated features: old homes are much more likely to be poorly rated."""
    rng = np.random.default_rng(3)
    n = 60_000
    age = rng.choice(["old", "mid", "new"], n, p=[0.25, 0.45, 0.30])
    p_poor = np.select([age == "old", age == "mid"], [0.6, 0.25], 0.05)
    rating = np.where(rng.random(n) < p_poor, "poor", "good")
    p_large = np.select([age == "old", age == "mid"], [0.7, 0.4], 0.2)  # older homes are bigger
    size = np.where(rng.random(n) < p_large, "large", "small")
    homes = pd.DataFrame({"age": age, "rating": rating, "size": size})
    eta = TRUE["intercept"] + sum(homes[f].map(TRUE[f]) for f in ["age", "rating", "size"])
    homes["p_true"] = expit(eta)
    cells = homes.groupby(["age", "rating", "size"], as_index=False).agg(
        n=("p_true", "size"), p_true=("p_true", "mean")
    )
    targets = {f: homes.groupby(f).p_true.mean().to_dict() for f in ["age", "rating", "size"]}
    return homes, cells, targets


def test_reproduces_published_margins(population):
    _, cells, targets = population
    model = MarginModel(["age", "rating", "size"]).fit(cells, targets)
    assert model.fit_report.error_pts.abs().max() < 0.05  # every margin matched within 0.05 points


def test_recovers_home_level_risk_despite_correlated_features(population):
    """Margins + the real joint mix identify the true model, so cell risks match the truth."""
    _, cells, targets = population
    model = MarginModel(["age", "rating", "size"]).fit(cells, targets)
    np.testing.assert_allclose(model.predict(cells), cells.p_true, atol=0.004)


def test_naive_multiplication_double_counts(population):
    """The approach exists because multiplying risk ratios over-states risk for old, poor homes."""
    homes, cells, targets = population
    overall = homes.p_true.mean()
    naive = overall * np.prod([cells[f].map(targets[f]) / overall for f in ["age", "rating", "size"]], axis=0)
    model = MarginModel(["age", "rating", "size"]).fit(cells, targets)
    worst = (cells.age == "old") & (cells.rating == "poor")
    assert (naive[worst] - cells.p_true[worst]).mean() > 0.02  # naive is badly too high
    assert abs((model.predict(cells)[worst] - cells.p_true[worst]).mean()) < 0.005


def test_held_out_margin_is_predicted(population):
    """Fit without the size margin, then predict it: the held-out check used for real validation."""
    homes, cells, targets = population
    model = MarginModel(["age", "rating", "size"]).fit(cells, {k: v for k, v in targets.items() if k != "size"})
    table = margin_table(model.predict(cells), cells, {"size": targets["size"]})
    s = summarise(table, homes.p_true.mean())
    assert s["mae_pts"] < s["baseline_mae_pts"]


def test_untargeted_categories_are_fixed_at_zero():
    """A category with no published rate (e.g. suppressed 'detached') must not get a made-up effect."""
    cells = pd.DataFrame(
        {"a": ["x", "y", "z", "x", "y", "z"], "b": ["p", "p", "p", "q", "q", "q"], "n": [100, 100, 100, 100, 100, 100]}
    )
    model = MarginModel(["a", "b"]).fit(cells, {"a": {"x": 0.1, "y": np.nan}, "b": {"p": 0.05, "q": 0.15}})
    assert model.coefs["a"]["y"] == 0.0 and model.coefs["a"]["z"] == 0.0
    assert set(model.fit_report.category) == {"x", "p", "q"}
    p = model.predict(pd.DataFrame({"a": ["x", "never_seen"], "b": ["p", "p"]}))
    assert 0 < p[1] < 1
