"""Tests for the hex cartogram assignment."""

import math

import numpy as np
from shapely.geometry import box

from src.geo.hexmap import assign, hexagon


def test_every_point_gets_a_unique_cell_inside_the_area():
    rng = np.random.default_rng(1)
    area = box(0, 0, 100, 60)
    pts = rng.uniform([0, 0], [100, 60], size=(40, 2))
    cells, radius = assign(pts, area)
    assert len({tuple(c) for c in cells}) == len(pts)  # no two points share a cell
    assert area.buffer(radius).contains(box(*cells.min(axis=0), *cells.max(axis=0)))


def test_points_stay_close_to_home():
    rng = np.random.default_rng(2)
    area = box(0, 0, 100, 100)
    pts = rng.uniform([5, 5], [95, 95], size=(50, 2))
    cells, radius = assign(pts, area)
    moved = np.sqrt(((pts - cells) ** 2).sum(axis=1))
    assert np.median(moved) < 2 * radius


def test_hexagon_geometry():
    h = hexagon(0, 0, 10)
    assert len(h.exterior.coords) == 7  # 6 corners + closing point
    assert math.isclose(h.area, 1.5 * math.sqrt(3) * 100, rel_tol=1e-9)
