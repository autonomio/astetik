"""World rendering with explicit scientific provenance."""

from __future__ import annotations

import itertools
from hashlib import sha256
from pathlib import Path
from typing import Protocol, cast

import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.colors import LogNorm, Normalize, to_hex
from matplotlib.patches import Polygon

from ._plot_backend import Color, colorbar_figure, disable_grid
from ._render_common import (
    figure_for,
    numerical,
)
from ._render_context import (
    RenderContext,
)
from ._shape_backend import geometry_code, geometry_reader, geometry_shape


def world(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    country, value = context.column('x'), context.column('y')
    codes = data.iloc[rows][country].astype(str).str.upper()
    if codes.duplicated().any():
        raise ValueError('world requires one explicitly aggregated value per country code.')
    values = numerical(data.iloc[rows][value], value)
    if options.get('log', False) and np.any(values <= 0):
        raise ValueError('Log colour normalization requires strictly positive values.')
    domain = numerical(data[value], value)
    if options.get('log', False) and np.any(domain <= 0):
        raise ValueError(
            'Log colour normalization requires strictly positive values in every facet.'
        )
    norm = (
        LogNorm(domain.min(), domain.max())
        if options.get('log', False)
        else Normalize(domain.min(), domain.max())
    )
    cmap = colors.sequential()
    reader = geometry_reader(str(Path(__file__).parent / 'extras' / 'countries.shp'))
    field_names = [str(f[0]) for f in reader.fields[1:]]
    codefield = field_names.index('ADM0_A3')
    records = list(reader.iterShapeRecords())
    available = {geometry_code(r, codefield) for r in records}
    unknown = sorted(set(codes) - available)
    if unknown:
        raise ValueError(
            f'Country codes absent from bundled geometry: {unknown}. Use supported three-letter ADM0_A3 codes.'
        )
    mapping = {code: (value, position) for code, value, position in zip(codes, values, rows)}
    polygons: list[Polygon] = []
    faces: list[Color] = []
    for record in records:
        code = geometry_code(record, codefield)
        shape = geometry_shape(record)
        parts = [*list(shape.parts), len(shape.points)]
        face = (
            _colour(cmap, norm, float(mapping[code][0]))
            if code in mapping
            else colors.manifest.colors['line']
        )
        for first, last in itertools.pairwise(parts):
            polygons.append(Polygon(shape.points[first:last], closed=True))
            faces.append(face)
        if code in mapping:
            v, p = mapping[code]
            rec.mark(
                'country',
                dict(country=code, value=v, colour=to_hex(_colour(cmap, norm, float(v)))),
                [int(p)],
                'identity; country polygon geometry; colour encodes original value',
                facet,
            )
    collection = PatchCollection(
        polygons, facecolor=faces, edgecolor=colors.manifest.colors['paper'], linewidth=0.12
    )
    collection.set_cmap(cmap)
    collection.set_norm(norm)
    ax.add_collection(collection)
    ax.set(
        xlim=(-180, 180), ylim=(-90, 90), xlabel='Longitude (degrees)', ylabel='Latitude (degrees)'
    )
    ax.set_aspect('equal')
    disable_grid(ax)
    colorbar_figure(figure_for(ax)).colorbar(
        collection, ax=ax, label=str(value), orientation='horizontal', fraction=0.08, pad=0.08
    )
    rec.methods['world'] = dict(
        projection='Plate Carree (unprojected longitude/latitude)',
        geometry='bundled countries.shp ADM0_A3',
        colour_normalization='log' if options.get('log', False) else 'linear',
        missing_country_colour=colors.manifest.colors['line'],
        domain=[float(domain.min()), float(domain.max())],
        geometry_files={
            suffix: sha256(
                (Path(__file__).parent / 'extras' / ('countries.' + suffix)).read_bytes()
            ).hexdigest()
            for suffix in ('shp', 'shx', 'dbf')
        },
    )
    reader.close()


class ScalarNormalizer(Protocol):
    def __call__(self, value: float) -> float: ...


class ScalarColormap(Protocol):
    def __call__(self, value: float) -> tuple[float, float, float, float]: ...


def _colour(cmap: object, norm: object, value: float) -> tuple[float, float, float, float]:
    return cast(ScalarColormap, cmap)(cast(ScalarNormalizer, norm)(value))
