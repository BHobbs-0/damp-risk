"""Data loader: All England MSOA outlines, compact delta-encoded, served as data/msoa_shapes.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import msoa_shapes  # noqa: E402

json.dump(msoa_shapes(), sys.stdout, separators=(",", ":"))
