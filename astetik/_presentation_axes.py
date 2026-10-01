"""Central physical-axis styling and declared scale/domain policies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, Unpack, cast

from matplotlib.axes import Axes
from matplotlib.ticker import MaxNLocator, ScalarFormatter

from ._manifest import Manifest
from ._plot_backend import ScaleAxes, disable_grid, drawing
from ._plot_styles import GridStyle, TickStyle
from ._presentation_labels import label, value_label
from ._spec_types import PlotSpec


class AxisDecoration(Protocol):
    def tick_params(self, **kwargs: Unpack[TickStyle]) -> None: ...
    def grid(self, _visible: bool, /, **kwargs: Unpack[GridStyle]) -> None: ...


def decorate(ax: Axes, manifest: Manifest, colorbar: bool) -> None:
    for side, spine in ax.spines.items():
        spine.set_visible(side in manifest.axes['spines'] and not colorbar)
        spine.set_color(manifest.colors['line'])
        spine.set_linewidth(manifest.axes['linewidth'])
    decoration = cast(AxisDecoration, ax)
    decoration.tick_params(
        colors=manifest.colors['muted'],
        direction=manifest.axes['tick_direction'],
        length=manifest.axes['tick_length'],
        width=manifest.axes['linewidth'],
    )
    ax.set_facecolor(manifest.colors['paper'])
    if manifest.axes['grid']:
        decoration.grid(
            True, color=manifest.colors['line'], linewidth=manifest.axes['linewidth'], alpha=0.5
        )
    else:
        disable_grid(ax)


def colorbar_label(
    ax: Axes, spec: PlotSpec, units: Mapping[str, str], descriptions: Mapping[str, str]
) -> None:
    kind = spec['kind']
    if kind == 'corr':
        drawing(ax).set_ylabel('Correlation coefficient')
    elif kind == 'world':
        drawing(ax).set_xlabel(label(spec.get('y'), units, descriptions))
    elif spec.get('hue'):
        drawing(ax).set_ylabel(label(spec.get('hue'), units, descriptions))


def label_axes(
    ax: Axes,
    spec: PlotSpec,
    units: Mapping[str, str],
    descriptions: Mapping[str, str],
    labels: tuple[str, str, bool],
) -> None:
    kind, options = spec['kind'], spec['options']
    x, y, _ = labels
    if kind == 'compare':
        drawing(ax).set_xlabel(label(ax.get_xlabel(), units, descriptions))
        drawing(ax).set_ylabel(label(spec.get('hue'), units, descriptions))
    elif kind == 'overlap':
        value = value_label(spec.get('x'), units)
        category = label(spec.get('hue'), units, descriptions)
        drawing(ax).set_xlabel(value if options.get('orient') == 'h' else category)
        drawing(ax).set_ylabel(category if options.get('orient') == 'h' else value)
    elif kind == 'oned':
        drawing(ax).set_xlabel(x)
    elif kind not in {'pie', 'world', 'table', 'text'}:
        drawing(ax).set_xlabel(x)
        if kind in {'line', 'longitudinal'} and isinstance(spec.get('y'), list):
            y = spec.get('labels', {}).get('y', value_label(spec.get('y'), units))
        drawing(ax).set_ylabel(y)


def apply_domains(ax: Axes, spec: PlotSpec, horizontal: bool) -> None:
    kind = spec['kind']
    for dimension in ('x', 'y'):
        policy = spec.get('axes', {}).get(dimension, {})
        scale = policy.get('scale', 'linear')
        axis = ax.xaxis if dimension == 'x' else ax.yaxis
        current = ax.get_xscale() if dimension == 'x' else ax.get_yscale()
        if scale != current:
            (
                cast(ScaleAxes, ax).set_xscale
                if dimension == 'x'
                else cast(ScaleAxes, ax).set_yscale
            )(scale)
        limits = policy.get('limits')
        if limits is not None:
            (ax.set_xlim if dimension == 'x' else ax.set_ylim)(*limits)
        formatter = axis.get_major_formatter()
        if scale == 'linear' and isinstance(formatter, ScalarFormatter):
            formatter.set_useOffset(False)
            axis.set_major_locator(
                MaxNLocator(
                    nbins=5,
                    integer=(
                        kind in {'count', 'multicount'}
                        and dimension == ('x' if horizontal else 'y')
                    ),
                )
            )
    if kind in {'bar', 'bartwo', 'bargrid', 'count', 'multicount', 'hist'}:
        dimension = 'x' if horizontal else 'y'
        if spec.get('axes', {}).get(dimension, {}).get('scale', 'linear') == 'linear':
            low, high = ax.get_xlim() if horizontal else ax.get_ylim()
            (ax.set_xlim if horizontal else ax.set_ylim)(min(0, low), max(0, high))
