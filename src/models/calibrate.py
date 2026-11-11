"""Estimate damp risk for every social home by calibrating a logistic model to published rates.

Why this approach
-----------------
Home-level survey data (EHS microdata) wasn't available, but the survey *publishes*
damp rates for social rented homes by building age, dwelling type, floor area and
(in its reports) energy rating. Each published rate is a *margin*: the average damp
rate over all homes in one category.

The model is an ordinary additive logistic model,

    logit P(damp | home) = b0 + b_age[home] + b_type[home] + b_area[home] + b_eer[home]

but instead of learning from labelled homes, its coefficients are chosen so that,
applied to the **real joint mix of 2.86m EPC homes**, it reproduces every published
margin at once (fitted by minimising cross-entropy between published and predicted
category rates). Because the EPC data shows how characteristics occur together
(old homes are often poorly rated), overlapping effects aren't double-counted, which is
the main flaw of simply multiplying published risk ratios.

Assumptions (state them in the write-up): effects add on the logit scale (no
interactions); EHS and EPC categories measure the same things; the EPC social stock
resembles the surveyed social stock.

Validation: margins the model never sees (region, deprivation decile) and
leave-one-margin-out refits. See `validate()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit


@dataclass
class MarginModel:
    """Additive logistic model fitted to category-level target rates."""

    features: list[str]
    ridge: float = 1e-6  # tiny: only to pin down the redundant intercept/category offsets
    intercept: float = 0.0
    coefs: dict[str, dict[str, float]] = field(default_factory=dict)
    fit_report: pd.DataFrame | None = None

    # ------------------------------------------------------------------ core maths
    def _design(self, cells: pd.DataFrame) -> tuple[list[np.ndarray], list[list[str]]]:
        """Integer category codes per feature, plus the category labels."""
        codes, levels = [], []
        for f in self.features:
            cat = pd.Categorical(cells[f])
            codes.append(cat.codes.astype(int))
            levels.append([str(c) for c in cat.categories])
        return codes, levels

    @staticmethod
    def _unpack(theta, sizes):
        out, i = [], 1
        for s in sizes:
            out.append(theta[i : i + s])
            i += s
        return theta[0], out

    def fit(self, cells: pd.DataFrame, targets: dict[str, dict[str, float]], weight: str = "n") -> MarginModel:
        """cells: one row per combination of feature categories, with a count column `weight`.
        targets: {feature: {category: rate (0-1)}}; categories missing from targets are unconstrained."""
        codes, levels = self._design(cells)
        n = cells[weight].to_numpy(float)
        sizes = [len(lv) for lv in levels]
        # Categories with no published target are fixed at 0 (no evidence either way). Left free,
        # the optimiser would move them to help fit *other* margins, giving meaningless effects.
        free = np.concatenate(
            [[True]]
            + [
                [targets.get(f, {}).get(lv) is not None and not np.isnan(targets.get(f, {}).get(lv)) for lv in lvs]
                for f, lvs in zip(self.features, levels, strict=True)
            ]
        ).astype(bool)

        # Pre-compute, for each targeted (feature, category), the cell mask and target rate
        terms = []
        for fi, f in enumerate(self.features):
            for ci, lv in enumerate(levels[fi]):
                t = targets.get(f, {}).get(lv)
                if t is None or np.isnan(t):
                    continue
                mask = codes[fi] == ci
                share = n[mask].sum() / n.sum()
                terms.append((mask, float(np.clip(t, 1e-4, 1 - 1e-4)), share))

        def loss_grad(free_theta):
            theta = np.zeros(free.size)
            theta[free] = free_theta
            b0, betas = self._unpack(theta, sizes)
            eta = b0 + sum(b[c] for b, c in zip(betas, codes, strict=True))
            p = expit(eta)
            loss, dl_deta = 0.0, np.zeros_like(p)
            for mask, t, share in terms:
                nm = n[mask]
                pm = np.clip((nm * p[mask]).sum() / nm.sum(), 1e-9, 1 - 1e-9)
                loss += share * -(t * np.log(pm) + (1 - t) * np.log(1 - pm))
                # d loss / d pm, then chain through pm = sum(n p)/sum(n) and dp/deta = p(1-p)
                g = share * (pm - t) / (pm * (1 - pm))
                dl_deta[mask] += g * nm * p[mask] * (1 - p[mask]) / nm.sum()
            grad = np.zeros_like(theta)
            grad[0] = dl_deta.sum()
            i = 1
            for c, s in zip(codes, sizes, strict=True):
                grad[i : i + s] = np.bincount(c, weights=dl_deta, minlength=s)
                i += s
            loss += self.ridge * (theta[1:] ** 2).sum()
            grad[1:] += 2 * self.ridge * theta[1:]
            return loss, grad[free]

        overall = np.average([t for _, t, _ in terms]) if terms else 0.05
        theta0 = np.zeros(free.size)
        theta0[0] = np.log(overall / (1 - overall))
        res = minimize(loss_grad, theta0[free], jac=True, method="L-BFGS-B", options={"maxiter": 5000, "gtol": 1e-10})
        theta = np.zeros(free.size)
        theta[free] = res.x
        b0, betas = self._unpack(theta, sizes)
        self.intercept = float(b0)
        self.coefs = {
            f: dict(zip(lv, map(float, b), strict=True)) for f, lv, b in zip(self.features, levels, betas, strict=True)
        }
        self.fit_report = margin_table(self.predict(cells), cells, targets, weight)
        return self

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Damp probability for each row (unknown categories contribute 0 on the logit scale)."""
        eta = np.full(len(df), self.intercept)
        for f in self.features:
            eta += df[f].astype(str).map(self.coefs[f]).fillna(0.0).to_numpy()
        return expit(eta)


def margin_table(p: np.ndarray, cells: pd.DataFrame, targets: dict, weight: str = "n") -> pd.DataFrame:
    """Predicted vs target rate for every targeted (feature, category)."""
    rows = []
    for f, cats in targets.items():
        if f not in cells:
            continue
        for c, t in cats.items():
            m = cells[f].astype(str) == c
            if not m.any() or t is None or np.isnan(t):
                continue
            w = cells.loc[m, weight].to_numpy(float)
            rows.append(
                {
                    "feature": f,
                    "category": c,
                    "target": t,
                    "predicted": float(np.average(p[m.to_numpy()], weights=w)),
                    "homes": float(w.sum()),
                }
            )
    out = pd.DataFrame(rows)
    if len(out):
        out["error_pts"] = 100 * (out.predicted - out.target)
    return out


def summarise(table: pd.DataFrame, overall: float) -> dict:
    """MAE (percentage points) of the model vs a baseline that predicts the national rate everywhere.
    Weighted by number of homes in each category."""
    w = table.homes
    mae = float(np.average((table.predicted - table.target).abs(), weights=w) * 100)
    base = float(np.average((overall - table.target).abs(), weights=w) * 100)
    corr = float(np.corrcoef(table.predicted, table.target)[0, 1]) if len(table) > 2 else float("nan")
    return {
        "mae_pts": round(mae, 2),
        "baseline_mae_pts": round(base, 2),
        "correlation": round(corr, 3),
        "categories": int(len(table)),
    }
