"""Data loader: National profile by construction age and published EHS damp rates, served as data/drivers.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import drivers  # noqa: E402

json.dump(drivers(), sys.stdout, separators=(",", ":"))
