"""Score every social home with the fitted damp model.

Reads the model from data/processed/model/damp_model.json (fitted by
`python -m src.models.fit_damp`) and writes one row per home:

    data/processed/epc_scored.parquet   epc_social columns + `risk` (estimated probability of damp, 0-1)

This file is address-free but still home-level, so it stays git-ignored. Only area
aggregates (src/score/aggregate.py) reach the dashboard.

Usage:
    .venv\\Scripts\\python.exe -m src.score.score
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import duckdb
import numpy as np
from scipy.special import expit

from src.models.fit_damp import FEATURE_SQL, SOCIAL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL = PROJECT_ROOT / "data" / "processed" / "model" / "damp_model.json"
OUT = PROJECT_ROOT / "data" / "processed" / "epc_scored.parquet"


def score() -> dict:
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    df = duckdb.sql(f"select *, {FEATURE_SQL} from read_parquet('{SOCIAL.as_posix()}')").df()
    eta = np.full(len(df), model["intercept"])
    for f in model["features"]:
        eta += df[f].map(model["coefs"][f]).fillna(0.0).to_numpy()  # unseen category -> 0 (no evidence)
    df["risk"] = expit(eta)
    df = df.drop(columns=model["features"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False, compression="zstd")
    q = np.quantile(df.risk, [0.1, 0.5, 0.9, 0.99])
    return {
        "homes": len(df),
        "mean": float(df.risk.mean()),
        "p10": q[0],
        "median": q[1],
        "p90": q[2],
        "p99": q[3],
        "min": float(df.risk.min()),
        "max": float(df.risk.max()),
    }


if __name__ == "__main__":
    t0 = time.time()
    s = score()
    print(f"Scored {s['homes']:,} homes in {time.time() - t0:.0f}s -> {OUT}")
    print("  ".join(f"{k} {100 * v:.1f}%" for k, v in s.items() if k != "homes"))
