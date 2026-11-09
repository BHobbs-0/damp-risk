"""Data loader: Framework runs this and serves its stdout as data/overview.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import overview  # noqa: E402

json.dump(overview(), sys.stdout, separators=(",", ":"))
