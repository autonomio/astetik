"""Central publication composition, axes, labels, and typography."""

from __future__ import annotations

from collections.abc import Mapping

from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.text import Text

from ._figure_panels import panel_axes
from ._manifest import Manifest
from ._plot_backend import draw_canvas
from ._presentation_axes import apply_domains, colorbar_label, decorate, label_axes
from ._presentation_grid import outer_labels, proportion, settle_bands
from ._presentation_headings import figure_title, fit_headings
from ._presentation_labels import axis_labels
from ._presentation_layout import hold_layout
from ._presentation_legend import clear_legends
from ._presentation_notes import spread_end_labels, wrap_category_labels
from ._spec_types import PlotSpec


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
        # A role names a manifest colour; a series label carries its series' own colour.
        artist.set_color(manifest.colors.get(role, role))


def finish(
    figure: Figure,
    spec: PlotSpec,
    manifest: Manifest,
    units: Mapping[str, str],
    descriptions: Mapping[str, str],
) -> None:
    """Apply one design policy to every renderer without changing data."""
    panels = [
        (view, axes, axis_labels(view, units, descriptions))
        for view, axes in panel_axes(figure, spec)
    ]
    for view, axes, labels in panels:
        for ax in axes:
            is_colorbar = hasattr(ax, '_colorbar')
            decorate(ax, manifest, is_colorbar)
            if is_colorbar:
                colorbar_label(ax, view, units, descriptions)
                continue
            label_axes(ax, view, units, descriptions, labels)
            apply_domains(ax, view, labels[2])
            legend = ax.get_legend()
            if legend:
                legend.set_frame_on(False)
    outer_labels(figure)
    figure_title(figure, spec, manifest)
    _typography(figure, spec, manifest)
    fit_headings(figure)
    for ax in figure.axes:
        wrap_category_labels(ax)
        spread_end_labels(ax)
    for view, axes, labels in panels:
        clear_legends(axes, view, labels[2])
    settle_bands(figure)
    proportion(figure, manifest.paper['aspect'])
    _typography(figure, spec, manifest)
    hold_layout(figure)
    draw_canvas(figure)
