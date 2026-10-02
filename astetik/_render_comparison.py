"""Validated comparison estimates and confidence intervals beside observations."""

from __future__ import annotations

from typing import TypedDict, cast

import numpy as np
import pandas as pd

from ._plot_backend import drawing
from ._render_common import (
    category_axes,
    color_mapping,
    equal,
    levels,
    numerical,
)
from ._render_context import (
    RenderContext,
)
from ._render_positions import van_der_corput
from ._types import JsonObject, JsonScalar


def comparison(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    rec = context.rec
    facet = context.facet
    analysis = context.analysis
    if not analysis or 'summary' not in analysis:
        raise ValueError('comparison requires a validated numerical analysis summary.')
    category, value = context.column('x'), context.column('y')
    categories = spec.get('order') or levels(data[category])
    mapping = color_mapping(spec['_manifest'], categories, spec['_paper'])
    summary = _summary(analysis)
    for i, label in enumerate(categories):
        r = rows[equal(data.iloc[rows][category], label)]
        values = numerical(data.iloc[r][value], value)
        jitter = np.asarray([(van_der_corput(j + 1) - 0.5) * 0.24 for j in range(len(r))])
        drawing(ax).scatter(
            np.full(len(r), i) + jitter,
            values,
            color=mapping[label],
            s=options.get('point_size', 18.0),
            alpha=options.get('alpha', 0.85),
            edgecolors='none',
        )
        for p, v, offset in zip(r, values, jitter):
            rec.mark(
                'observation',
                dict(group=label, value=v, display_offset=offset),
                [int(p)],
                'identity; deterministic categorical jitter',
                facet,
            )
        record = next((s for s in summary if s['group'] == label), None)
        if record is None:
            raise ValueError(f'Comparison summary missing group {label!r}.')
        estimate, lower, upper = record['estimate'], record['lower'], record['upper']
        drawing(ax).errorbar(
            i + 0.3,
            estimate,
            yerr=np.asarray([[estimate - lower], [upper - estimate]]),
            color=mapping[label],
            marker='D',
            markersize=4,
            linewidth=options.get('linewidth', 1.25),
            capsize=2,
        )
        rec.mark(
            'estimate',
            dict(group=label, estimate=estimate, lower=lower, upper=upper, n=record['n']),
            r,
            'validated comparison estimate and declared confidence interval',
            facet,
        )
    category_axes(ax, categories, False)
    ax.set_xlim(-0.5, len(categories) - 0.3)
    drawing(ax).set_xlabel(str(category))
    drawing(ax).set_ylabel(str(value))
    rec.methods['comparison'] = {k: v for k, v in analysis.items() if k != 'summary'}


class ComparisonSummary(TypedDict):
    group: JsonScalar
    n: int
    estimate: float
    lower: float
    upper: float


def _summary(analysis: JsonObject) -> list[ComparisonSummary]:
    source: object = analysis['summary']
    if isinstance(source, pd.DataFrame):
        source = source.to_dict('records')
    if not isinstance(source, list):
        raise ValueError('Comparison summary must contain group records.')
    result: list[ComparisonSummary] = []
    for value in cast(list[object], source):
        if not isinstance(value, dict):
            raise ValueError('Comparison summary must contain group objects.')
        record = cast(dict[str, object], value)
        if not all(
            isinstance(record.get(key), (int, float)) for key in ('estimate', 'lower', 'upper', 'n')
        ):
            raise ValueError('Comparison estimates, interval endpoints and n must be numerical.')
        result.append(cast(ComparisonSummary, record))
    return result
