"""Line, scatter, bar, box, and violin contracts on the bundled country estimates."""

from __future__ import annotations

from itertools import pairwise

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from scipy import stats

import astetik as ast

INCOME = {
    'High income: OECD': '#9A7016',
    'High income: nonOECD': '#2A4A70',
    'Upper middle income': '#2D7D60',
    'Lower middle income': '#7D5595',
    'Low income': '#AC4B35',
}
TIERS = {'High income': '#2A4A70', 'Other': '#AC4B35'}
UNITS = {'wealth': 'USD', 'output': 'USD', 'population': 'persons', 'size_class': '1'}
LOG = {'x': {'scale': 'log'}, 'y': {'scale': 'log'}}


def _spec(kind: str, **fields: object) -> dict[str, object]:
    return {'kind': kind, 'key': ['iso3'], 'paper': 'single', 'units': UNITS, **fields}


def _marks(result: ast.EvidenceResult, kind: str) -> pd.DataFrame:
    return result.table[result.table['mark_kind'] == kind]


def _interval(values: pd.Series, confidence: float = 0.95) -> tuple[float, float]:
    half = stats.t.ppf((1 + confidence) / 2, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values))
    return values.mean() - half, values.mean() + half


def test_line_draws_the_declared_mean_and_its_confidence_interval_at_each_x(country_estimates):
    options = {'estimator': 'mean', 'errorbar': 'ci', 'confidence': 0.9, 'marker': 'o'}
    result = ast.render(country_estimates, _spec('line', x='size_class', y='wealth', options=options))
    estimates = _marks(result, 'estimate').set_index('size_class')
    members = country_estimates[country_estimates['size_class'] == 12]['wealth']
    low, high = _interval(members, 0.9)
    assert estimates.loc[12, 'wealth'] == pytest.approx(members.mean())
    assert (estimates.loc[12, 'lower'], estimates.loc[12, 'upper']) == pytest.approx((low, high))
    assert estimates['n'].sum() == len(country_estimates)
    assert 'Student t interval; confidence=0.9' in estimates['computation'].iloc[0]
    axis = result.figure.axes[0]
    assert list(axis.lines[0].get_xdata()) == sorted(country_estimates['size_class'].unique())
    assert len(axis.collections) == 1 and axis.get_legend() is None


def test_line_joins_each_observation_when_no_estimate_is_declared(country_estimates):
    result = ast.render(country_estimates, _spec('line', x='population', y='output', axes=LOG))
    assert len(_marks(result, 'observation')) == len(country_estimates)
    assert np.all(np.diff(result.figure.axes[0].lines[0].get_xdata()) >= 0)


def test_line_groups_are_dashed_keyed_and_counted_exactly_as_drawn(country_estimates):
    options = {'estimator': 'median', 'errorbar': 'iqr', 'interval': 'bars', 'dashes': True,
               'annotate_n': True}
    result = ast.render(
        country_estimates, _spec('line', x='size_class', y='wealth', hue='tier', options=options),
        {'categories': TIERS},
    )
    axis = result.figure.axes[0]
    drawn = [line for line in axis.lines if line.get_linestyle() != 'None']
    assert [line.get_linestyle() for line in drawn] == ['-', '--']
    keys = axis.get_legend().get_lines()
    assert [key.get_linestyle() for key in keys] == ['-', '--']
    assert [key.get_color() for key in keys] == [line.get_color() for line in drawn]
    counts = country_estimates['tier'].value_counts()
    assert {text.get_text() for text in axis.get_legend().get_texts()} == {
        f'{label} (n = {counts[label]})' for label in TIERS
    }
    estimate = _marks(result, 'estimate')
    one = estimate[(estimate['series'] == 'Other') & (estimate['size_class'] == 12)].iloc[0]
    members = country_estimates.query("tier == 'Other' and size_class == 12")['wealth']
    assert (one['lower'], one['upper']) == pytest.approx(tuple(members.quantile([0.25, 0.75])))


def test_line_end_labels_name_each_series_in_its_colour_without_overlapping(country_estimates):
    options = {'estimator': 'median', 'legend_loc': 'end'}
    result = ast.render(
        country_estimates, _spec('line', x='size_class', y='wealth', hue='income', options=options),
        {'categories': INCOME},
    )
    axis = result.figure.axes[0]
    labels = [text for text in axis.texts if text.get_text() in INCOME]
    assert axis.get_legend() is None and len(labels) == len(INCOME)
    for label in labels:
        assert mcolors.to_hex(label.get_color()).upper() == INCOME[label.get_text()]
    result.figure.canvas.draw()
    boxes = sorted((label.get_window_extent() for label in labels), key=lambda box: box.y0)
    assert all(lower.y1 <= upper.y0 + 0.5 for lower, upper in pairwise(boxes))
    assert result.verify()['passed']


@pytest.mark.parametrize(
    'fields,reason',
    [
        ({'options': {'errorbar': 'ci'}}, 'describes a mean'),
        ({'options': {'estimator': 'median', 'errorbar': 'se'}}, 'describes a mean'),
        ({'options': {'estimator': 'mean', 'errorbar': 'iqr'}}, 'describes a median'),
        ({'options': {'estimator': 'sum'}}, 'A line joins observations'),
        ({'options': {'estimator': 'mean', 'sort': False}}, 'ordered by x'),
        ({'options': {'confidence': 1}}, 'confidence must be'),
        ({'options': {'band_alpha': 2}}, 'band_alpha must be'),
        ({'options': {'interval': 'ribbon'}}, 'interval must be one of'),
        ({'options': {'legend_loc': 'middle'}}, 'legend_loc must be one of'),
        ({'options': {'dashes': True, 'linestyle': 'dotted'}}, 'leave linestyle solid'),
        ({'hue': 'income', 'options': {'dashes': True}}, 'at most 4 series'),
        ({'hue': 'income', 'options': {'color': 'ink'}}, 'applies to one series'),
        ({'x': 'population', 'options': {'estimator': 'mean', 'errorbar': 'sd'}}, 'has 1'),
    ],
)
def test_line_orders_that_cannot_be_read_one_way_are_refused(country_estimates, fields, reason):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            country_estimates, _spec('line', **{'x': 'size_class', 'y': 'wealth', **fields}),
            {'categories': INCOME},
        )
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']


def test_fit_is_a_straight_line_in_the_displayed_scale_with_its_band(country_estimates):
    options = {'annotate_fit': True, 'confidence': 0.9}
    result = ast.render(
        country_estimates, _spec('regs', x='population', y='output', axes=LOG, options=options)
    )
    x, y = np.log10(country_estimates['population']), np.log10(country_estimates['output'])
    expected = stats.linregress(x, y)
    method = result.receipt['methods']['plot']['regression']
    assert (method['slope'], method['intercept']) == pytest.approx(
        (expected.slope, expected.intercept)
    )
    assert method['scale'] == {'x': 'log10', 'y': 'log10'}
    assert method['band'].startswith('0.9 confidence band')
    line = _marks(result, 'regression')
    assert np.all(line['lower'] < line['predicted_y']) and np.all(line['predicted_y'] < line['upper'])
    assert np.allclose(np.diff(np.log10(line['predicted_y'])) / np.diff(np.log10(line['x'])), expected.slope)
    note = result.figure.axes[0].get_legend().get_texts()[0].get_text()
    assert note == f'r = {expected.rvalue:.2f}, p < 0.001, n = {len(country_estimates)}'


def test_group_fits_are_recorded_and_keyed_per_group_in_the_declared_order(country_estimates):
    order = list(INCOME)
    options = {'fit_groups': True, 'annotate_fit': True}
    result = ast.render(
        country_estimates,
        _spec('regs', x='population', y='output', hue='income', hue_order=order, axes=LOG,
              options=options),
        {'categories': INCOME},
    )
    fits = result.receipt['methods']['plot']['regression_by_group']
    assert [fit['group'] for fit in fits] == order
    assert sum(fit['n'] for fit in fits) == len(country_estimates)
    labels = [text.get_text() for text in result.figure.axes[0].get_legend().get_texts()]
    assert [label.split(' (r = ')[0] for label in labels] == order
    assert labels[0].endswith(f'n = {fits[0]["n"]})')


def test_scatter_key_is_painted_as_its_points_and_never_covers_one(country_estimates):
    options = {'alpha': 0.4, 'point_size': 30.0, 'edgewidth': 0.5}
    result = ast.render(
        country_estimates,
        _spec('scat', x='population', y='output', hue='income', axes=LOG, options=options),
        {'categories': INCOME},
    )
    axis = result.figure.axes[0]
    legend = axis.get_legend()
    key = legend.legend_handles[0]
    assert key.get_alpha() == 0.4 and key.get_markersize() == pytest.approx(np.sqrt(30.0))
    assert key.get_markeredgewidth() == 0.5
    result.figure.canvas.draw()
    box = legend.get_window_extent()
    points = np.vstack([
        c.get_offset_transform().transform(c.get_offsets())
        for c in axis.collections if isinstance(c, PathCollection)
    ])
    inside = (
        (points[:, 0] > box.x0) & (points[:, 0] < box.x1)
        & (points[:, 1] > box.y0) & (points[:, 1] < box.y1)
    )
    assert not inside.any()


@pytest.mark.parametrize(
    'kind,fields,reason',
    [
        ('regs', {'options': {'fit_groups': True}}, 'declare hue'),
        ('regs', {'options': {'fit_reg': False, 'annotate_fit': True}}, 'enable fit_reg'),
        ('scat', {'hue': 'income', 'hue_order': ['Low income']}, 'every observed hue group'),
        ('scat', {'hue_order': ['Low income']}, 'hue_order orders the hue groups'),
        ('scat', {'hue': 'income', 'options': {'legend_loc': 'center'}}, 'legend_loc must be'),
        ('scat', {'options': {'edgecolor': 'bleu'}}, 'manifest colour role'),
        ('regs', {'axes': {'x': {'scale': 'symlog'}}}, 'a symlog axis has none'),
        ('scat', {'hue': 'wealth', 'options': {'hue_mode': 'continuous', 'color': 'ink'}},
         'a continuous hue colours the points'),
    ],
)
def test_scatter_orders_with_no_single_reading_are_refused(country_estimates, kind, fields, reason):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            country_estimates,
            _spec(kind, **{'x': 'population', 'y': 'output', 'axes': LOG, **fields}),
            {'categories': INCOME},
        )
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']


@pytest.mark.parametrize('orient', ['v', 'h'])
def test_bar_interval_is_the_declared_one_and_the_axis_ends_on_a_tick_above_it(
    country_estimates, orient
):
    options = {'estimator': 'mean', 'errorbar': 'ci', 'annotate_n': True, 'orient': orient}
    result = ast.render(country_estimates, _spec('bar', x='income', y='wealth', options=options))
    bars = _marks(result, 'aggregate').set_index('category')
    members = country_estimates[country_estimates['income'] == 'Low income']['wealth']
    assert bars.loc['Low income', 'estimate'] == pytest.approx(members.mean())
    assert (bars.loc['Low income', 'lower'], bars.loc['Low income', 'upper']) == pytest.approx(
        _interval(members)
    )
    axis = result.figure.axes[0]
    value, names = (axis.xaxis, axis.yaxis) if orient == 'h' else (axis.yaxis, axis.xaxis)
    low, high = value.get_view_interval()
    assert low == 0 and high >= bars['upper'].max() and high in value.get_ticklocs()
    labels = {' '.join(tick.get_text().split()) for tick in names.get_ticklabels()}
    assert labels == {f'{category} n = {count}' for category, count in bars['n'].items()}
    assert result.verify()['passed']


def test_bar_shows_every_observation_over_its_summary_when_asked(country_estimates):
    options = {'estimator': 'median', 'errorbar': 'iqr', 'points': 'all', 'color': 'secondary'}
    result = ast.render(country_estimates, _spec('bar', x='income', y='wealth', options=options))
    assert len(_marks(result, 'observation')) == len(country_estimates)
    assert len(_marks(result, 'aggregate')) == country_estimates['income'].nunique()
    bar = result.figure.axes[0].patches[0]
    assert bar.get_facecolor()[:3] == pytest.approx(mcolors.to_rgb(ast.Manifest().colors['secondary']))
    assert 'linear quantiles 0.25 and 0.75' in _marks(result, 'aggregate')['computation'].iloc[0]


def test_grouped_bars_follow_the_declared_group_order_and_key(country_estimates):
    options = {'estimator': 'mean', 'errorbar': 'se', 'alpha': 0.6}
    result = ast.render(
        country_estimates,
        _spec('bar', x='income', y='wealth', hue='tier', hue_order=['Other', 'High income'],
              paper='double', options=options),
        {'categories': TIERS},
    )
    legend = result.figure.axes[0].get_legend()
    assert [text.get_text() for text in legend.get_texts()] == ['Other', 'High income']
    assert legend.get_patches()[0].get_alpha() == 0.6
    assert set(_marks(result, 'aggregate')['series']) == set(TIERS)


@pytest.mark.parametrize('points', ['outliers', 'all'])
def test_box_quartiles_whiskers_and_shown_observations_are_exact(country_estimates, points):
    options = {'points': points, 'means': True, 'whis': 1.5}
    result = ast.render(
        country_estimates,
        _spec('box', x='income', y='wealth', axes={'y': {'scale': 'log'}}, options=options),
    )
    boxes = _marks(result, 'box').set_index('category')
    members = country_estimates[country_estimates['income'] == 'Low income']['wealth']
    q1, median, q3 = members.quantile([0.25, 0.5, 0.75])
    row = boxes.loc['Low income']
    assert (row['q1'], row['median'], row['q3'], row['mean']) == pytest.approx(
        (q1, median, q3, members.mean())
    )
    inside = members[(members >= q1 - 1.5 * (q3 - q1)) & (members <= q3 + 1.5 * (q3 - q1))]
    assert (row['lower_whisker'], row['upper_whisker']) == (inside.min(), inside.max())
    if points == 'all':
        assert len(_marks(result, 'observation')) == len(country_estimates)
        assert _marks(result, 'outlier').empty
    else:
        outliers = _marks(result, 'outlier')
        beyond = outliers[outliers['category'] == 'Low income']['value']
        assert sorted(beyond) == sorted(members[(members < inside.min()) | (members > inside.max())])


def test_box_and_violin_keys_are_painted_as_their_shapes(country_estimates):
    for kind, extra in (('box', {}), ('violin', {'split': True, 'inner': 'quartiles'})):
        result = ast.render(
            country_estimates,
            _spec(kind, x='income', y='wealth', hue='tier', paper='double',
                  axes={'y': {'scale': 'log'}}, options={'alpha': 0.5, **extra}),
            {'categories': TIERS},
        )
        key = result.figure.axes[0].get_legend().get_patches()[0]
        assert key.get_facecolor() == pytest.approx(mcolors.to_rgba(TIERS['High income'], 0.5))
        assert key.get_edgecolor() == pytest.approx(mcolors.to_rgba(TIERS['High income']))
        assert result.verify()['passed']


def test_violin_density_is_estimated_in_the_displayed_scale_with_quartiles_inside(
    country_estimates,
):
    spec = _spec('violin', x='tier', y='wealth', options={'points': 'all'})
    linear = ast.render(country_estimates, spec)
    logarithmic = ast.render(country_estimates, {**spec, 'axes': {'y': {'scale': 'log'}}})
    assert 'log10' not in _marks(linear, 'density')['computation'].iloc[0]
    assert 'Gaussian KDE of log10 values' in _marks(logarithmic, 'density')['computation'].iloc[0]
    members = country_estimates[country_estimates['tier'] == 'Other']['wealth']
    inner = _marks(logarithmic, 'box').set_index('category').loc['Other']
    assert (inner['q1'], inner['median'], inner['q3']) == pytest.approx(
        tuple(members.quantile([0.25, 0.5, 0.75]))
    )
    assert len(_marks(logarithmic, 'observation')) == len(country_estimates)
    support = _marks(logarithmic, 'density').query("category == 'Other'")['value']
    assert support.min() == pytest.approx(members.min()) and support.max() == pytest.approx(members.max())


@pytest.mark.parametrize(
    'kind,fields,reason',
    [
        ('bar', {'options': {'estimator': 'mean', 'errorbar': 'iqr'}}, 'describes a median'),
        ('bar', {'options': {'estimator': None}}, "estimator must be"),
        ('bar', {'options': {'points': 'outliers'}}, 'points must be one of'),
        ('bar', {'options': {'capsize': -1}}, 'capsize must be'),
        ('box', {'options': {'points': 'none'}}, 'points must be one of'),
        ('box', {'options': {'means': 'yes'}}, 'means must be a boolean'),
        ('violin', {'options': {'inner': 'stick'}}, 'inner must be one of'),
        ('violin', {'hue': 'income', 'options': {'split': True}}, 'exactly two hue categories'),
        ('box', {'hue': 'income', 'options': {'color': 'ink'}}, 'applies to one series'),
    ],
)
def test_category_orders_with_no_single_reading_are_refused(country_estimates, kind, fields, reason):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            country_estimates, _spec(kind, x='tier', y='wealth', **fields), {'categories': INCOME}
        )
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']


def test_continuous_hue_points_carry_the_declared_edge(country_estimates):
    def points(**options: object):
        spec = _spec('scat', x='population', y='output', hue='wealth', axes=LOG,
                     options={'hue_mode': 'continuous', **options})
        return ast.render(country_estimates, spec).figure.axes[0].collections[0]

    assert list(points(edgewidth=0.0).get_linewidths()) == [0.0]
    styled = points(edgecolor='secondary', edgewidth=0.8)
    assert list(styled.get_linewidths()) == [0.8]
    assert styled.get_edgecolors()[0][:3] == pytest.approx(
        mcolors.to_rgb(ast.Manifest().colors['secondary'])
    )
    automatic = points().get_edgecolors()[0][:3]
    assert automatic == pytest.approx(mcolors.to_rgb(ast.Manifest().colors['ink']))


def test_legend_headroom_never_replaces_declared_axis_limits(country_estimates):
    spec = _spec('bar', x='income', y='wealth', hue='tier', paper='double',
                 options={'estimator': 'mean', 'points': 'all', 'legend_loc': 'upper left'})
    highest = float(country_estimates['wealth'].max())
    declared = float(np.ceil(highest / 1e4) * 1e4)
    free = ast.render(country_estimates, spec, {'categories': TIERS})
    assert free.figure.axes[0].get_ylim()[1] > declared
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(
            country_estimates, {**spec, 'axes': {'y': {'limits': [0, declared]}}},
            {'categories': TIERS},
        )
    assert 'within the declared y limits' in caught.value.details['reason']


def test_a_marker_on_a_connected_line_counts_as_a_mark_for_legend_clearance():
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure
    from matplotlib.transforms import Bbox

    from astetik._presentation_clearance import covered

    figure = Figure(figsize=(3, 2), dpi=100)
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    axis.plot([0, 1], [0, 0], marker='o', markersize=20)
    axis.set_xlim(-1, 2)
    axis.set_ylim(-1, 1)
    figure.canvas.draw()
    x, y = axis.transData.transform((1, 0))
    assert covered(axis, Bbox.from_bounds(x + 5, y - 2, 4, 4))
    assert not covered(axis, Bbox.from_bounds(x + 40, y - 2, 4, 4))
