"""SHAP explanations for LightGBM models.

Uses LightGBM's built-in TreeSHAP (`predict(..., pred_contrib=True)`) rather
than the `shap` package's TreeExplainer:
- exact same algorithm (TreeSHAP), computed by LightGBM itself
- handles pandas `category` columns natively
- avoids `shap` output-shape changes between versions (a list vs a 3-D array)

Values are in **log-odds** units. A positive value pushes a home towards damp.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline


def _unwrap(model, X: pd.DataFrame) -> tuple[LGBMClassifier, pd.DataFrame]:
    """Get the underlying LGBMClassifier, and X transformed by any pipeline steps before it."""
    if isinstance(model, Pipeline):
        X = model[:-1].transform(X) if len(model.steps) > 1 else X
        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X, columns=model[:-1].get_feature_names_out())
        model = model.steps[-1][1]
    if isinstance(model, CalibratedClassifierCV):
        # Calibration rescales probabilities but keeps the ranking; explain the
        # first fitted base model (others are trained on different folds).
        model = model.calibrated_classifiers_[0].estimator
    if not isinstance(model, LGBMClassifier):
        raise TypeError(
            f"Expected an LGBMClassifier (optionally in a Pipeline/CalibratedClassifierCV), got {type(model)}"
        )
    return model, X


def shap_values(model, X: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Per-home, per-feature SHAP values (log-odds) and the expected value (base rate in log-odds)."""
    lgbm, X_t = _unwrap(model, X)
    contrib = np.asarray(lgbm.predict(X_t, pred_contrib=True))
    values = pd.DataFrame(contrib[:, :-1], columns=list(X_t.columns), index=X.index)
    return values, float(contrib[0, -1])


def mean_abs_shap(model, X: pd.DataFrame) -> pd.Series:
    """Global feature importance: mean |SHAP| per feature, largest first."""
    values, _ = shap_values(model, X)
    return values.abs().mean().sort_values(ascending=False)
