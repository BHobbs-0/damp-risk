"""Data loader: Indicators by IMD decile and MSOA points for the scatter, served as data/deprivation.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import deprivation  # noqa: E402

json.dump(deprivation(), sys.stdout, separators=(",", ":"))
