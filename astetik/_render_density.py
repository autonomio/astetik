"""Gaussian density estimates with shared grids and recorded fit parameters."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from scipy import stats

from ._plot_backend import colorbar_figure, drawing
from ._render_common import figure_for, groups, legend, numerical, scalar, zero_baseline
from ._render_context import (
    DensityFit,
    FacetPlan,
    RenderContext,
    RendererOptions,
    RendererSpec,
    required_column,
)
from ._types import FloatArray, JsonObject


def calculate_density(
    values: FloatArray, options: RendererOptions, name: str
) -> tuple[FloatArray, FloatArray, float]:
    if len(values) < 2 or np.ptp(values) == 0:
        raise ValueError(f'KDE for {name!r} requires at least two distinct observations.')
    try:
        estimate = stats.gaussian_kde(values, bw_method=options.get('bw_method', 'scott'))
    except (ValueError, np.linalg.LinAlgError) as exc:
        raise ValueError(f'KDE for {name!r} has singular covariance.') from exc
    bandwidth = float(np.sqrt(estimate.covariance[0, 0]))
    cut = options.get('cut', 0.0)
    support = np.linspace(
        float(values.min()) - cut * bandwidth,
        float(values.max()) + cut * bandwidth,
        options.get('gridsize', 128),
    )
    density = cast(FloatArray, estimate(support))
    if options.get('cumulative', False):
        density = np.asarray([estimate.integrate_box_1d(-np.inf, v) for v in support])
    return support, density, bandwidth


def kde(context: RenderContext) -> None:
    if context.spec.get('y'):
        _kde2d(context)
        return
    x, hue = context.column('x'), context.spec.get('hue')
    options, colors, rec = context.options, context.colors, context.rec
    mapping = context.spec['_hue_colors']
    for label, rows in groups(context.data, context.rows, hue):
        values = numerical(context.data.iloc[rows][x], x)
        support, density, bandwidth = calculate_density(values, options, x)
        color = mapping.get(label, colors.primary)
        drawing(context.ax).plot(support, density, color=color, linewidth=1.25)
        if options.get('fill', True):
            drawing(context.ax).fill_between(
                support, density, color=color, alpha=options.get('alpha', 0.85)
            )
        for xv, value in zip(support, density):
            rec.mark(
                'density',
                dict(series=label, x=xv, density=value, bandwidth=bandwidth),
                rows,
                f'Gaussian KDE; bandwidth={options.get("bw_method", "scott")}; cumulative={options.get("cumulative", False)}',
                context.facet,
            )
    rec.methods['kde'] = dict(
        dimensions=1,
        bandwidth_method=options.get('bw_method', 'scott'),
        gridsize=options.get('gridsize', 128),
        cut=options.get('cut', 0.0),
        cumulative=options.get('cumulative', False),
    )
    zero_baseline(context.ax, False, [])
    drawing(context.ax).set_xlabel(x)
    drawing(context.ax).set_ylabel(
        'Cumulative probability' if options.get('cumulative', False) else 'Density'
    )
    legend(context.ax, context.spec, mapping)


def _kde2d(context: RenderContext) -> None:
    spec, options, rec = context.spec, context.options, context.rec
    if options.get('cumulative', False):
        raise ValueError('Cumulative two-dimensional KDE is not supported.')
    if spec.get('hue'):
        raise ValueError('Two-dimensional KDE does not support hue; use facets.')
    fits, domain = spec.get('_kde2d'), spec.get('_kde2d_domain')
    if fits is None or domain is None:
        raise ValueError('Two-dimensional KDE requires prepared facet estimates.')
    cached = fits[tuple(int(p) for p in context.rows)]
    xx, yy, density = cached.xx, cached.yy, cached.density
    if xx is None or yy is None or density is None:
        raise ValueError('Two-dimensional KDE estimate lacks its shared grid.')
    levels = np.linspace(domain[0], domain[1], 9)
    artist = drawing(context.ax)
    contour = (artist.contourf if options.get('fill', True) else artist.contour)(
        xx, yy, density, levels=levels, cmap=context.colors.sequential(), norm=Normalize(*domain)
    )
    colorbar_figure(figure_for(context.ax)).colorbar(contour, ax=context.ax, label='Density')
    for xv, yv, value in zip(xx.ravel(), yy.ravel(), density.ravel()):
        rec.mark(
            'density',
            dict(x=xv, y=yv, density=value),
            context.rows,
            f'2D Gaussian KDE; bandwidth={options.get("bw_method", "scott")}',
            context.facet,
        )
    rec.methods['kde'] = dict(
        dimensions=2,
        bandwidth_method=options.get('bw_method', 'scott'),
        gridsize=options.get('gridsize', 128),
        cut=options.get('cut', 0.0),
        shared_colour_domain=list(domain),
        contour_levels=levels.tolist(),
    )
    fit_record: JsonObject = dict(
        facet={k: scalar(v) for k, v in context.facet.items()},
        covariance=cast(FloatArray, cached.model.covariance).tolist(),
        source_rows=[int(p) for p in context.rows],
    )
    rec.append_method('kde_fits', fit_record)
    artist.set_xlabel(context.column('x'))
    artist.set_ylabel(context.column('y'))


def prepare_kde2d(
    data: pd.DataFrame, spec: RendererSpec, options: RendererOptions, facets: FacetPlan
) -> tuple[dict[tuple[int, ...], DensityFit], tuple[float, float]]:
    if options.get('cumulative', False):
        raise ValueError('Cumulative two-dimensional KDE is not supported.')
    if spec.get('hue'):
        raise ValueError('Two-dimensional KDE does not support hue; use facets.')
    x, y = required_column(spec, 'x'), required_column(spec, 'y')
    fitted: dict[tuple[int, ...], DensityFit] = {}
    for _, rows, _ in facets:
        if not len(rows):
            continue
        values = np.vstack((numerical(data.iloc[rows][x], x), numerical(data.iloc[rows][y], y)))
        try:
            model = stats.gaussian_kde(values, bw_method=options.get('bw_method', 'scott'))
        except (ValueError, np.linalg.LinAlgError) as exc:
            raise ValueError(
                'Two-dimensional KDE requires nonsingular covariance in every facet.'
            ) from exc
        fitted[tuple(int(p) for p in rows)] = DensityFit(model)
    largest = np.max(
        [np.sqrt(np.diag(cast(FloatArray, item.model.covariance))) for item in fitted.values()],
        axis=0,
    )
    xv, yv = numerical(data[x], x), numerical(data[y], y)
    cut, size = options.get('cut', 0.0), options.get('gridsize', 128)
    gx = np.linspace(float(xv.min() - cut * largest[0]), float(xv.max() + cut * largest[0]), size)
    gy = np.linspace(float(yv.min() - cut * largest[1]), float(yv.max() + cut * largest[1]), size)
    xx, yy = np.meshgrid(gx, gy)
    positions = np.vstack((xx.ravel(), yy.ravel()))
    maximum = 0.0
    for item in fitted.values():
        density = cast(FloatArray, item.model(positions)).reshape(xx.shape)
        item.xx, item.yy, item.density = xx, yy, density
        maximum = max(maximum, float(density.max()))
    return fitted, (0.0, maximum)
