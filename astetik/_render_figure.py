"""Compose several complete plot specifications into one lettered figure."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import cast

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ._figure_panels import bind
from ._presentation_headings import heading
from ._render_context import Recorder, RendererOptions, RendererSpec
from ._render_layout import figure_dimensions
from ._types import JsonValue

Draw = Callable[[pd.DataFrame, RendererSpec, Axes, Recorder], None]
_MAX_PANELS = 26


def _letter(index: int, style: str | None) -> str:
    letter = chr(ord('a') + index)
    return {'a': letter, 'A': letter.upper(), '(a)': f'({letter})'}.get(style or '', '')


def compose(
    data: pd.DataFrame, spec: RendererSpec, options: RendererOptions, rec: Recorder, draw: Draw
) -> Figure:
    """Lay the panels out row by row; each keeps its own axes, legend, and methods."""
    manifest, paper, panels = spec['_manifest'], spec['_paper'], spec.get('panels', [])
    if len(panels) > _MAX_PANELS:
        raise ValueError(f'A figure letters at most {_MAX_PANELS} panels.')
    wide = not paper or manifest.paper['preset'] == 'double'
    ncols = min(options.get('ncols') or (2 if wide else 1), len(panels))
    nrows = math.ceil(len(panels) / ncols)
    figure = Figure(figsize=figure_dimensions(manifest, paper, nrows, ncols), layout='constrained')
    FigureCanvasAgg(figure)
    setattr(figure, '_astetik_font_size', manifest.rc(paper).get('font.size', 9))
    axes = figure.subplots(nrows, ncols, squeeze=False).flat
    methods: list[JsonValue] = []
    for index, panel in enumerate(panels):
        ax, letter = axes[index], _letter(index, options.get('labels', 'a'))
        view = cast(
            RendererSpec,
            dict(panel, key=spec.get('key', []), _manifest=manifest, _paper=paper, _hue_colors={},
                 legend=panel.get('legend', spec.get('legend', True))),
        )
        part, before = Recorder(rec.marks, {}, {'panel': letter or index + 1}), set(figure.axes)
        try:
            draw(data, view, ax, part)
        except ValueError as error:
            raise ValueError(f'Panel {index + 1} ({view["kind"]}): {error}') from error
        for owned in (ax, *(set(figure.axes) - before)):
            bind(owned, index)
        text = f'{letter}  {panel.get("title", "")}'.strip()
        if text:
            heading(ax, text)
        methods.append({'panel': letter or index + 1, 'kind': view['kind'], **part.methods})
    for ax in axes[len(panels):]:
        ax.set_visible(False)
    rec.methods.update(panels=methods, rows=nrows, columns=ncols)
    return figure
