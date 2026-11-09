"""Polygon ring orientation for d3-geo maps.

d3-geo treats a polygon whose outer ring runs anticlockwise as "the whole
globe except this shape", so every area fills the screen. GeoJSON from most
tools (RFC 7946) uses anticlockwise outer rings, so flip them to clockwise.
"""

import geopandas as gpd
import shapely


def clockwise(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = shapely.orient_polygons(out.geometry.values, exterior_cw=True)
    return out
