"""Names set beside marks: direct series labels and category names, kept from colliding."""

from __future__ import annotations

import textwrap
from typing import cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.text import Annotation
from matplotlib.ticker import FixedLocator, FuncFormatter

from ._mark_backend import marks
from ._plot_backend import drawing
from ._presentation_layout import solve_layout
from ._render_common import figure_for

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


def spread_end_labels(ax: Axes) -> None:
    """Separate direct labels that would overlap, moving each as little as needed."""
    labels = cast('list[Annotation]', getattr(ax, _END_LABELS, []))
    if len(labels) < 2:
        return
    figure = figure_for(ax)
    solve_layout(figure)
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
        labels[index].xyann = (_OFFSET, float(moved - origin[index]) * 72 / figure.dpi)


def wrap_category_labels(ax: Axes) -> None:
    """Break category names between words so neighbouring names do not touch."""
    positions = np.asarray(ax.get_xticks(), dtype=float)
    # Named categories sit on fixed positions; a numeric axis keeps its own tick labels.
    named = isinstance(ax.xaxis.get_major_formatter(), FuncFormatter)
    if not named or not isinstance(ax.xaxis.get_major_locator(), FixedLocator) or len(positions) < 2:
        return
    solve_layout(figure_for(ax))
    pixels = ax.transData.transform(np.column_stack([positions, np.zeros(len(positions))]))[:, 0]
    slot = float(np.diff(pixels).min()) * 0.94
    names: list[str] = []
    for label in ax.get_xticklabels():
        text, width = label.get_text(), label.get_window_extent().width
        longest = max((len(line) for line in text.split('\n')), default=0)
        if width > slot and longest:
            fit = max(1, int(longest * slot / width))
            text = '\n'.join(
                textwrap.fill(line, fit, break_long_words=False) for line in text.split('\n')
            )
        names.append(text)
    drawing(ax).set_xticks(positions, names)
