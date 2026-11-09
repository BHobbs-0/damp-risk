"""Model evaluation charts (matplotlib, for notebooks and the write-up).

Colours follow docs/design.md: baseline grey, logistic regression blue, the
main model in the accent orange. Pass a `title` that states the finding.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve

from src.models.evaluate import calibration_table, weighted_prevalence

ACCENT = "#D85A30"
COLOURS = {"baseline": "#9E9E9E", "logistic": "#2B6CB0", "lightgbm": ACCENT}
FALLBACK = ["#6B46C1", "#2F855A", "#B7791F"]


def _colour(name: str, i: int) -> str:
    key = name.lower()
    for k, c in COLOURS.items():
        if k in key:
            return c
    return FALLBACK[i % len(FALLBACK)]


def plot_calibration(oof: pd.DataFrame, y, weight=None, n_bins: int = 10, title: str | None = None):
    """Observed vs predicted damp rate per decile of predicted risk, one line per model."""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    top = 0.0
    for i, name in enumerate(oof.columns):
        t = calibration_table(y, oof[name].to_numpy(), weight, n_bins)
        ax.plot(t.mean_predicted, t.observed_rate, marker="o", ms=4, label=name, color=_colour(name, i))
        top = max(top, t.mean_predicted.max(), t.observed_rate.max())
    lim = min(1.0, top * 1.1)
    ax.plot([0, lim], [0, lim], ls="--", lw=1, color="#BDBDBD", label="perfect calibration")
    ax.set(xlim=(0, lim), ylim=(0, lim), xlabel="Mean predicted risk", ylabel="Observed damp rate")
    ax.set_title(title or "Calibration: predicted vs observed")
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def plot_pr_curves(oof: pd.DataFrame, y, weight=None, title: str | None = None):
    """Precision-recall curves; the dashed line is the prevalence (a random model)."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for i, name in enumerate(oof.columns):
        precision, recall, _ = precision_recall_curve(y, oof[name].to_numpy(), sample_weight=weight)
        ax.plot(recall, precision, label=name, color=_colour(name, i), lw=1.8)
    ax.axhline(weighted_prevalence(y, weight), ls="--", lw=1, color="#BDBDBD", label="prevalence")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Recall (share of damp homes found)", ylabel="Precision")
    ax.set_title(title or "Precision-recall")
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig


def plot_shap_importance(importance: pd.Series, top: int = 12, title: str | None = None):
    """Horizontal bar chart of mean |SHAP| (from explain.mean_abs_shap)."""
    s = importance.head(top)[::-1]
    fig, ax = plt.subplots(figsize=(6, 0.35 * len(s) + 1))
    ax.barh(s.index, s.values, color=ACCENT)
    ax.set(xlabel="Mean |SHAP value| (log-odds)", ylabel="")
    ax.set_title(title or "What drives predicted damp risk")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    return fig


def plot_shap_by_category(shap_df: pd.DataFrame, X: pd.DataFrame, feature: str, title: str | None = None):
    """SHAP effect of one feature: boxes per category, or a scatter for numeric features."""
    fig, ax = plt.subplots(figsize=(6, 4))
    values, x = shap_df[feature], X[feature]
    if isinstance(x.dtype, pd.CategoricalDtype) or x.dtype == object:
        order = values.groupby(x, observed=True).median().sort_values().index
        ax.boxplot(
            [values[x == c] for c in order],
            orientation="horizontal",
            showfliers=False,
            patch_artist=True,
            boxprops={"facecolor": "#F5C4B3", "edgecolor": ACCENT},
            medianprops={"color": ACCENT},
        )
        ax.set_yticks(range(1, len(order) + 1), [str(c) for c in order])
        ax.set_xlabel("SHAP value (log-odds); right = more damp risk")
    else:
        sample = np.random.default_rng(42).choice(len(x), size=min(len(x), 5000), replace=False)
        ax.scatter(x.iloc[sample], values.iloc[sample], s=6, alpha=0.4, color=ACCENT)
        ax.axhline(0, color="#BDBDBD", lw=1)
        ax.set(xlabel=feature, ylabel="SHAP value (log-odds)")
    ax.set_title(title or f"Effect of {feature}")
    fig.tight_layout()
    return fig
