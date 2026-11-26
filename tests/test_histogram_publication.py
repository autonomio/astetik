"""Publication histogram contracts on the bundled country and area attributes."""

from __future__ import annotations

from importlib.resources import as_file, files

import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import pytest
import shapefile

import astetik as ast

GROUPS = {
    'High income: OECD': '#9A7016',
    'High income: nonOECD': '#2A4A70',
    'Upper middle income': '#2D7D60',
    'Lower middle income': '#7D5595',
    'Low income': '#AC4B35',
}


@pytest.fixture(scope='module')
def countries() -> pd.DataFrame:
    """Natural Earth estimates shipped with the package; sentinel rows are excluded."""
    with as_file(files('astetik').joinpath('extras', 'countries.dbf')) as source:
        records = shapefile.Reader(str(source.with_suffix(''))).records()
    frame = pd.DataFrame([record.as_dict() for record in records])
    kept = frame[(frame['POP_EST'] > 0) & (frame['GDP_MD_EST'] > 0)]
    return pd.DataFrame(
        {
            'iso3': kept['ADM0_A3'],
            'income': kept['INCOME_GRP'].str.replace(r'^\d\. ', '', regex=True),
            'population': kept['POP_EST'],
            'wealth': kept['GDP_MD_EST'] * 1e6 / kept['POP_EST'],
        }
    ).reset_index(drop=True)


def _spec(**fields: object) -> dict[str, object]:
    return {
        'kind': 'hist',
        'x': 'wealth',
        'key': ['iso3'],
        'paper': 'single',
        'units': {'wealth': 'USD', 'population': 'persons'},
        **fields,
    }


def _bins(result: ast.EvidenceResult) -> pd.DataFrame:
    return result.table[result.table['mark_kind'] == 'bin']


@pytest.mark.parametrize(
    'options,total',
    [
        ({'stat': 'proportion'}, 1.0),
        ({'stat': 'percent'}, 100.0),
        ({'stat': 'proportion', 'cumulative': True}, None),
        ({'stat': 'count'}, None),
    ],
)
def test_each_statistic_accounts_for_every_observation(countries, options, total):
    result = ast.render(countries, _spec(options=options))
    values = _bins(result)['value'].to_numpy(float)
    if options.get('cumulative'):
        assert values[-1] == pytest.approx(1.0)
        assert np.all(np.diff(values) >= 0)
    elif total is None:
        assert values.sum() == len(countries)
        assert all(isinstance(value, int) for value in _bins(result)['value'])
    else:
        assert values.sum() == pytest.approx(total)
    label = result.figure.axes[0].get_ylabel()
    assert label == {'count': 'Count', 'percent': 'Percent'}.get(
        options['stat'], 'Cumulative proportion' if options.get('cumulative') else 'Proportion'
    )


def test_density_integrates_to_one_and_carries_its_estimate(countries):
    options = {'density': True, 'kde': True, 'bw_method': 'silverman', 'rug': True}
    result = ast.render(countries, _spec(options=options))
    bins = _bins(result)
    assert (bins['value'] * (bins['upper'] - bins['lower'])).sum() == pytest.approx(1.0)
    assert result.receipt['methods']['plot']['histogram']['statistic'] == 'density'
    kinds = set(result.table['mark_kind'])
    assert {'bin', 'density', 'rug'} <= kinds
    assert result.figure.axes[0].get_ylabel() == 'Density (1/USD)'


def test_bin_width_yields_aligned_boundaries_covering_the_data(countries):
    result = ast.render(countries, _spec(options={'binwidth': 10000}))
    edges = np.asarray(result.receipt['methods']['plot']['histogram']['bins'])
    assert np.allclose(np.diff(edges), 10000)
    assert np.allclose(edges % 10000, 0)
    assert edges[0] <= countries['wealth'].min() and edges[-1] >= countries['wealth'].max()


def test_an_infinite_bin_count_is_refused_as_a_plot_contract_error():
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(pd.DataFrame({'value': [0.0, 1.0]}),
                   {'kind': 'hist', 'x': 'value', 'options': {'binwidth': 1e-309}})
    assert caught.value.code == 'PLOT_CONTRACT'
    assert 'inf bins' in caught.value.details['reason']
    assert 'Declare coarser bins' in caught.value.details['reason']


def test_log_axis_bins_are_even_in_the_displayed_scale(countries):
    result = ast.render(
        countries, _spec(x='population', axes={'x': {'scale': 'log'}}, options={'bins': 12})
    )
    method = result.receipt['methods']['plot']['histogram']
    steps = np.diff(np.log10(method['bins']))
    assert method['log_bins'] is True
    assert np.allclose(steps, steps[0])
    axis = result.figure.axes[0]
    labels = [tick.get_text() for tick in axis.get_xticklabels() if tick.get_text()]
    assert labels and all('$' not in label and label.startswith('10') for label in labels)


def test_value_axis_ends_on_a_whole_labelled_tick(countries):
    result = ast.render(countries, _spec(x='population', axes={'x': {'scale': 'log'}}))
    axis = result.figure.axes[0]
    top = axis.get_ylim()[1]
    ticks = axis.get_yticks()
    assert top in ticks
    assert top >= _bins(result)['value'].max()
    assert np.allclose(ticks, np.round(ticks))


def test_large_linear_values_are_printed_whole_and_grouped(countries):
    result = ast.render(countries, _spec(options={'density': True, 'binwidth': 10000}))
    axis = result.figure.axes[0]
    x = [tick.get_text() for tick in axis.get_xticklabels()]
    y = [tick.get_text() for tick in axis.get_yticklabels()]
    assert '100\N{NO-BREAK SPACE}000' in x
    assert all('e' not in label for label in x + y)
    assert axis.yaxis.get_offset_text().get_text() == ''


def _clear(result: ast.EvidenceResult) -> bool:
    axis = result.figure.axes[0]
    legend = axis.get_legend()
    result.figure.canvas.draw()
    box = legend.get_window_extent()
    return not any(
        patch.get_transform().transform_path(patch.get_path()).intersects_bbox(box, filled=True)
        for patch in axis.patches
    )


@pytest.mark.parametrize(
    'options',
    [
        {},
        {'element': 'step', 'alpha': 0.3, 'stat': 'proportion'},
        {'multiple': 'stack', 'legend_loc': 'upper left'},
        {'multiple': 'dodge', 'bins': 6, 'legend_loc': 'outside top', 'annotate_n': True},
        {'multiple': 'stack', 'orient': 'h', 'legend_loc': 'outside right'},
    ],
)
def test_legend_never_covers_a_bin(countries, options):
    scale = {'y' if options.get('orient') == 'h' else 'x': {'scale': 'log'}}
    result = ast.render(
        countries, _spec(hue='income', axes=scale, options=options), {'categories': GROUPS}
    )
    assert _clear(result)
    assert result.verify()['passed']


def test_legend_key_is_painted_as_its_bins(countries):
    options = {'element': 'step', 'alpha': 0.3}
    result = ast.render(countries, _spec(hue='income', options=options), {'categories': GROUPS})
    legend = result.figure.axes[0].get_legend()
    for key, text in zip(legend.get_patches(), legend.get_texts()):
        expected = mcolors.to_rgba(GROUPS[text.get_text()], 0.3)
        assert key.get_facecolor() == pytest.approx(expected)
        assert key.get_edgecolor() == pytest.approx(mcolors.to_rgba(GROUPS[text.get_text()]))
    bars = ast.render(countries, _spec(options={'alpha': 0.6, 'annotate_n': True}))
    note = bars.figure.axes[0].get_legend().get_texts()[0].get_text()
    assert note == f'n = {len(countries)}'


def test_stacked_shares_total_the_pooled_sample(countries):
    options = {'multiple': 'stack', 'stat': 'proportion', 'common_norm': True}
    result = ast.render(countries, _spec(hue='income', options=options), {'categories': GROUPS})
    assert _bins(result)['value'].sum() == pytest.approx(1.0)
    assert 'N pooled across series' in _bins(result)['computation'].iloc[0]


def test_reference_rules_record_the_statistic_and_stop_at_the_tallest_bin(countries):
    result = ast.render(countries, _spec(options={'reference': ['mean', 'median']}))
    marks = result.table[result.table['mark_kind'] == 'reference'].set_index('statistic')
    assert marks.loc['mean', 'value'] == pytest.approx(countries['wealth'].mean())
    assert marks.loc['median', 'value'] == pytest.approx(countries['wealth'].median())
    rules = result.figure.axes[0].collections
    tallest = _bins(result)['value'].max()
    assert all(segment[1][1] == tallest for rule in rules for segment in rule.get_segments())


@pytest.mark.parametrize(
    'fields,reason',
    [
        ({'options': {'density': True, 'stat': 'percent'}}, 'conflicts with stat'),
        ({'options': {'binwidth': 5000, 'bins': 10}}, 'bins or binwidth'),
        ({'options': {'binwidth': 1}}, 'cannot be printed'),
        ({'options': {'bins': 5000}}, 'cannot be printed'),
        ({'options': {'binwidth': 0}}, 'binwidth must be'),
        ({'options': {'stat': 'frequency'}}, 'stat must be one of'),
        ({'options': {'shrink': 1.5}}, 'shrink must be'),
        ({'options': {'edgewidth': -1}}, 'edgewidth must be'),
        ({'options': {'fill': False, 'edgewidth': 0}}, 'needs edgewidth'),
        ({'options': {'reference': ['mode']}}, 'reference must list'),
        ({'options': {'rug': 'yes'}}, 'rug must be a boolean'),
        ({'options': {'color': 'bleu'}}, 'manifest colour role'),
        ({'options': {'color': 5}}, 'color must be'),
        ({'options': {'edgecolor': None}}, 'edgecolor must be'),
        ({'options': {'cumulative': True, 'density': True}}, 'cumulative applies'),
        ({'options': {'element': 'step', 'shrink': 0.8}}, 'apply to bars'),
        ({'options': {'multiple': 'stack'}}, 'requires hue groups'),
        ({'legend': False, 'options': {'annotate_n': True}}, 'enable legend'),
        ({'axes': {'x': {'scale': 'log'}}, 'options': {'binwidth': 5000}}, 'binwidth is linear'),
        (
            {'axes': {'x': {'scale': 'log'}}, 'options': {'kde': True, 'density': True}},
            'linear measurement axis',
        ),
        ({'hue': 'income', 'options': {'color': 'ink'}}, 'applies to one series'),
        ({'hue': 'income', 'options': {'multiple': 'stack', 'kde': True, 'density': True}}, 'KDE'),
        ({'hue': 'income', 'options': {'multiple': 'stack', 'stat': 'percent'}}, 'common_norm'),
        ({'hue': 'income', 'options': {'legend_loc': 'lower left'}}, 'covers the data'),
        (
            {'hue': 'income', 'options': {'legend_loc': 'upper left', 'stat': 'proportion'}},
            'cannot clear the data',
        ),
    ],
)
def test_ambiguous_or_unprintable_orders_are_refused_with_a_reason(countries, fields, reason):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(countries, _spec(**fields), {'categories': GROUPS})
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']


def test_presentation_options_reach_the_drawn_marks(countries):
    options = {'fill': False, 'edgewidth': 0.8, 'color': 'ink', 'shrink': 0.8, 'orient': 'h'}
    result = ast.render(countries, _spec(axes={'y': {'scale': 'log'}}, options=options))
    bar = result.figure.axes[0].patches[0]
    ink = mcolors.to_rgb(ast.Manifest().colors['ink'])
    assert bar.get_facecolor()[3] == 0
    assert bar.get_edgecolor()[:3] == pytest.approx(ink)
    assert bar.get_linewidth() == 0.8
    assert result.figure.axes[0].get_xlabel() == 'Count'
    outline = ast.render(
        countries, _spec(options={'element': 'step', 'fill': False, 'cumulative': True})
    )
    path = outline.figure.axes[0].patches[0].get_path()
    assert path.vertices[-1][1] == len(countries)


@pytest.mark.parametrize('orient', ['v', 'h'])
def test_filled_cumulative_step_outline_preserves_the_terminal_value(countries, orient):
    result = ast.render(
        countries, _spec(options={'element': 'step', 'orient': orient, 'cumulative': True})
    )
    area, outline = result.figure.axes[0].patches
    value_axis = 0 if orient == 'h' else 1
    endpoint = outline.get_path().vertices[-1]
    assert endpoint[1 - value_axis] == _bins(result)['upper'].iloc[-1]
    assert endpoint[value_axis] == len(countries)
    assert area.get_fill()
    assert area.get_path().vertices[-1][value_axis] == 0


def test_pooled_normalisation_names_every_pooled_row_as_an_origin(countries):
    everyone = list(range(len(countries)))
    for extra in ({}, {'stat': 'density', 'kde': True}):
        options = {'stat': 'proportion', 'common_norm': True, **extra}
        pooled = ast.render(countries, _spec(hue='income', options=options), {'categories': GROUPS})
        marks = pooled.table[pooled.table['mark_kind'].isin(['bin', 'density'])]
        assert all(sorted(rows) == everyone for rows in marks['source_rows'])
    alone = ast.render(
        countries, _spec(hue='income', options={'stat': 'proportion'}), {'categories': GROUPS}
    )
    assert all(len(rows) < len(countries) for rows in _bins(alone)['source_rows'])


def test_extreme_integer_bin_count_is_refused_without_overflow():
    from astetik._histogram_bins import bin_edges

    for bins in (10**400, 10**5000):
        with pytest.raises(ValueError, match='cannot be printed'):
            bin_edges(np.array([0.0, 1.0]), {'bins': bins}, False)
