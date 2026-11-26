"""Imported studio measurements retain paper-mode unit validation."""

import json

from scripts import studio


def test_imported_csv_can_render_in_paper_mode_with_declared_units(country_estimates, tmp_path):
    path = tmp_path / 'measurements.csv'
    country_estimates[['wealth']].to_csv(path, index=False)
    data, about = studio.user_file(path)
    metadata = studio.describe(data, about)
    assert metadata['numeric'] == ['wealth'] and metadata['units'] == {}
    spec = {'kind': 'hist', 'x': 'wealth', 'paper': 'single'}
    missing = studio.render(data, [], json.dumps({'spec': spec}).encode())
    assert missing['error']['code'] == 'UNITS_REQUIRED'
    spec['units'] = {'wealth': 'USD'}
    declared = studio.render(data, [], json.dumps({'spec': spec}).encode())
    assert 'error' not in declared and '<svg' in declared['svg']
    assert all(check['passed'] for check in declared['checks'])
