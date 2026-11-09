"""Hex cartogram of local authorities: one equal-sized hexagon per council.

Why: on a normal map, large rural councils dominate the picture even though
they hold few social homes, while dense urban councils are tiny. Giving every
council the same size makes the comparison fair.

Method:
1. Lay a pointy-top hexagon grid over England, sized so there are slightly
   more cells than councils.
2. Assign each council to one cell, minimising the total squared distance
   between council centres and cell centres (the Hungarian algorithm,
   `scipy.optimize.linear_sum_assignment`). Councils move as little as
   possible, but dense areas like London have to spread out.

Usage:
    .venv\\Scripts\\python.exe -m src.geo.hexmap
"""

from __future__ import annotations

import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from shapely.geometry import Point, Polygon

from src.geo.orient import clockwise

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAD_GPKG = PROJECT_ROOT / "data" / "processed" / "geo" / "lad_england.gpkg"
OUT = PROJECT_ROOT / "data" / "processed" / "dashboard" / "la_hex.geojson"


def hex_centres(boundary, radius: float) -> np.ndarray:
    """Centres of a pointy-top hex grid whose centres fall within `boundary` (buffered by one radius)."""
    minx, miny, maxx, maxy = boundary.bounds
    dx, dy = math.sqrt(3) * radius, 1.5 * radius
    area = boundary.buffer(radius * 0.9)
    centres = []
    for row, y in enumerate(np.arange(miny - dy, maxy + dy, dy)):
        offset = dx / 2 if row % 2 else 0.0
        for x in np.arange(minx - dx + offset, maxx + dx, dx):
            if area.contains(Point(x, y)):
                centres.append((x, y))
    return np.array(centres)


def hexagon(x: float, y: float, radius: float) -> Polygon:
    """Pointy-top hexagon polygon."""
    return Polygon(
        [
            (x + radius * math.cos(math.radians(60 * k - 90)), y + radius * math.sin(math.radians(60 * k - 90)))
            for k in range(6)
        ]
    )


def assign(points: np.ndarray, boundary, spare: float = 1.05, max_tries: int = 30) -> tuple[np.ndarray, float]:
    """Assign each point to a unique hex cell. Returns (cell centres per point, hex radius)."""
    n = len(points)
    radius = math.sqrt(boundary.area / (n * spare) / (1.5 * math.sqrt(3)))  # hex area = 1.5*sqrt(3)*r^2
    for _ in range(max_tries):
        cells = hex_centres(boundary, radius)
        if len(cells) >= n:
            break
        radius *= 0.95  # not enough cells (irregular coastline): shrink and retry
    else:
        raise ValueError("Could not create enough hex cells")
    cost = ((points[:, None, :] - cells[None, :, :]) ** 2).sum(axis=2)
    rows, cols = linear_sum_assignment(cost)
    out = np.empty_like(points)
    out[rows] = cells[cols]
    return out, radius


def build(out_path: Path = OUT) -> gpd.GeoDataFrame:
    lad = gpd.read_file(LAD_GPKG)
    boundary = lad.union_all().simplify(500)
    pts = np.array([(p.x, p.y) for p in lad.representative_point()])
    centres, radius = assign(pts, boundary)
    hexes = gpd.GeoDataFrame(
        pd.DataFrame({"lad24cd": lad.lad24cd, "lad24nm": lad.lad24nm}),
        geometry=[hexagon(x, y, radius * 0.94) for x, y in centres],  # 6% gap between hexes
        crs=lad.crs,
    )
    moved_km = np.sqrt(((pts - centres) ** 2).sum(axis=1)) / 1000
    print(
        f"{len(hexes)} councils, hex radius {radius / 1000:.1f} km, median move {np.median(moved_km):.0f} km, "
        f"max move {moved_km.max():.0f} km ({lad.lad24nm.iloc[moved_km.argmax()]})"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clockwise(hexes.to_crs(4326)).to_file(out_path, driver="GeoJSON", COORDINATE_PRECISION=5)
    return hexes


if __name__ == "__main__":
    build()
