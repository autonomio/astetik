"Publish descriptive counts from the shipped geographic metadata snapshot."

from __future__ import annotations

import argparse
import json
from importlib.resources import as_file, files
from pathlib import Path

import astetik as ast

REGION_COLORS = {
    'Africa': 'primary',
    'Americas': 'secondary',
    'Asia': '#2D7D60',
    'Europe': '#7D5595',
    'Oceania': '#A54532',
}


def first_figure() -> ast.EvidenceResult:
    """Count countries and areas by the region labels in the bundled snapshot."""
    manifest = ast.Manifest(categories=REGION_COLORS)
    spec = {
        'kind': 'count',
        'x': 'region',
        'key': ['alpha-3'],
        'paper': 'single',
        'title': 'Countries and areas by region',
        'labels': {'x': 'Region', 'y': 'Countries and areas'},
        'order': list(REGION_COLORS),
        'missing': 'drop',
        'missing_reason': 'The bundled Antarctica record has no region label.',
    }
    resource = files('astetik').joinpath('extras', 'countries.csv')
    with as_file(resource) as source:
        return ast.render(source, spec, manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Publish a descriptive plot from actual bundled metadata.'
    )
    parser.add_argument(
        'directory', type=Path, help='New evidence bundle directory; existing paths are refused.'
    )
    arguments = parser.parse_args(argv)
    result = first_figure()
    directory = result.write(arguments.directory)
    print(
        json.dumps(
            {
                'bundle': str(directory),
                'result_id': result.result_id,
                'observations': result.receipt['observations'],
            },
            indent=2,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
