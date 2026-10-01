"""Central publication composition, axes, labels, and typography."""

from __future__ import annotations

import textwrap
from collections.abc import Mapping
from typing import Protocol, Unpack, cast

from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text

from ._manifest import Manifest
from ._plot_backend import draw_canvas
from ._plot_styles import TitleStyle
from ._presentation_axes import apply_domains, colorbar_label, decorate, label_axes
from ._presentation_labels import axis_labels
from ._spec_types import PlotSpec


class FigureTitle(Protocol):
    def suptitle(self, title: str, **kwargs: Unpack[TitleStyle]) -> Text: ...


def _title(figure: Figure, spec: PlotSpec, manifest: Manifest) -> None:
    title, subtitle = spec['title'], spec['subtitle']
    if title or subtitle:
        available_pt = figure.get_figwidth() * 72 - 24
        width = max(15, int(available_pt / (manifest.typography['titlesize'] * 0.52)))
        content = '\n'.join(
            textwrap.fill(text, width=width, break_long_words=False)
            for text in (title, subtitle)
            if text
        )
        cast(FigureTitle, figure).suptitle(
            content,
            x=0.02,
            ha='left',
            va='top',
            fontsize=manifest.typography['titlesize'],
            fontweight='normal',
        )


def _typography(figure: Figure, spec: PlotSpec, manifest: Manifest) -> None:
    font = FontProperties(fname=str(manifest.font_path))
    for artist in figure.findobj(match=Text):
        size = (
            max(artist.get_fontsize(), manifest.paper['min_fontsize'])
            if spec['paper']
            else artist.get_fontsize()
        )
        artist.set_fontproperties(font)
        artist.set_fontsize(size)
        artist.set_fontweight('normal')
        artist.set_parse_math(False)
        artist.set_usetex(False)
        role = getattr(
            artist,
            '_astetik_text_role',
            'ink' if artist is getattr(figure, '_suptitle', None) else 'muted',
        )
        artist.set_color(manifest.colors[role])


def finish(
    figure: Figure,
    spec: PlotSpec,
    manifest: Manifest,
    units: Mapping[str, str],
    descriptions: Mapping[str, str],
) -> None:
    """Apply one design policy to every renderer without changing data."""
    labels = axis_labels(spec, units, descriptions)
    for ax in figure.axes:
        is_colorbar = hasattr(ax, '_colorbar')
        decorate(ax, manifest, is_colorbar)
        if is_colorbar:
            colorbar_label(ax, spec, units, descriptions)
            continue
        label_axes(ax, spec, units, descriptions, labels)
        apply_domains(ax, spec, labels[2])
        legend = ax.get_legend()
        if legend:
            legend.set_frame_on(False)
    _title(figure, spec, manifest)
    _typography(figure, spec, manifest)
    draw_canvas(figure)
