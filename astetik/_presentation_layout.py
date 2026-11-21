"""Solve a figure's layout, and refuse a figure whose plot area has no room left."""

from __future__ import annotations

import warnings
from typing import Protocol, cast

from matplotlib.figure import Figure


class _Layout(Protocol):
    def draw_without_rendering(self) -> None: ...


def solve_layout(figure: Figure) -> None:
    """Place every axes for the current content; a collapsed plot area is an error."""
    with warnings.catch_warnings():
        warnings.filterwarnings('error', message='constrained_layout not applied')
        try:
            cast(_Layout, figure).draw_without_rendering()
        except UserWarning as error:
            raise ValueError(
                'The figure has no room left for its plot: its labels, legend, or panels need '
                'more than the page gives. Use a wider layout, fewer panels per row, shorter '
                'labels, or a legend above the plot.'
            ) from error


class _Engine(Protocol):
    def set_layout_engine(self, layout: str) -> None: ...


def hold_layout(figure: Figure) -> None:
    """Solve the layout a last time and hold it, so no later draw can place anything anew."""
    solve_layout(figure)
    cast(_Engine, figure).set_layout_engine('none')
