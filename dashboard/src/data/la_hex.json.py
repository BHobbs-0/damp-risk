"""Data loader: council hex cartogram, served as data/la_hex.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import la_hex  # noqa: E402

json.dump(la_hex(), sys.stdout, separators=(",", ":"))
