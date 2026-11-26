"""Names set beside marks: direct series labels and category names, kept from colliding."""

from __future__ import annotations

import textwrap
from typing import cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Annotation
from matplotlib.ticker import FixedLocator, FuncFormatter

from ._mark_backend import marks
from ._plot_backend import drawing
from ._presentation_layout import solve_layout

_END_LABELS = '_astetik_end_labels'
_OFFSET = 5.0


def end_labels(ax: Axes, entries: list[tuple[str, tuple[object, float], str]], size: float) -> None:
    """Name each series beside its last point, in the series' own colour."""
    labels: list[Annotation] = []
    for text, point, color in entries:
        label = marks(ax).annotate(
            text, xy=point, xytext=(_OFFSET, 0.0), textcoords='offset points', ha='left',
            va='center', fontsize=size, annotation_clip=False,
        )
        setattr(label, '_astetik_text_role', color)
        labels.append(label)
    setattr(ax, _END_LABELS, labels)


def _spread(labels: list[Annotation], dpi: float) -> None:
    for label in labels:
        label.xyann = (_OFFSET, 0.0)
    boxes = [label.get_window_extent() for label in labels]
    origin = np.asarray([(box.y0 + box.y1) / 2 for box in boxes])
    order = np.argsort(origin, kind='stable')
    centre, height = origin[order].copy(), max(box.height for box in boxes) * 1.05
    for _ in range(200):
        tight = np.flatnonzero(np.diff(centre) < height - 1e-9)
        if not len(tight):
            break
        for index in tight:
            push = (height - (centre[index + 1] - centre[index])) / 2
            centre[index] -= push
            centre[index + 1] += push
    for index, moved in zip(order, centre):
        labels[index].xyann = (_OFFSET, float(moved - origin[index]) * 72 / dpi)


def spread_end_labels(figure: Figure) -> None:
    """Separate direct labels that would overlap, moving each as little as needed."""
    groups = [cast('list[Annotation]', getattr(ax, _END_LABELS, [])) for ax in figure.axes]
    crowded = [labels for labels in groups if len(labels) > 1]
    if crowded:
        solve_layout(figure)
    for labels in crowded:
        _spread(labels, figure.dpi)


def _named(ax: Axes) -> bool:
    """Named categories sit on fixed positions; a numeric axis keeps its own tick labels."""
    return (
        isinstance(ax.xaxis.get_major_formatter(), FuncFormatter)
        and isinstance(ax.xaxis.get_major_locator(), FixedLocator)
        and len(ax.get_xticks()) > 1
    )


def _wrap(ax: Axes) -> None:
    positions = np.asarray(ax.get_xticks(), dtype=float)
    labels = ax.get_xticklabels()
    if len(labels) != len(positions):
        # Shared facets show the names on one row only; an axes that hides them has none to wrap,
        # and writing its empty list back would erase the names every sharing facet shows.
        return
    pixels = ax.transData.transform(np.column_stack([positions, np.zeros(len(positions))]))[:, 0]
    slot = float(np.diff(pixels).min()) * 0.94
    names: list[str] = []
    for label in labels:
        text, width = label.get_text(), label.get_window_extent().width
        longest = max((len(line) for line in text.split('\n')), default=0)
        if width > slot and longest:
            fit = max(1, int(longest * slot / width))
            text = '\n'.join(
                textwrap.fill(line, fit, break_long_words=False) for line in text.split('\n')
            )
        names.append(text)
    if names != [label.get_text() for label in labels]:
        drawing(ax).set_xticks(positions, names)


def wrap_category_labels(figure: Figure) -> None:
    """Break category names between words so neighbouring names do not touch."""
    named = [ax for ax in figure.axes if ax.get_visible() and _named(ax)]
    if named:
        solve_layout(figure)
    for ax in named:
        _wrap(ax)
