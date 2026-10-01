"""Visible-label and table-cell geometry at the actual renderer dimensions."""
from __future__ import annotations

import itertools

from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.table import Table
from matplotlib.text import Text
from matplotlib.transforms import BboxBase

from ._json import json_object
from ._types import JsonObject


def omitted_tick_labels(figure: Figure) -> set[int]:
    omitted: set[int] = set()
    for axes in figure.axes:
        if not axes.get_visible():
            omitted.update(id(text) for text in axes.findobj(match=Text))
        for axis in (axes.xaxis, axes.yaxis):
            if not axes.axison:
                omitted.update((id(axis.label), id(axis.get_offset_text())))
            low, high = sorted(axis.get_view_interval())
            for tick in (*axis.get_major_ticks(), *axis.get_minor_ticks()):
                if not axes.axison or not low - 1e-12 <= tick.get_loc() <= high + 1e-12:
                    omitted.update((id(tick.label1), id(tick.label2)))
    return omitted


def overlap(left: BboxBase, right: BboxBase) -> bool:
    return (min(left.x1, right.x1) - max(left.x0, right.x0) > .5 and
            min(left.y1, right.y1) - max(left.y0, right.y0) > .5)


def clipped(extent: BboxBase, bounds: BboxBase) -> bool:
    return (extent.x0 < bounds.x0 - .5 or extent.y0 < bounds.y0 - .5 or
            extent.x1 > bounds.x1 + .5 or extent.y1 > bounds.y1 + .5)


def tick_collisions(figure: Figure, renderer: RendererBase, omitted: set[int]) -> list[JsonObject]:
    issues: list[JsonObject] = []
    for axes in figure.axes:
        if not axes.get_visible() or not axes.axison:
            continue
        for name, axis in (('x', axes.xaxis), ('y', axes.yaxis)):
            ticks = sorted((*axis.get_major_ticks(), *axis.get_minor_ticks()), key=lambda tick: tick.get_loc())
            for side in ('label1', 'label2'):
                labels = [tick.label1 if side == 'label1' else tick.label2 for tick in ticks]
                labels = [label for label in labels if label.get_visible() and label.get_text().strip()
                          and id(label) not in omitted]
                for left, right in itertools.pairwise(labels):
                    if overlap(left.get_window_extent(renderer), right.get_window_extent(renderer)):
                        issues.append({'axis': name, 'labels': [left.get_text(), right.get_text()]})
    return issues


def _cell_extents(table: Table, renderer: RendererBase) -> tuple[dict[tuple[int, int], tuple[str, BboxBase]], list[JsonObject]]:
    extents: dict[tuple[int, int], tuple[str, BboxBase]] = {}
    issues: list[JsonObject] = []
    for location, cell in table.get_celld().items():
        text = cell.get_text()
        if not cell.get_visible() or not text.get_visible() or not text.get_text().strip():
            continue
        extent, bounds = text.get_window_extent(renderer), cell.get_window_extent(renderer)
        extents[location] = (text.get_text(), extent)
        if clipped(extent, bounds):
            issues.append(json_object({'cell': list(location), 'text': text.get_text()}))
    return extents, issues


def _cell_collisions(extents: dict[tuple[int, int], tuple[str, BboxBase]]) -> list[JsonObject]:
    issues: list[JsonObject] = []
    for dimension in (0, 1):
        groups: dict[int, list[tuple[int, int]]] = {}
        for location in extents:
            groups.setdefault(location[dimension], []).append(location)
        for locations in groups.values():
            locations.sort(key=lambda location: location[1 - dimension])
            for left, right in itertools.pairwise(locations):
                if overlap(extents[left][1], extents[right][1]):
                    issues.append(json_object({'cells': [list(left), list(right)],
                                               'texts': [extents[left][0], extents[right][0]]}))
    return issues


def table_issues(figure: Figure, renderer: RendererBase) -> tuple[list[JsonObject], list[JsonObject]]:
    fit: list[JsonObject] = []
    collisions: list[JsonObject] = []
    for table in figure.findobj(match=Table):
        if not table.get_visible() or (table.axes and not table.axes.get_visible()):
            continue
        extents, issues = _cell_extents(table, renderer)
        fit.extend(issues)
        collisions.extend(_cell_collisions(extents))
    return fit, collisions
