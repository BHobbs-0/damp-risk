"""Data loader: Headline numbers for the Method page, served as data/method.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import method  # noqa: E402

json.dump(method(), sys.stdout, separators=(",", ":"))
