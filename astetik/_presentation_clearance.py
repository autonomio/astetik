"""Where plotted marks sit on the settled canvas, for anything that must stay clear of them."""

from __future__ import annotations

from typing import cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection, PolyCollection
from matplotlib.colors import to_rgba
from matplotlib.path import Path
from matplotlib.transforms import Bbox

from ._render_common import figure_for
from ._types import FloatArray

_UNCONNECTED = ('None', 'none', '', ' ')


def _outlines(ax: Axes) -> list[tuple[Path, bool, float]]:
    """Display-space paths, occupied interiors (even hollow), and visible stroke half-widths."""
    scale = figure_for(ax).dpi / 144
    shapes = [
        (patch.get_transform().transform_path(patch.get_path()), True,
         patch.get_linewidth() * scale if to_rgba(patch.get_edgecolor())[3]
         and patch.get_linestyle() not in _UNCONNECTED else 0.0)
        for patch in ax.patches
        if patch.get_visible()
    ]
    shapes += [
        (line.get_transform().transform_path(line.get_path()), False, line.get_linewidth() * scale)
        for line in ax.lines
        if line.get_visible() and line.get_alpha() != 0 and to_rgba(line.get_color())[3]
        and line.get_linestyle() not in _UNCONNECTED
    ]
    for collection in ax.collections:
        if collection.get_visible() and not isinstance(collection, PathCollection):
            filled, transform = isinstance(collection, PolyCollection), collection.get_transform()
            colors = np.asarray(collection.get_edgecolor(), dtype=float)
            radius = float(np.max(collection.get_linewidth(), initial=0.0)) * scale if colors.size and colors[:, 3].any() else 0.0
            shapes += [(transform.transform_path(path), filled, radius)
                       for path in collection.get_paths()]
    return shapes


def _markers(ax: Axes) -> tuple[FloatArray, float]:
    """Marker centres in display space and the largest marker radius among them."""
    scale = figure_for(ax).dpi / 72
    centres: list[FloatArray] = [np.empty((0, 2))]
    radius = 0.0
    for collection in ax.collections:
        if isinstance(collection, PathCollection) and collection.get_visible():
            offsets = np.asarray(collection.get_offsets(), dtype=float).reshape(-1, 2)
            centres.append(collection.get_offset_transform().transform(offsets))
            sizes = np.asarray(collection.get_sizes(), dtype=float)
            colors = np.asarray(collection.get_edgecolor(), dtype=float)
            edge = float(np.max(collection.get_linewidth(), initial=0.0)) if colors.size and colors[:, 3].any() else 0.0
            radius = max(radius, (float(np.sqrt(sizes.max(initial=0.0))) + edge) / 2 * scale)
    for line in ax.lines:
        if line.get_visible() and line.get_marker() not in _UNCONNECTED:
            centres.append(line.get_transform().transform(line.get_xydata()))
            edge = line.get_markeredgewidth() if to_rgba(line.get_markeredgecolor())[3] else 0.0
            radius = max(radius, (float(line.get_markersize()) + edge) / 2 * scale)
    points = np.vstack(centres)
    return points[np.isfinite(points).all(axis=1)], radius


def covered(ax: Axes, box: Bbox) -> bool:
    """Whether any mark of the axes reaches into ``box`` on the settled canvas."""
    if any(path.intersects_bbox(box.padded(radius), filled=filled)
           for path, filled, radius in _outlines(ax)):
        return True
    points, radius = _markers(ax)
    inside = (
        (points[:, 0] >= box.x0 - radius)
        & (points[:, 0] <= box.x1 + radius)
        & (points[:, 1] >= box.y0 - radius)
        & (points[:, 1] <= box.y1 + radius)
    )
    return bool(inside.any())


def _reach(polygon: FloatArray, low: float, high: float) -> float:
    """Largest value coordinate a polyline attains while its other coordinate is in range."""
    x0, y0, x1, y1 = polygon[:-1, 0], polygon[:-1, 1], polygon[1:, 0], polygon[1:, 1]
    upright = x1 == x0
    run = np.where(upright, 1.0, x1 - x0)
    start = np.where(upright, 0.0, np.clip((low - x0) / run, 0, 1))
    stop = np.where(upright, 1.0, np.clip((high - x0) / run, 0, 1))
    crossing = (np.maximum(x0, x1) >= low) & (np.minimum(x0, x1) <= high)
    values = np.maximum(y0 + (y1 - y0) * start, y0 + (y1 - y0) * stop)[crossing]
    return float(values.max()) if len(values) else -np.inf


def required_limit(ax: Axes, box: Bbox, horizontal: bool) -> float:
    """Upper value-axis limit at which every mark beside ``box`` ends below it."""
    frame = ax.get_window_extent()
    swap = slice(None, None, -1) if horizontal else slice(None)
    (low, edge), (high, _) = box.get_points()[:, swap]
    base = frame.x0 if horizontal else frame.y0
    reaches = [
        (_reach(cast(FloatArray, polygon)[:, swap], float(low) - radius, float(high) + radius), radius)
        for path, _, radius in _outlines(ax)
        for polygon in path.to_polygons(closed_only=False)
    ]
    points, radius = _markers(ax)
    points = points[:, swap]
    beside = points[(points[:, 0] >= low - radius) & (points[:, 0] <= high + radius)]
    if len(beside):
        reaches.append((float(beside[:, 1].max()), radius))
    bottom, top = ax.get_xlim() if horizontal else ax.get_ylim()
    stretch = max((max(reach - base, 0.0) / (float(edge) - base - radius)
                   if float(edge) > base + radius else np.inf
                   for reach, radius in reaches if np.isfinite(reach)), default=0.0)
    return bottom + (top - bottom) * stretch
