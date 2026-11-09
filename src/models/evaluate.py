"""Evaluation metrics for an imbalanced, survey-weighted binary classifier.

Why these metrics (interview notes):
- **PR-AUC (average precision)** is the headline metric. With ~7% damp, a
  model can reach 93% accuracy by predicting "no damp" for everyone, so
  accuracy is meaningless. PR-AUC focuses on how well positives are found.
  Its baseline is the prevalence (~0.07), not 0.5.
- **ROC-AUC** is reported for familiarity, but it looks flattering on
  imbalanced data.
- **Brier score** (mean squared error of probabilities) rewards calibrated
  probabilities, which matter because risk is *averaged* over areas.
- **Calibration table**: within each band of predicted risk, does the observed
  damp rate match? If the model says 20%, about 20% should be damp.
- **Top-decile capture**: "inspect the riskiest 10% of homes and you find X%
  of damp cases." The business-friendly version of the ranking metrics.

Every function accepts optional `weight` (EHS survey weights), so results
describe the housing stock rather than just the sampled homes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def _arrays(y, p, w):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    w = np.ones_like(y) if w is None else np.asarray(w, dtype=float)
    if not (len(y) == len(p) == len(w)):
        raise ValueError(f"Length mismatch: y={len(y)}, p={len(p)}, weight={len(w)}")
    if np.any(w < 0):
        raise ValueError("Weights must be non-negative")
    return y, p, w


def weighted_prevalence(y, weight=None) -> float:
    """Share of positives, weighted (e.g. % of dwellings with damp)."""
    y, _, w = _arrays(y, np.zeros(len(y)), weight)
    return float(np.average(y, weights=w))


def top_k_capture(y, p, weight=None, k: float = 0.10) -> float:
    """Share of all (weighted) positives found in the top `k` share of (weighted) predicted risk."""
    y, p, w = _arrays(y, p, weight)
    order = np.argsort(-p, kind="stable")
    cum_w = np.cumsum(w[order]) / w.sum()
    in_top = cum_w <= k + 1e-12
    if not in_top.any():  # k smaller than the first case's weight share: take that one case
        in_top[0] = True
    return float((y[order] * w[order])[in_top].sum() / (y * w).sum())


def metrics(y, p, weight=None) -> dict[str, float]:
    """Headline metrics for one set of predictions."""
    y, p, w = _arrays(y, p, weight)
    p_clipped = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "pr_auc": float(average_precision_score(y, p, sample_weight=w)),
        "roc_auc": float(roc_auc_score(y, p, sample_weight=w)),
        "brier": float(brier_score_loss(y, p, sample_weight=w)),
        "log_loss": float(log_loss(y, p_clipped, sample_weight=w, labels=[0, 1])),
        "prevalence": float(np.average(y, weights=w)),
        "mean_predicted": float(np.average(p, weights=w)),
        "top10_capture": top_k_capture(y, p, w, k=0.10),
    }


def calibration_table(y, p, weight=None, n_bins: int = 10, strategy: str = "quantile") -> pd.DataFrame:
    """Observed vs predicted rate per bin of predicted risk.

    strategy='quantile' gives bins with equal (weighted) numbers of homes, which
    suits skewed risk distributions. 'uniform' gives equal-width bins over [0, 1].
    """
    y, p, w = _arrays(y, p, weight)
    if strategy == "quantile":
        order = np.argsort(p, kind="stable")
        cum = np.cumsum(w[order]) / w.sum()
        bins = np.empty(len(p), dtype=int)
        bins[order] = np.minimum((cum * n_bins - 1e-9).astype(int), n_bins - 1)
    elif strategy == "uniform":
        bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    else:
        raise ValueError("strategy must be 'quantile' or 'uniform'")

    df = pd.DataFrame({"bin": bins, "y": y, "p": p, "w": w})
    df["yw"], df["pw"] = df.y * df.w, df.p * df.w
    table = df.groupby("bin").agg(n=("y", "size"), weight=("w", "sum"), yw=("yw", "sum"), pw=("pw", "sum"))
    table["mean_predicted"] = table.pw / table.weight
    table["observed_rate"] = table.yw / table.weight
    return table[["n", "weight", "mean_predicted", "observed_rate"]].reset_index()


def expected_calibration_error(y, p, weight=None, n_bins: int = 10) -> float:
    """Weighted mean |observed - predicted| across quantile bins (0 = perfectly calibrated)."""
    t = calibration_table(y, p, weight, n_bins)
    return float(np.average((t.observed_rate - t.mean_predicted).abs(), weights=t.weight))
