"""Sectors rendering with explicit scientific provenance."""

from __future__ import annotations

from typing import cast

import numpy as np
from scipy.integrate import trapezoid

from ._plot_backend import drawing
from ._render_common import (
    color_mapping,
    equal,
    figure_for,
    legend,
    levels,
    numerical,
    scalar,
)
from ._render_context import (
    RenderContext,
    RowArray,
)
from ._types import JsonScalar


def pie(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    x, y = spec.get('x'), spec.get('y')
    labels: list[JsonScalar]
    records: list[tuple[JsonScalar, float, RowArray, str]]
    if isinstance(x, list):
        labels = list(x)
        records = [(c, float(numerical(data.iloc[rows][c], c).sum()), rows, 'sum') for c in x]
    elif y:
        labels = spec.get('order') or levels(data[x])
        records = []
        for label in labels:
            r = rows[equal(data.iloc[rows][x], label)]
            records.append(
                (
                    label,
                    float(numerical(data.iloc[r][context.column('y')], context.column('y')).sum()),
                    r,
                    'sum',
                )
            )
    else:
        labels = spec.get('order') or levels(data[x])
        records = [
            (label, float(len(r)), r, 'row count')
            for label in labels
            for r in [rows[equal(data.iloc[rows][x], label)]]
        ]
    values = np.asarray([r[1] for r in records])
    if np.any(values < 0) or values.sum() <= 0:
        raise ValueError('Pie requires nonnegative values with a positive total.')
    mapping = color_mapping(spec['_manifest'], labels, spec['_paper'])
    drawing(ax).pie(
        values,
        labels=[str(v) for v in labels],
        colors=[mapping[v] for v in labels],
        startangle=options.get('startangle', 90.0),
        autopct='%1.1f%%' if options.get('percent', True) else None,
        textprops=dict(fontsize=cast(float, getattr(figure_for(ax), '_astetik_font_size'))),
        wedgeprops=dict(edgecolor=colors.manifest.colors['paper'], linewidth=0.7),
    )
    ax.set_aspect('equal')
    for label, value, r, comp in records:
        rec.mark(
            'sector',
            dict(
                category=label,
                value=value,
                fraction=value / values.sum(),
                total=values.sum(),
                category_source_rows=[int(p) for p in r],
            ),
            rows,
            f'{comp}; fraction denominator uses all displayed sectors',
            facet,
        )
    rec.methods['pie'] = {
        'normalization': 'fraction of the displayed sum',
        'total': float(values.sum()),
    }


def roc(context: RenderContext) -> None:
    ax = context.ax
    data = context.data
    rows = context.rows
    spec = context.spec
    options = context.options
    colors = context.colors
    rec = context.rec
    facet = context.facet
    truth, scores = (
        np.asarray(data.iloc[rows][context.column('x')]),
        numerical(data.iloc[rows][context.column('y')], context.column('y')),
    )
    labels = levels(truth)
    if len(labels) != 2 or options.get('positive_label', 1) not in labels:
        raise ValueError(
            'ROC requires two truth classes and a declared positive_label present in the data.'
        )
    positive = truth == options.get('positive_label', 1)
    sort = np.argsort(-scores, kind='stable')
    ordered_scores, ordered_truth = scores[sort], positive[sort]
    endpoints = np.r_[np.flatnonzero(np.diff(ordered_scores)), len(rows) - 1]
    tp = np.r_[0, np.cumsum(ordered_truth)[endpoints]]
    fp = np.r_[0, np.cumsum(~ordered_truth)[endpoints]]
    tpr, fpr = tp / positive.sum(), fp / (~positive).sum()
    thresholds = [None, *ordered_scores[endpoints].tolist()]
    auc = float(trapezoid(tpr, fpr))
    drawing(ax).plot(
        [0, 1], [0, 1], color=colors.manifest.colors['muted'], linestyle='--', linewidth=0.7
    )
    drawing(ax).plot(
        fpr,
        tpr,
        color=colors.primary,
        linewidth=options.get('linewidth', 1.25),
        label=f'AUC = {auc:.3f}',
    )
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel='False positive rate', ylabel='True positive rate')
    ax.set_aspect('equal')
    legend(ax, spec, {})
    if spec.get('legend', True):
        drawing(ax).legend(frameon=False, loc='lower right')
    for f, t, threshold, tpv, fpv in zip(fpr, tpr, thresholds, tp, fp):
        rec.mark(
            'roc',
            dict(
                fpr=f, tpr=t, threshold=threshold, true_positive=int(tpv), false_positive=int(fpv)
            ),
            rows,
            'stable descending-score threshold sweep; scores >= threshold; initial threshold above all scores',
            facet,
        )
    rec.methods['roc'] = dict(
        positive_label=scalar(options.get('positive_label', 1)),
        auc=auc,
        auc_method='trapezoidal integration',
        positives=int(positive.sum()),
        negatives=int((~positive).sum()),
    )
