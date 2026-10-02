"""Shared row identities, categorical axes, and local figure operations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.text import Text
from numpy.typing import NDArray

from ._colors import ColorSystem
from ._manifest import Manifest
from ._plot_backend import FileFontProperties, SharingAxes, disable_grid, drawing
from ._render_context import ColorMapping, RendererSpec, RowArray
from ._render_scalar import scalar
from ._types import FloatArray, JsonScalar


def levels(values: Iterable[object]) -> list[JsonScalar]:
    unique = pd.unique(np.asarray(list(values), dtype=object))
    result: list[JsonScalar] = []
    for value in unique:
        normalized = scalar(value)
        if isinstance(normalized, (list, dict)):
            raise ValueError('Category labels must be scalar values.')
        result.append(normalized)
    return result


def equal(values: object, label: JsonScalar) -> NDArray[np.bool_]:
    return np.asarray(values == label, dtype=bool)


def numerical(values: object, name: str) -> FloatArray:
    try:
        array = np.asarray(values, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name!r} must contain numerical observations.') from exc
    if not np.isfinite(array).all():
        raise ValueError(
            f'{name!r} contains missing or nonfinite observations; declare exclusions before rendering.'
        )
    return array


def series_colors(manifest: Manifest, labels: list[str], paper: bool) -> ColorMapping:
    return (
        {labels[0]: ColorSystem(manifest).primary}
        if len(labels) == 1 and str(labels[0]) not in manifest.categories
        else color_mapping(manifest, labels, paper)
    )


def color_mapping(manifest: Manifest, labels: Iterable[object], paper: bool) -> ColorMapping:
    return ColorSystem(manifest).categorical(labels, strict=paper)


def groups(
    data: pd.DataFrame, rows: RowArray, hue: str | None
) -> list[tuple[JsonScalar, RowArray]]:
    if hue is None:
        return [(None, rows)]
    result: list[tuple[JsonScalar, RowArray]] = []
    for label in levels(data[hue]):
        positions = rows[equal(data.iloc[rows][hue], label)]
        if len(positions):
            result.append((label, positions))
    return result


def zero_baseline(ax: Axes, horizontal: bool, values: Iterable[float]) -> None:
    resolved = list(np.asarray(list(values), dtype=float))
    sharing = cast(SharingAxes, ax)
    siblings = (
        sharing.get_shared_x_axes() if horizontal else sharing.get_shared_y_axes()
    ).get_siblings(ax)
    for sibling in siblings:
        interval = sibling.dataLim.intervalx if horizontal else sibling.dataLim.intervaly
        if np.isfinite(interval).all():
            resolved.extend(interval)
    low, high = min([0.0, *resolved]), max([0.0, *resolved])
    if low == high:
        low, high = 0.0, 1.0
    if horizontal:
        ax.set_xlim(low, high)
        disable_grid(ax.yaxis)
    else:
        ax.set_ylim(low, high)
        disable_grid(ax.xaxis)


def category_axes(ax: Axes, categories: list[JsonScalar], horizontal: bool) -> None:
    positions = np.arange(len(categories))
    if horizontal:
        drawing(ax).set_yticks(positions, [str(v) for v in categories])
        ax.set_ylim(len(categories) - 0.5, -0.5)
    else:
        drawing(ax).set_xticks(positions, [str(v) for v in categories])
        ax.set_xlim(-0.5, len(categories) - 0.5)


def legend(ax: Axes, spec: RendererSpec, mappings: ColorMapping) -> None:
    if spec.get('legend', True) and mappings:
        drawing(ax).legend(
            handles=[Patch(facecolor=color, label=str(label)) for label, color in mappings.items()],
            frameon=False,
            loc='best',
        )


def figure_for(ax: Axes) -> Figure:
    figure = ax.figure
    if not isinstance(figure, Figure):
        raise ValueError('Astetik renderers require an owned Figure.')
    return figure


def finalize_font(figure: Figure, manifest: Manifest) -> None:
    for item in figure.findobj(match=Text):
        properties = item.get_fontproperties().copy()
        cast(FileFontProperties, properties).set_file(str(manifest.font_path))
        item.set_fontproperties(properties)
