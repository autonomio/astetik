"""Scientific values, axis semantics and deterministic rendering contracts."""

import copy
import warnings

import matplotlib
import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

from astetik._manifest import Manifest
from astetik._renderers import KINDS, render_plot


@pytest.fixture
def manifest():
    return Manifest(categories={'A': '#2A4A70', 'B': '#AC4B35', 'x': '#2D7D60', 'y': '#7D5595'})


@pytest.fixture
def observations():
    return pd.DataFrame(
        {
            'x': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            'y': [1.2, 2.8, 2.2, 4.1, 5.3, 5.9],
            'group': ['A'] * 3 + ['B'] * 3,
            'truth': [0, 1, 0, 1, 0, 1],
            'score': [0.1, 0.9, 0.4, 0.7, 0.2, 0.6],
        }
    )


CASES = {
    'corr': {'columns': ['x', 'y']},
    'hist': {'x': 'x'},
    'kde': {'x': 'x'},
    'pie': {'x': 'group'},
    'scat': {'x': 'x', 'y': 'y'},
    'line': {'x': 'x', 'y': 'y'},
    'roc': {'x': 'truth', 'y': 'score'},
    'oned': {'x': 'x'},
    'regs': {'x': 'x', 'y': 'y'},
    'twod': {'x': 'x', 'y': 'y'},
    'multikde': {'x': 'x', 'hue': 'group'},
    'compare': {'x': 'x', 'y': 'y', 'hue': 'group'},
    'overlap': {'x': 'x', 'y': 'y', 'hue': 'group'},
    'comparison': {'x': 'group', 'y': 'y'},
    'association': {'x': 'x', 'y': 'y'},
    'longitudinal': {'x': 'x', 'y': 'y'},
}
for _kind in (
    'swarm',
    'grid',
    'box',
    'violin',
    'strip',
    'count',
    'bargrid',
    'multicount',
    'bar',
    'bartwo',
):
    CASES[_kind] = {'x': 'group', 'y': None if _kind in ('count', 'multicount') else 'y'}


@pytest.mark.parametrize('kind', list(CASES))
def test_each_catalogue_renderer_obeys_paper_and_source_row_contract(kind, observations, manifest):
    before = observations.copy(deep=True)
    analysis = {
        'summary': [
            {'group': 'A', 'n': 3, 'estimate': 2.0, 'lower': 1.0, 'upper': 3.0},
            {'group': 'B', 'n': 3, 'estimate': 5.0, 'lower': 4.0, 'upper': 6.0},
        ]
    }
    result = render_plot(observations, {'kind': kind, **CASES[kind]}, manifest, True, analysis)
    result.figure.canvas.draw()
    assert result.figure.dpi == manifest.paper['dpi']
    assert result.figure.get_size_inches()[0] * 25.4 == pytest.approx(manifest.paper['width_mm'])
    assert result.marks
    assert set(range(len(observations))) == {p for m in result.marks for p in m['source_rows']}
    assert len(result.table) == len(result.marks)
    assert all(m['computation'] for m in result.marks)
    assert len({m['id'] for m in result.marks}) == len(result.marks)
    assert all(
        text.get_fontproperties().get_file() == manifest.font_path
        for text in result.figure.findobj(match=matplotlib.text.Text)
    )
    pd.testing.assert_frame_equal(observations, before)


def test_world_preserves_fractional_values_and_refuses_unknown_geometry(manifest):
    frame = pd.DataFrame({'country': ['FIN', 'USA'], 'value': [1.25, 8.875]})
    rendered = render_plot(frame, {'kind': 'world', 'x': 'country', 'y': 'value'}, manifest, True)
    rendered.figure.canvas.draw()
    assert {m['values']['country']: m['values']['value'] for m in rendered.marks} == {
        'FIN': 1.25,
        'USA': 8.875,
    }
    assert rendered.methods['world']['projection'].startswith('Plate Carree')
    with pytest.raises(ValueError, match='absent'):
        render_plot(
            frame.assign(country=['FIN', 'ZZZ']),
            {'kind': 'world', 'x': 'country', 'y': 'value'},
            manifest,
            True,
        )


def test_histogram_all_counts_and_density_units_have_exact_bin_provenance(manifest):
    frame = pd.DataFrame({'x': [0.0, 1.0, 2.0, 2.0, 3.0, 4.0]}, index=[5, 5, 2, 9, 9, 9])
    spec = {'kind': 'hist', 'x': 'x', 'options': {'bins': [0, 2, 4]}}
    result = render_plot(frame, spec, manifest, True)
    assert [m['values']['n'] for m in result.marks] == [2, 4]
    assert [m['source_rows'] for m in result.marks] == [[0, 1], [2, 3, 4, 5]]
    density = render_plot(
        frame, {**spec, 'options': {'bins': [0, 2, 4], 'density': True}}, manifest, True
    )
    assert sum(
        m['values']['value'] * (m['values']['upper'] - m['values']['lower']) for m in density.marks
    ) == pytest.approx(1)
    with pytest.raises(ValueError, match='cover every'):
        render_plot(frame, {**spec, 'options': {'bins': [1, 3]}}, manifest, True)


def test_correlation_retains_negative_effects_and_fixed_symmetric_colour_domain(manifest):
    frame = pd.DataFrame(
        {'x': [1.0, 2.0, 3.0, 4.0], 'y': [4.0, 3.0, 2.0, 1.0], 'sample_id': [1, 2, 3, 4]}
    )
    result = render_plot(
        frame,
        {'kind': 'corr', 'columns': ['x', 'y'], 'options': {'method': 'pearson', 'annot': True}},
        manifest,
        True,
    )
    assert result.figure.axes[0].images[0].get_clim() == (-1.0, 1.0)
    negative = [m for m in result.marks if m['values']['x'] != m['values']['y']]
    assert all(m['values']['correlation'] == pytest.approx(-1.0) for m in negative)
    assert all(m['source_rows'] == [0, 1, 2, 3] for m in negative)
    with pytest.raises(ValueError, match='constant'):
        render_plot(frame.assign(y=1.0), {'kind': 'corr', 'columns': ['x', 'y']}, manifest, True)


def test_roc_truth_score_order_ties_and_auc_are_correct(manifest):
    # At the tied .8 threshold, both truth classes enter together.
    frame = pd.DataFrame({'truth': [0, 1, 1, 0], 'score': [0.2, 0.8, 0.8, 0.8]})
    result = render_plot(frame, {'kind': 'roc', 'x': 'truth', 'y': 'score'}, manifest, True)
    assert result.methods['roc']['auc'] == pytest.approx(0.75)
    assert [(m['values']['fpr'], m['values']['tpr']) for m in result.marks] == [
        (0.0, 0.0),
        (0.5, 1.0),
        (1.0, 1.0),
    ]
    assert result.marks[0]['values']['threshold'] is None
    assert result.marks[1]['values']['threshold'] == 0.8
    assert result.figure.axes[0].get_xlim() == (0.0, 1.0)
    assert result.figure.axes[0].get_ylim() == (0.0, 1.0)


@pytest.mark.parametrize('kind', ['count', 'bar', 'bartwo', 'bargrid', 'multicount'])
def test_positive_bar_numeric_axis_has_exact_zero_baseline(kind, observations, manifest):
    spec = {'kind': kind, 'x': 'group', 'y': None if 'count' in kind else 'y'}
    result = render_plot(observations, spec, manifest, True)
    assert result.figure.axes[0].get_ylim()[0] == 0.0
    horizontal = render_plot(observations, {**spec, 'options': {'orient': 'h'}}, manifest, True)
    assert horizontal.figure.axes[0].get_xlim()[0] == 0.0


def test_aggregates_declare_estimator_and_exact_contributing_rows(observations, manifest):
    result = render_plot(
        observations,
        {
            'kind': 'bargrid',
            'x': 'group',
            'y': 'y',
            'options': {'estimator': 'mean', 'errorbar': 'se'},
        },
        manifest,
        True,
    )
    first = result.marks[0]
    assert first['source_rows'] == [0, 1, 2]
    assert first['values']['estimate'] == pytest.approx(observations.y.iloc[:3].mean())
    assert first['values']['error'] == pytest.approx(
        observations.y.iloc[:3].std(ddof=1) / np.sqrt(3)
    )
    assert 'ddof=1' in first['computation']


def test_kde_is_explicit_and_refuses_singular_data(observations, manifest):
    result = render_plot(
        observations,
        {'kind': 'kde', 'x': 'x', 'options': {'bw_method': 0.4, 'gridsize': 32}},
        manifest,
        True,
    )
    assert len(result.marks) == 32
    assert all(m['source_rows'] == list(range(6)) for m in result.marks)
    assert result.methods['kde']['bandwidth_method'] == 0.4
    with pytest.raises(ValueError, match='distinct'):
        render_plot(observations.assign(x=2.0), {'kind': 'kde', 'x': 'x'}, manifest, True)


def test_scatter_continuous_hue_shares_global_domain_across_facets(observations, manifest):
    result = render_plot(
        observations,
        {'kind': 'scat', 'x': 'x', 'y': 'y', 'hue': 'score', 'col': 'group'},
        manifest,
        True,
    )
    point_axes = [
        ax for ax in result.figure.axes if ax.get_label() != '<colorbar>' and ax.collections
    ]
    assert len(point_axes) == 2
    assert all(ax.collections[0].get_clim() == (0.1, 0.9) for ax in point_axes)
    assert result.marks[0]['values']['score'] == 0.1


def test_multi_measure_lines_preserve_raw_values_and_stable_time_order(observations, manifest):
    reversed_frame = observations.iloc[::-1]
    result = render_plot(
        reversed_frame,
        {'kind': 'line', 'x': 'x', 'y': ['y', 'score']},
        Manifest(categories={'y': '#2A4A70', 'score': '#AC4B35'}),
        True,
    )
    assert len(result.marks) == 12
    assert result.marks[0]['source_rows'] == [5]
    assert list(result.figure.axes[0].lines[0].get_xdata()) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_rendering_is_rng_warning_rc_and_pyplot_figure_isolated(observations, manifest):
    # Matplotlib's lazy backend normalization is settled before taking the snapshot.
    matplotlib.get_backend()
    before_rc = dict(matplotlib.rcParams)
    before_rng = np.random.get_state()
    before_filters = copy.deepcopy(warnings.filters)
    before_figures = plt.get_fignums()
    spec = {'kind': 'strip', 'x': 'group', 'y': 'y', 'hue': 'group'}
    first = render_plot(observations, spec, manifest, True)
    second = render_plot(observations, spec, manifest, True)
    first.figure.canvas.draw()
    second.figure.canvas.draw()
    assert first.marks == second.marks
    assert np.array_equal(
        np.asarray(first.figure.canvas.buffer_rgba()),
        np.asarray(second.figure.canvas.buffer_rgba()),
    )
    assert dict(matplotlib.rcParams) == before_rc
    after_rng = np.random.get_state()
    assert before_rng[0] == after_rng[0]
    assert np.array_equal(before_rng[1], after_rng[1])
    assert before_rng[2:] == after_rng[2:]
    assert warnings.filters == before_filters
    assert plt.get_fignums() == before_figures


def test_swarm_keeps_all_numeric_values_and_rejects_unrepresentable_density(manifest):
    frame = pd.DataFrame({'group': ['A'] * 8, 'y': np.arange(8, dtype=float)})
    result = render_plot(frame, {'kind': 'swarm', 'x': 'group', 'y': 'y'}, manifest, True)
    assert sorted(m['values']['value'] for m in result.marks) == list(frame.y)
    assert all(m['source_rows'] == [i] for i, m in enumerate(result.marks))
    crowded = pd.DataFrame({'group': ['A'] * 100, 'y': np.zeros(100)})
    with pytest.raises(ValueError, match='cannot display all'):
        render_plot(crowded, {'kind': 'swarm', 'x': 'group', 'y': 'y'}, manifest, True)


def test_comparison_displays_observations_and_declared_intervals(observations, manifest):
    analysis = {
        'summary': [
            {'group': 'A', 'n': 3, 'estimate': 2.0, 'lower': 0.1, 'upper': 3.5},
            {'group': 'B', 'n': 3, 'estimate': 5.0, 'lower': 4.2, 'upper': 6.3},
        ],
        'methods': {'method': 'welch'},
    }
    result = render_plot(
        observations, {'kind': 'comparison', 'x': 'group', 'y': 'y'}, manifest, True, analysis
    )
    estimates = [m for m in result.marks if m['kind'] == 'estimate']
    assert [m['values']['lower'] for m in estimates] == [0.1, 4.2]
    assert [m['source_rows'] for m in estimates] == [[0, 1, 2], [3, 4, 5]]
    assert len([m for m in result.marks if m['kind'] == 'observation']) == 6


def test_catalogue_coverage_and_unknown_options_fail(observations, manifest):
    assert set(KINDS) == set(CASES) | {'world'}
    with pytest.raises(ValueError, match='Unsupported'):
        render_plot(
            observations,
            {'kind': 'scat', 'x': 'x', 'y': 'y', 'options': {'mispelled': True}},
            manifest,
            True,
        )


def test_two_dimensional_kde_facets_share_grid_and_density_colour_domain(observations, manifest):
    result = render_plot(
        observations,
        {'kind': 'kde', 'x': 'x', 'y': 'y', 'col': 'group', 'options': {'gridsize': 16}},
        manifest,
        True,
    )
    result.figure.canvas.draw()
    point_axes = [ax for ax in result.figure.axes if ax.get_label() != '<colorbar>']
    assert len(point_axes) == 2
    assert point_axes[0].collections[0].get_clim() == point_axes[1].collections[0].get_clim()
    assert len(result.marks) == 512
    assert result.methods['kde']['shared_colour_domain'][0] == 0.0
    fits = result.methods['kde_fits']
    assert [fit['source_rows'] for fit in fits] == [[0, 1, 2], [3, 4, 5]]
    assert result.marks[0]['values']['x'] == result.marks[256]['values']['x']
    assert result.marks[0]['values']['y'] == result.marks[256]['values']['y']


@pytest.mark.parametrize(
    'kind, ignored',
    [('roc', {'hue': 'group'}), ('hist', {'y': 'y'}), ('scat', {'columns': ['x', 'y']})],
)
def test_ignored_fields_are_rejected_instead_of_implying_a_scientific_operation(
    kind, ignored, observations, manifest
):
    spec = {'kind': kind, **CASES[kind], **ignored}
    with pytest.raises(ValueError, match='unsupported'):
        render_plot(observations, spec, manifest, True)
