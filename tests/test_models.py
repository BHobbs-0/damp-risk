"""Tests for the evaluation toolkit on synthetic data with a known answer.

The synthetic homes are built so damp is driven mainly by wall insulation and
SAP score, with ~7% prevalence and uneven survey-style weights.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
from lightgbm import LGBMClassifier  # noqa: E402
from sklearn.calibration import CalibratedClassifierCV  # noqa: E402
from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import OneHotEncoder, StandardScaler  # noqa: E402

from src.models import evaluate, explain, plots, train  # noqa: E402

CATS = ["wall_insulation", "age_band"]
NUMS = ["sap_score", "floor_area_m2"]


@pytest.fixture(scope="module")
def data():
    rng = np.random.default_rng(0)
    n = 4000
    X = pd.DataFrame(
        {
            "wall_insulation": rng.choice(["insulated", "partial", "none"], n, p=[0.7, 0.05, 0.25]),
            "age_band": rng.choice(["pre1919", "1945-1964", "post1990"], n, p=[0.2, 0.5, 0.3]),
            "sap_score": rng.normal(70, 10, n).clip(1, 100),
            "floor_area_m2": rng.normal(70, 15, n).clip(20, 200),  # pure noise
        }
    )
    logit = -3.4 + 1.6 * (X.wall_insulation == "none") + 0.5 * (X.age_band == "pre1919") - 0.06 * (X.sap_score - 70)
    p_true = 1 / (1 + np.exp(-logit))
    y = rng.binomial(1, p_true)
    w = rng.lognormal(0, 0.5, n) * 1000
    for c in CATS:
        X[c] = X[c].astype("category")
    return X, y, w, p_true


def logistic():
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATS), ("num", StandardScaler(), NUMS)])
    return Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=1000))])


def lightgbm():
    return LGBMClassifier(
        n_estimators=150, learning_rate=0.05, num_leaves=15, min_child_samples=40, random_state=42, verbose=-1
    )


# --- evaluate ---------------------------------------------------------------


def test_synthetic_prevalence_is_realistic(data):
    _, y, w, _ = data
    assert 0.04 < evaluate.weighted_prevalence(y, w) < 0.12


def test_perfect_and_constant_predictions():
    y = np.array([0, 0, 0, 1, 0, 1, 0, 0, 0, 0])
    perfect = evaluate.metrics(y, y.astype(float))
    assert perfect["pr_auc"] == pytest.approx(1.0)
    assert perfect["roc_auc"] == pytest.approx(1.0)
    assert perfect["top10_capture"] == pytest.approx(0.5)  # top 10% = 1 home = 1 of 2 positives
    constant = evaluate.metrics(y, np.full(len(y), 0.2))
    assert constant["roc_auc"] == pytest.approx(0.5)
    assert constant["pr_auc"] == pytest.approx(0.2)  # average precision of a constant = prevalence


def test_weights_equal_duplicated_rows():
    """Weight 2 must give the same answer as including the row twice."""
    y = np.array([0, 1, 0, 1, 0, 0, 1, 0])
    p = np.array([0.1, 0.8, 0.3, 0.4, 0.2, 0.6, 0.7, 0.05])
    w = np.array([1, 2, 1, 1, 2, 1, 1, 1])
    weighted = evaluate.metrics(y, p, w)
    duplicated = evaluate.metrics(np.repeat(y, w), np.repeat(p, w))
    for k in ("pr_auc", "roc_auc", "brier", "prevalence", "mean_predicted"):
        assert weighted[k] == pytest.approx(duplicated[k]), k


def test_calibration_of_true_probabilities_is_good(data):
    _, y, w, p_true = data
    table = evaluate.calibration_table(y, p_true, w, n_bins=10)
    assert len(table) == 10
    assert table.weight.sum() == pytest.approx(w.sum())
    assert evaluate.expected_calibration_error(y, p_true, w) < 0.03
    # A model that doubles every probability is badly calibrated
    assert evaluate.expected_calibration_error(y, np.clip(2 * p_true, 0, 1), w) > 0.03


def test_input_validation():
    with pytest.raises(ValueError, match="Length mismatch"):
        evaluate.metrics([0, 1], [0.5], None)
    with pytest.raises(ValueError, match="non-negative"):
        evaluate.metrics([0, 1], [0.2, 0.8], [1, -1])


# --- train ------------------------------------------------------------------


@pytest.fixture(scope="module")
def cv(data):
    X, y, w, _ = data
    models = {"baseline": train.baseline(), "logistic": logistic(), "lightgbm": lightgbm()}
    return train.cross_validate(models, X, y, weight=w, n_splits=4)


def test_cross_validation_outputs(cv, data):
    X, *_ = data
    assert list(cv.oof.columns) == ["baseline", "logistic", "lightgbm"]
    assert cv.oof.notna().all().all()  # every home predicted out-of-fold
    assert len(cv.oof) == len(X)
    assert len(cv.fold_metrics) == 3 * 4
    assert set(cv.table().columns) == {"pr_auc", "roc_auc", "brier", "top10_capture"}


def test_models_beat_baseline(cv):
    s = cv.summary
    assert s.loc["logistic", "pr_auc_mean"] > 1.5 * s.loc["baseline", "pr_auc_mean"]
    assert s.loc["lightgbm", "pr_auc_mean"] > 1.5 * s.loc["baseline", "pr_auc_mean"]
    assert s.loc["baseline", "roc_auc_mean"] == pytest.approx(0.5)
    assert s.loc["lightgbm", "oof_top10_capture"] > 0.2  # better than the 10% a random list finds


def test_weighted_fitting_runs_with_pipeline(data):
    X, y, w, _ = data
    res = train.cross_validate({"logistic": logistic()}, X, y, weight=w, n_splits=3, fit_weighted=True)
    assert res.oof.notna().all().all()


# --- explain ----------------------------------------------------------------


def test_shap_values_add_up_to_prediction(data):
    X, y, _, _ = data
    model = lightgbm().fit(X, y)
    values, expected = explain.shap_values(model, X)
    raw = model.predict(X, raw_score=True)
    np.testing.assert_allclose(values.sum(axis=1) + expected, raw, atol=1e-6)


def test_shap_ranks_true_drivers_above_noise(data):
    X, y, _, _ = data
    importance = explain.mean_abs_shap(lightgbm().fit(X, y), X)
    assert importance.index[0] in {"wall_insulation", "sap_score"}
    assert importance["floor_area_m2"] < importance["wall_insulation"]


def test_shap_works_through_calibration(data):
    X, y, _, _ = data
    calibrated = CalibratedClassifierCV(lightgbm(), method="isotonic", cv=3).fit(X, y)
    values, _ = explain.shap_values(calibrated, X)
    assert values.shape == X.shape


def test_shap_rejects_other_models(data):
    X, y, _, _ = data
    with pytest.raises(TypeError, match="LGBMClassifier"):
        explain.shap_values(logistic().fit(X, y), X)


# --- plots (smoke tests) ----------------------------------------------------


def test_plots_render(cv, data):
    X, y, w, _ = data
    model = lightgbm().fit(X, y)
    values, _ = explain.shap_values(model, X)
    figs = [
        plots.plot_calibration(cv.oof, y, w),
        plots.plot_pr_curves(cv.oof, y, w),
        plots.plot_shap_importance(explain.mean_abs_shap(model, X)),
        plots.plot_shap_by_category(values, X, "wall_insulation"),
        plots.plot_shap_by_category(values, X, "sap_score"),
    ]
    assert all(isinstance(f, plt.Figure) for f in figs)
    plt.close("all")
