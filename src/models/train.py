"""Cross-validation harness: compare models fairly on identical folds.

Design notes:
- **Stratified K-fold** keeps the ~7% damp rate in every fold, so no fold is
  short of positive cases.
- **Out-of-fold (OOF) predictions**: every home is predicted by a model that
  never saw it. Calibration curves and top-decile capture are computed on these.
- **Survey weights** are always used for *evaluation*. Using them for
  *training* is optional (`fit_weighted`) and an experiment to report:
  weighting can help match the population but adds variance.
- Fixed `seed` (42) means results are reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from src.models.evaluate import metrics

SEED = 42


def baseline() -> DummyClassifier:
    """Predicts the training prevalence for everyone: the bar every model must beat."""
    return DummyClassifier(strategy="prior")


def _fit(model, X, y, w, fit_weighted: bool):
    if not fit_weighted or w is None:
        return model.fit(X, y)
    if isinstance(model, Pipeline):
        return model.fit(X, y, **{f"{model.steps[-1][0]}__sample_weight": w})
    return model.fit(X, y, sample_weight=w)


@dataclass
class CVResult:
    fold_metrics: pd.DataFrame  # one row per (model, fold)
    oof: pd.DataFrame  # out-of-fold predicted probability, one column per model
    summary: pd.DataFrame  # mean ± sd across folds, plus pooled OOF metrics

    def table(self, cols=("pr_auc", "roc_auc", "brier", "top10_capture")) -> pd.DataFrame:
        """Compact 'mean (sd)' comparison table for the write-up."""
        out = {}
        for c in cols:
            out[c] = (
                self.summary[f"{c}_mean"].map("{:.3f}".format)
                + " ("
                + self.summary[f"{c}_sd"].map("{:.3f}".format)
                + ")"
            )
        return pd.DataFrame(out, index=self.summary.index)


def cross_validate(
    models: dict[str, object],
    X: pd.DataFrame,
    y,
    weight=None,
    n_splits: int = 5,
    seed: int = SEED,
    fit_weighted: bool = False,
) -> CVResult:
    """Fit each model on the same stratified folds; return fold metrics and OOF predictions."""
    y = np.asarray(y)
    w = None if weight is None else np.asarray(weight, dtype=float)
    folds = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    oof = pd.DataFrame(index=X.index, columns=list(models), dtype=float)
    rows = []
    for fold, (train_idx, test_idx) in enumerate(folds.split(X, y)):
        w_train = None if w is None else w[train_idx]
        w_test = None if w is None else w[test_idx]
        for name, model in models.items():
            fitted = _fit(clone(model), X.iloc[train_idx], y[train_idx], w_train, fit_weighted)
            p = fitted.predict_proba(X.iloc[test_idx])[:, 1]
            oof.iloc[test_idx, oof.columns.get_loc(name)] = p
            rows.append({"model": name, "fold": fold, **metrics(y[test_idx], p, w_test)})

    fold_metrics = pd.DataFrame(rows)
    agg = fold_metrics.drop(columns="fold").groupby("model", sort=False).agg(["mean", "std"])
    agg.columns = [f"{m}_{'sd' if s == 'std' else s}" for m, s in agg.columns]
    pooled = pd.DataFrame({name: metrics(y, oof[name].to_numpy(), w) for name in models}).T.add_prefix("oof_")
    return CVResult(fold_metrics=fold_metrics, oof=oof, summary=agg.join(pooled))
