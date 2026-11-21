"""Figure titles and panel headings, set in the manifest's type."""

from __future__ import annotations

import textwrap
from typing import Protocol, Unpack, cast

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.text import Text

from ._manifest import Manifest
from ._plot_styles import TitleStyle
from ._presentation_layout import solve_layout
from ._spec_types import PlotSpec


class _FigureTitle(Protocol):
    def suptitle(self, title: str, **kwargs: Unpack[TitleStyle]) -> Text: ...


def _wrapped(text: str, width_pt: float, size: float) -> str:
    """Break a heading between words so it stays inside the width it heads."""
    return textwrap.fill(text, width=max(15, int(width_pt / (size * 0.52))), break_long_words=False)


def figure_title(figure: Figure, spec: PlotSpec, manifest: Manifest) -> None:
    title, subtitle = spec['title'], spec['subtitle']
    if title or subtitle:
        size, available = manifest.typography['titlesize'], figure.get_figwidth() * 72 - 24
        content = '\n'.join(_wrapped(text, available, size) for text in (title, subtitle) if text)
        cast(_FigureTitle, figure).suptitle(
            content, x=0.02, ha='left', va='top', fontsize=size, fontweight='normal'
        )


class _Headed(Protocol):
    def set_title(self, _label: str, /, *, loc: str, pad: float | None = None) -> Text: ...


def heading(ax: Axes, text: str, pad: float | None = None) -> Text:
    """Head one panel at its top-left corner, in ink, ``pad`` points above the axes."""
    title = cast(_Headed, ax).set_title(text, loc='left', pad=pad)
    setattr(title, '_astetik_text_role', 'ink')
    return title


def fit_headings(figure: Figure) -> None:
    """Break a panel heading between words when it is wider than the panel it heads."""
    headed = [ax for ax in figure.axes if ax.get_visible() and ax.get_title(loc='left')]
    if not headed:
        return
    solve_layout(figure)
    for ax in headed:
        text = ax.get_title(loc='left')
        width, room = heading(ax, text).get_window_extent().width, ax.get_window_extent().width
        if width > room:
            fit = max(8, int(len(text) * room / width))
            heading(ax, textwrap.fill(text, fit, break_long_words=False))
