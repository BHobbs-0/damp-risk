"""Data loader: Councils and neighbourhoods (MSOAs) with indicators and housing mix, served as data/areas.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # project root, for `src.*`

from src.dashboard.data import areas  # noqa: E402

json.dump(areas(), sys.stdout, separators=(",", ":"))
