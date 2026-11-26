"""Grid figures, shared legends, and page contracts on the bundled country estimates."""

from __future__ import annotations

import matplotlib.colors as mcolors
import pytest

import astetik as ast

TIERS = {'High income': '#2A4A70', 'Other': '#AC4B35'}
INCOME = {
    'High income: OECD': '#9A7016',
    'High income: nonOECD': '#2A4A70',
    'Upper middle income': '#2D7D60',
    'Lower middle income': '#7D5595',
    'Low income': '#AC4B35',
}
UNITS = {'wealth': 'USD', 'output': 'USD', 'population': 'persons', 'size_class': '1'}
LOG = {'x': {'scale': 'log'}, 'y': {'scale': 'log'}}
PANELS = [
    {'kind': 'hist', 'x': 'wealth', 'axes': {'x': {'scale': 'log'}}, 'title': 'Distribution'},
    {'kind': 'regs', 'x': 'population', 'y': 'output', 'axes': LOG},
    {'kind': 'bar', 'x': 'tier', 'y': 'wealth', 'options': {'estimator': 'mean', 'errorbar': 'ci'}},
    {'kind': 'box', 'x': 'tier', 'y': 'wealth', 'axes': {'y': {'scale': 'log'}}},
    {'kind': 'line', 'x': 'size_class', 'y': 'wealth', 'hue': 'tier',
     'options': {'estimator': 'median'}},
    {'kind': 'violin', 'x': 'tier', 'y': 'wealth', 'axes': {'y': {'scale': 'log'}}},
]


def _spec(**fields: object) -> dict[str, object]:
    return {'key': ['iso3'], 'paper': 'double', 'units': UNITS, **fields}


def _plots(result: ast.EvidenceResult) -> list:
    return [axis for axis in result.figure.axes if axis.get_visible()]


def test_panels_mix_the_five_types_in_one_lettered_figure(country_estimates):
    spec = _spec(kind='panels', panels=PANELS, options={'ncols': 3})
    result = ast.render(country_estimates, spec, {'categories': TIERS})
    plots = _plots(result)
    assert [axis.get_title(loc='left') for axis in plots] == [
        'a  Distribution', 'b', 'c', 'd', 'e', 'f'
    ]
    methods = result.receipt['methods']['plot']
    assert [panel['kind'] for panel in methods['panels']] == [p['kind'] for p in PANELS]
    assert (methods['rows'], methods['columns']) == (2, 3)
    assert 'histogram' in methods['panels'][0] and 'regression' in methods['panels'][1]
    assert set(result.table['facet'].map(lambda facet: facet['panel'])) == set('abcdef')
    aspect = result.manifest['paper']['aspect']
    for axis in plots:
        frame = axis.get_window_extent()
        assert frame.width / frame.height == pytest.approx(aspect, rel=0.01)
    assert plots[0].get_ylabel() == 'Count' and plots[1].get_xlabel() == 'population (persons)'
    assert result.verify()['passed']


def test_one_type_repeats_over_any_number_of_panels(country_estimates):
    columns = ['wealth', 'output', 'population']
    panels = [{'kind': 'hist', 'x': column, 'axes': {'x': {'scale': 'log'}}} for column in columns]
    result = ast.render(
        country_estimates, _spec(kind='panels', panels=panels, options={'ncols': 3, 'labels': 'A'})
    )
    plots = _plots(result)
    assert [axis.get_title(loc='left') for axis in plots] == ['A', 'B', 'C']
    assert [axis.get_xlabel() for axis in plots] == [
        'wealth (USD)', 'output (USD)', 'population (persons)'
    ]
    bins = result.table[result.table['mark_kind'] == 'bin']
    assert bins.groupby(bins['facet'].map(lambda f: f['panel']))['value'].sum().tolist() == [
        len(country_estimates)
    ] * 3


@pytest.mark.parametrize(
    'spec,code,reason',
    [
        ({'kind': 'panels'}, 'SPEC_SCHEMA', 'at least one panel'),
        ({'kind': 'panels', 'panels': [{'kind': 'pie', 'x': 'tier'}]}, 'PLOT_KIND', 'panel kind'),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth', 'col': 'tier'}]},
         'SPEC_SCHEMA', 'A panel accepts'),
        ({'kind': 'panels', 'x': 'wealth', 'panels': [{'kind': 'hist', 'x': 'wealth'}]},
         'SPEC_SCHEMA', 'Unsupported top-level fields for a panels figure.'),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth', 'options': {'trim': 1}}]},
         'PLOT_OPTIONS', 'never ignored'),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth', 'title': 3}]},
         'SPEC_SCHEMA', 'title text'),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth', 'labels': {'z': 'a'}}]},
         'SPEC_SCHEMA', 'x and y text'),
        ({'kind': 'hist', 'x': 'wealth', 'panels': []}, 'SPEC_SCHEMA', "kind 'panels'"),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth'}], 'options': {'ncols': 0}},
         'PLOT_CONTRACT', 'ncols must be'),
        ({'kind': 'panels', 'panels': [{'kind': 'hist', 'x': 'wealth'}], 'options': {'labels': 'i'}},
         'PLOT_CONTRACT', 'labels must be one of'),
    ],
)
def test_malformed_panel_figures_are_refused_with_a_reason(country_estimates, spec, code, reason):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(country_estimates, _spec(**spec))
    assert caught.value.code == code
    report = caught.value.to_dict()
    assert reason in (report['details'].get('reason') or report['message'])


@pytest.mark.parametrize(
    'field,value',
    [('row', 'tier'), ('col', 'tier'), ('columns', ['wealth']), ('analysis', {})],
)
def test_unsupported_top_level_panel_fields_have_actionable_refusals(country_estimates, field, value):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(country_estimates, _spec(kind='panels', panels=[PANELS[0]], **{field: value}))
    assert caught.value.code == 'SPEC_SCHEMA'
    assert str(caught.value) == 'Unsupported top-level fields for a panels figure.'
    assert caught.value.details['fields'] == [field]


def test_a_failing_panel_is_named_in_the_refusal(country_estimates):
    panels = [PANELS[0], {'kind': 'bar', 'x': 'iso3', 'y': 'wealth',
                          'options': {'estimator': 'mean', 'errorbar': 'sd'}}]
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(country_estimates, _spec(kind='panels', panels=panels))
    assert caught.value.details['reason'].startswith('Panel 2 (bar): SD/SE error bars')


def test_facets_state_each_axis_once_and_key_every_group(country_estimates):
    spec = _spec(kind='hist', x='wealth', hue='tier', col='income', axes={'x': {'scale': 'log'}},
                 options={'col_wrap': 3})
    result = ast.render(country_estimates, spec, {'categories': TIERS})
    plots = _plots(result)
    assert sorted(axis.get_title(loc='left') for axis in plots) == sorted(INCOME)
    labelled = [axis.get_xlabel() for axis in plots]
    assert labelled.count('wealth (USD)') == 3 and labelled.count('') == 2
    assert [axis.get_ylabel() for axis in plots] == ['Count', '', '', 'Count', '']
    legends = [axis.get_legend() for axis in plots if axis.get_legend() is not None]
    assert len(legends) == 1
    assert [text.get_text() for text in legends[0].get_texts()] == list(
        dict.fromkeys(country_estimates['tier'])
    )
    aspect = result.manifest['paper']['aspect']
    frames = [axis.get_window_extent() for axis in plots]
    assert all(frame.width / frame.height == pytest.approx(aspect, rel=0.01) for frame in frames)
    assert result.verify()['passed']


def test_a_legend_above_the_plot_lengthens_the_figure_by_its_band(country_estimates):
    spec = {'kind': 'scat', 'x': 'population', 'y': 'output', 'hue': 'income', 'axes': LOG,
            'key': ['iso3'], 'paper': 'single', 'units': UNITS}
    keyed = ast.render(country_estimates, spec, {'categories': INCOME})
    plain = ast.render(country_estimates, {**spec, 'legend': False}, {'categories': INCOME})
    band = keyed.receipt['methods']['plot']['legend_band_mm']
    assert band > 0 and 'legend_band_mm' not in plain.receipt['methods']['plot']
    assert keyed.figure.get_figheight() * 25.4 == pytest.approx(
        plain.figure.get_figheight() * 25.4 + band, abs=0.001
    )
    frames = [result.figure.axes[0].get_window_extent() for result in (keyed, plain)]
    assert frames[0].height == pytest.approx(frames[1].height, rel=0.02)
    check = keyed.verify()['checks'][0]
    assert check['check'] == 'physical_dimensions' and check['passed']


def test_paper_figures_sit_on_a_white_page_unless_the_manifest_declares_one(country_estimates):
    spec = {'kind': 'hist', 'x': 'wealth', 'key': ['iso3'], 'units': UNITS}

    def page(paper: object, manifest: object = None) -> str:
        figure = ast.render(country_estimates, {**spec, 'paper': paper}, manifest).figure
        return mcolors.to_hex(figure.get_facecolor()).upper()

    cream = ast.Manifest().colors['paper']
    assert page('single') == '#FFFFFF'
    assert page(True, ast.Manifest().with_primary('#235B60')) == '#FFFFFF'
    assert page(False) == cream
    assert page('single', {'colors': {'paper': cream}}) == cream
    assert page('double', ast.Manifest(colors={'paper': '#FAFAFA'})) == '#FAFAFA'
    replayed = ast.render(country_estimates, {**spec, 'paper': 'single'})
    assert replayed.manifest['colors']['paper'] == '#FFFFFF'


FITS = {'kind': 'regs', 'x': 'population', 'y': 'output', 'hue': 'income', 'axes': LOG,
        'options': {'fit_groups': True, 'annotate_fit': True}}


@pytest.mark.parametrize(
    'spec,reason',
    [
        ({'kind': 'panels', 'panels': [FITS] * 4, 'options': {'ncols': 4}}, 'no room left for its plot'),
        ({**FITS, 'paper': 'single', 'options': {**FITS['options'], 'legend_loc': 'outside right'}},
         'of the figure width'),
        ({**FITS, 'paper': 'single', 'options': {**FITS['options'], 'legend_loc': 'upper left'}},
         'covers the data'),
    ],
)
def test_a_figure_whose_plot_has_no_room_is_refused_without_a_stray_warning(
    country_estimates, recwarn, spec, reason
):
    with pytest.raises(ast.AstetikError) as caught:
        ast.render(country_estimates, _spec(**spec), {'categories': INCOME})
    assert caught.value.code == 'PLOT_CONTRACT'
    assert reason in caught.value.details['reason']
    assert not [warning for warning in recwarn.list if 'constrained_layout' in str(warning.message)]


def test_a_legend_too_large_for_the_plot_is_set_above_it_and_never_squeezes_it(country_estimates):
    keyed = ast.render(country_estimates, _spec(**FITS, paper='single'), {'categories': INCOME})
    plain = ast.render(
        country_estimates, _spec(**FITS, paper='single', legend=False), {'categories': INCOME}
    )
    legend = keyed.figure.axes[0].get_legend()
    frames = [result.figure.axes[0].get_window_extent() for result in (keyed, plain)]
    assert legend.get_window_extent().y0 >= frames[0].y1
    assert (frames[0].width, frames[0].height) == pytest.approx(
        (frames[1].width, frames[1].height), rel=0.02
    )
    assert keyed.verify()['passed']


def test_the_finished_layout_is_held_so_a_later_draw_moves_nothing(country_estimates):
    result = ast.render(
        country_estimates,
        _spec(kind='bar', x='income', y='wealth', hue='tier', col='tier',
              options={'estimator': 'median', 'annotate_n': True, 'legend_loc': 'outside top'}),
        {'categories': TIERS},
    )
    before = [axis.get_position().bounds for axis in result.figure.axes]
    result.figure.canvas.draw()
    assert [axis.get_position().bounds for axis in result.figure.axes] == before
    assert result.figure.get_layout_engine() is None


def test_an_empty_facet_cell_does_not_take_the_axis_labels_of_the_plot_above(country_estimates):
    spec = {'kind': 'hist', 'x': 'wealth', 'row': 'income', 'col': 'tier', 'key': ['iso3'],
            'units': UNITS, 'axes': {'x': {'scale': 'log'}}}
    result = ast.render(country_estimates, spec)
    drawn = {axis.get_title(loc='left'): axis for axis in result.figure.axes if axis.axison}
    assert len(drawn) == 5 and len(result.figure.axes) == 10
    lowest = drawn['Lower middle income \N{MIDDLE DOT} Other']
    assert lowest.get_xlabel() == 'wealth (USD)'
    assert any(tick.get_visible() and tick.get_text() for tick in lowest.get_xticklabels())
    assert drawn['Low income \N{MIDDLE DOT} Other'].get_xlabel() == ''
    alone_in_row = drawn['Low income \N{MIDDLE DOT} Other']
    assert alone_in_row.get_ylabel() == 'Count'
    assert any(tick.get_visible() and tick.get_text() for tick in alone_in_row.get_yticklabels())


def test_end_labels_name_the_lines_of_every_facet(country_estimates):
    spec = {'kind': 'line', 'x': 'size_class', 'y': 'wealth', 'hue': 'income', 'col': 'tier',
            'key': ['iso3'], 'units': UNITS, 'options': {'estimator': 'median', 'legend_loc': 'end'}}
    result = ast.render(country_estimates, spec, {'categories': INCOME})
    named = [{text.get_text() for text in axis.texts} & set(INCOME) for axis in result.figure.axes]
    assert named == [
        {'High income: nonOECD', 'High income: OECD'},
        {'Low income', 'Upper middle income', 'Lower middle income'},
    ]


def test_category_names_survive_rows_of_shared_facets(country_estimates):
    spec = {'kind': 'bar', 'x': 'income', 'y': 'wealth', 'col': 'tier', 'key': ['iso3'],
            'paper': 'single', 'units': UNITS, 'options': {'estimator': 'median'}}
    result = ast.render(country_estimates, spec)
    upper, lower = result.figure.axes
    assert upper.get_subplotspec().rowspan.start < lower.get_subplotspec().rowspan.start
    names = [' '.join(tick.get_text().split()) for tick in lower.get_xticklabels()]
    assert names == list(dict.fromkeys(country_estimates['income']))
    assert any(chr(10) in tick.get_text() for tick in lower.get_xticklabels())
    assert not upper.get_xticklabels()
    assert result.verify()['passed']


def test_a_panel_inherits_the_figure_legend_unless_it_declares_its_own(country_estimates):
    grouped = {'kind': 'box', 'x': 'tier', 'y': 'wealth', 'hue': 'tier',
               'axes': {'y': {'scale': 'log'}}}
    spec = _spec(kind='panels', legend=False, panels=[grouped, {**grouped, 'legend': True}])
    result = ast.render(country_estimates, spec, {'categories': TIERS})
    first, second = _plots(result)
    assert first.get_legend() is None and second.get_legend() is not None
