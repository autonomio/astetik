"""Place legends at declared positions and keep them clear of the plotted data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypedDict, Unpack, cast

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend
from matplotlib.transforms import Bbox, ScaledTranslation, Transform

from ._histogram_options import statistic
from ._presentation_clearance import covered, required_limit
from ._presentation_layout import solve_layout
from ._presentation_ticks import counted, value_locator
from ._render_common import figure_for
from ._spec_types import PlotSpec

# Outside positions: legend corner, axes corner, and the gap between them in points.
_OUTSIDE = {
    'outside right': ('upper left', (1.0, 1.0), (6.0, 0.0)),
    'outside top': ('lower left', (0.0, 1.0), (0.0, 4.0)),
}
_INSIDE = ('upper right', 'upper left', 'upper center', 'center right', 'center left',
           'lower right', 'lower left', 'lower center')
# Positions a legend can be cleared at by lengthening a zero-based value axis.
_HEADROOM = {False: ('upper right', 'upper left', 'upper center'),
             True: ('upper right', 'lower right', 'center right')}
_ZERO_BASED = frozenset({'hist', 'bar', 'bartwo', 'bargrid', 'count', 'multicount'})
# Beside the plot, a legend wider than this share of the page leaves the plot a sliver.
_SIDE_SHARE = 0.4
_PLACEMENT = '_astetik_legend_placement'


@dataclass(frozen=True)
class Placement:
    """What a legend shows and where it was asked to sit."""

    loc: str
    handles: list[Artist]
    fontsize: float
    bare: bool


class _LegendPlace(TypedDict, total=False):
    handles: list[Artist]
    loc: str
    frameon: bool
    bbox_to_anchor: tuple[float, float]
    bbox_transform: Transform
    ncols: int
    borderpad: float
    borderaxespad: float
    handlelength: float
    handletextpad: float


class _Keyed(Protocol):
    def legend(self, **kwargs: Unpack[_LegendPlace]) -> Legend: ...


class _Placed(Protocol):
    def set_loc(self, loc: str) -> None: ...


def place_legend(ax: Axes, placement: Placement, ncols: int = 1) -> Legend:
    """Create the legend at its declared position."""
    # 'best' starts upper right; the settled canvas decides where it finally sits.
    loc = 'upper right' if placement.loc == 'best' else placement.loc
    place = _LegendPlace(handles=placement.handles, loc=loc, frameon=False, ncols=ncols)
    if placement.loc in _OUTSIDE:
        corner, anchor, (dx, dy) = _OUTSIDE[placement.loc]
        shift = ScaledTranslation(dx / 72, dy / 72, figure_for(ax).dpi_scale_trans)
        # Flush with the axes edge, a fixed distance away at any figure size.
        place.update(loc=corner, bbox_to_anchor=anchor, bbox_transform=ax.transAxes + shift,
                     borderpad=0.0, borderaxespad=0.0)
    if placement.bare:
        place.update(handlelength=0.0, handletextpad=0.0)
    legend = cast(_Keyed, ax).legend(**place)
    # A legend inside the plot takes its room from the plot, never from the page layout.
    legend.set_in_layout(placement.loc in _OUTSIDE)
    setattr(legend, _PLACEMENT, placement)
    return legend


def placement_of(legend: Legend | None) -> Placement | None:
    """The declared placement of a legend this module set, if it is one."""
    return cast('Placement | None', getattr(legend, _PLACEMENT, None))


def _rows(ax: Axes, placement: Placement) -> None:
    """Set a legend above the axes in the fewest rows that fit the axes width."""
    for ncols in range(len(placement.handles), 0, -1):
        legend = place_legend(ax, placement, ncols)
        # Measured outside the layout, so a row that is too wide cannot collapse the axes.
        legend.set_in_layout(False)
        solve_layout(figure_for(ax))
        if ncols == 1 or legend.get_window_extent().width <= ax.get_window_extent().width:
            legend.set_in_layout(True)
            return


def _clear(ax: Axes, legend: Legend, pad: float) -> bool:
    """Whether the legend lies wholly inside the plot and reaches no mark."""
    solve_layout(figure_for(ax))
    frame, box = ax.get_window_extent(), legend.get_window_extent()
    inside = frame.x0 <= box.x0 and box.x1 <= frame.x1 and frame.y0 <= box.y0 and box.y1 <= frame.y1
    return inside and not covered(ax, box.padded(pad))


def _free_spot(ax: Axes, legend: Legend, pad: float) -> str | None:
    """First inside position at which the legend, set there, would reach no mark.

    An inside legend does not move the axes, so every candidate box follows from the one
    settled layout in which the legend sits upper right; no further layout pass is needed.
    """
    frame, box = ax.get_window_extent(), legend.get_window_extent()
    gap, width, height = frame.x1 - box.x1, box.width, box.height
    across = {'left': frame.x0 + gap, 'center': (frame.x0 + frame.x1 - width) / 2,
              'right': frame.x1 - gap - width}
    along = {'lower': frame.y0 + gap, 'center': (frame.y0 + frame.y1 - height) / 2,
             'upper': frame.y1 - gap - height}
    if width + 2 * gap > frame.width or height + 2 * gap > frame.height:
        return None
    for loc in _INSIDE:
        vertical, horizontal = loc.split()
        spot = Bbox.from_bounds(across[horizontal], along[vertical], width, height)
        if not covered(ax, spot.padded(pad)):
            return loc
    return None


def _ceiling(spec: PlotSpec) -> float:
    """A share cannot be drawn on an axis that runs past the whole."""
    if spec['kind'] != 'hist':
        return np.inf
    return {'proportion': 1.0, 'percent': 100.0}.get(statistic(spec['options']), np.inf)


def _settle(ax: Axes, legend: Legend, spec: PlotSpec, horizontal: bool) -> None:
    placement = cast(Placement, getattr(legend, _PLACEMENT))
    pad = 2 * figure_for(ax).dpi / 72
    if placement.loc == 'outside top':
        _rows(ax, placement)
    share = legend.get_window_extent().width / figure_for(ax).bbox.width
    if placement.loc == 'outside right' and share > _SIDE_SHARE:
        raise ValueError(
            f"A legend at 'outside right' would take {share:.0%} of the figure width; "
            "set it above the plot ('outside top') or shorten its labels."
        )
    if placement.loc in _OUTSIDE or _clear(ax, legend, pad):
        return
    if placement.loc == 'best':
        # Inside only where a spot is free; otherwise above the axes, never over the data.
        free = _free_spot(ax, legend, pad)
        if free is None:
            above = Placement('outside top', placement.handles, placement.fontsize, placement.bare)
            _rows(ax, above)
        else:
            cast(_Placed, legend).set_loc(free)
        return
    _headroom(ax, legend, spec, horizontal)


def _headroom(ax: Axes, legend: Legend, spec: PlotSpec, horizontal: bool) -> None:
    """Lengthen a zero-based value axis until the legend clears, where the order allows it."""
    loc, pad = cast(Placement, getattr(legend, _PLACEMENT)).loc, 2 * figure_for(ax).dpi / 72
    dimension = 'x' if horizontal else 'y'
    if spec['kind'] not in _ZERO_BASED or loc not in _HEADROOM[horizontal]:
        raise ValueError(f'A legend at {loc!r} covers the data; choose a free or outside position.')
    if spec.get('axes', {}).get(dimension, {}).get('limits') is not None:
        raise ValueError(
            f'A legend at {loc!r} cannot clear the data within the declared {dimension} limits; '
            'use an outside position.'
        )
    locator = value_locator(counted(spec, dimension, horizontal))
    low = (ax.get_xlim() if horizontal else ax.get_ylim())[0]
    for _ in range(3):
        needed = required_limit(ax, legend.get_window_extent().padded(pad), horizontal)
        limit = float(locator.tick_values(low, needed)[-1]) if np.isfinite(needed) else np.inf
        if limit > _ceiling(spec):
            break
        (ax.set_xlim if horizontal else ax.set_ylim)(low, limit)
        if _clear(ax, legend, pad):
            return
    raise ValueError(f'A legend at {loc!r} cannot clear the data; use an outside position.')


def clear_legends(axes: list[Axes], spec: PlotSpec, horizontal: bool) -> None:
    """Move or give headroom to each declared legend until it covers no mark."""
    for ax in axes:
        legend = ax.get_legend()
        if legend is not None and placement_of(legend) is not None:
            _settle(ax, legend, spec, horizontal)
