"""Measurement identity must preserve explicit semantic color bindings."""

from typing import Literal

import matplotlib.colors as mcolors
import pandas as pd
import pytest

from astetik._manifest import Manifest
from astetik._renderers import render_plot
from astetik._spec_types import PlotSpec


@pytest.mark.parametrize('kind', ['hist', 'line', 'longitudinal'])
def test_single_measurement_respects_explicit_category_binding(
    kind: Literal['hist', 'line', 'longitudinal'],
) -> None:
    frame = pd.DataFrame({'x': [1.0, 2.0, 3.0], 'y': [1.25, 1.5, 1.75]})
    measurement = 'x' if kind == 'hist' else 'y'
    manifest = Manifest(categories={measurement: 'secondary'})
    spec: PlotSpec = {
        'schema_version': '1.0',
        'kind': kind,
        'x': 'x',
        'options': {},
        'paper': True,
        'missing': 'error',
        'legend': True,
        'key': [],
        'title': '',
        'subtitle': '',
    }
    if kind != 'hist':
        spec['y'] = 'y'
    result = render_plot(frame, spec, manifest, True)
    axis = result.figure.axes[0]
    actual = (
        axis.patches[0].get_facecolor()
        if kind == 'hist'
        else mcolors.to_rgba(axis.lines[0].get_color())
    )
    assert actual[:3] == mcolors.to_rgb(manifest.colors['secondary'])
