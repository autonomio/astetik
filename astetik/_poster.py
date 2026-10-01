"""Publication poster frames retain the source field and input row identity."""

from __future__ import annotations

from typing import cast

import pandas as pd

from ._errors import AstetikError
from ._manifest import Manifest
from ._render_context import Rendered
from ._renderers import DEFAULT_OPTIONS, render_plot
from ._spec_types import PlotSpec
from ._types import JsonObject


def render_poster(data: pd.DataFrame, spec: PlotSpec, manifest: Manifest, paper: bool) -> Rendered:
    options, frame = spec['options'], cast(object, spec['options'].get('frame'))
    if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame < len(data):
        raise AstetikError(
            'ANIMATION_FRAME', 'Declare an existing zero-based poster frame.', {'rows': len(data)}
        )
    kind = options.get('plot_type')
    if kind not in {'bar', 'pie'}:
        raise AstetikError('ANIMATION_KIND', 'Animation frames support bar or pie.')
    x, y = spec.get('x'), spec.get('y')
    if not isinstance(x, str) or not isinstance(y, str):
        raise AstetikError('ANIMATION_COLUMNS', 'Animation requires one x and one y field.')
    fields = [x, y]
    units = spec.get('units', {})
    if units.get(x) != units.get(y):
        raise AstetikError(
            'UNIT_COMPARABILITY',
            'Animated quantities require the same declared unit; convert during preparation.',
        )
    poster = pd.DataFrame(
        {'series': fields, 'value': [data.iloc[frame][field] for field in fields]}
    )
    poster_spec = cast(
        PlotSpec, {'kind': kind, 'x': 'series', 'y': 'value', 'options': DEFAULT_OPTIONS[kind]}
    )
    rendered = render_plot(poster, poster_spec, manifest, paper)
    records: list[JsonObject] = []
    for mark in rendered.marks:
        values = mark['values']
        if not isinstance(values, dict):
            raise ValueError('Animation mark values must be an object.')
        field = values['category']
        mark['source_rows'] = [frame]
        if 'category_source_rows' in values:
            values['category_source_rows'] = [frame]
        mark['source_field'], values['frame'] = field, frame
        records.append(
            {
                'mark_id': mark['id'],
                **values,
                'source_rows': [frame],
                'source_field': field,
                'computation': mark['computation'],
            }
        )
    rendered.table = pd.DataFrame(records)
    rendered.methods['poster'] = {
        'frame': frame,
        'plot_type': kind,
        'fields': [field for field in fields],
    }
    return rendered
