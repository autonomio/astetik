"""Local studio: adjust figure parameters and see Astetik's actual output.

Every change in the page posts the same ``spec`` and ``manifest`` an agent
would pass to ``astetik.render``; the figure shown is that call's result.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pandas as pd
import shapefile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import astetik as ast
from astetik._colors import _CATEGORY_PALETTE
from astetik._histogram_options import LEGEND_LOCATIONS

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path(__file__).with_name('studio.html')
FONT = ROOT / 'astetik' / 'fonts' / 'Finlandica.ttf'
FORMATS = {'pdf': 'application/pdf', 'png': 'image/png', 'svg': 'image/svg+xml'}
KINDS = ('hist', 'line', 'regs', 'bar', 'box', 'violin', 'panels')
_HEX = re.compile(r'#[0-9A-Fa-f]{6}')
_SECTIONS = ('colors', 'categories', 'typography', 'paper', 'axes')
_ROLES = ('primary', 'secondary', 'paper', 'ink', 'muted', 'line', 'negative', 'neutral', 'positive')
_SIZES = ('fontsize', 'labelsize', 'titlesize', 'ticksize', 'legendsize')
_PAPER = ('preset', 'width_mm', 'aspect', 'dpi', 'min_fontsize')
_AXES = ('linewidth', 'grid', 'spines', 'tick_direction', 'tick_length')
_SPINES = ('left', 'bottom', 'right', 'top')
_ACCEPTED = (
    'The studio accepts a spec object, a manifest of colours, sizes, page and axes values or null, '
    'and format svg, pdf, or png. The reason is printed in the terminal running it.'
)


def _latitude(shape: shapefile.Shape) -> float:
    """Latitude of the centroid of an area's largest polygon, in degrees north."""
    points = np.asarray(shape.points, dtype=float)
    best, latitude = 0.0, float('nan')
    for start, stop in zip(shape.parts, [*shape.parts[1:], len(points)]):
        x, y = points[start:stop, 0], points[start:stop, 1]
        cross = x[:-1] * y[1:] - x[1:] * y[:-1]
        area = cross.sum() / 2
        if abs(area) > best:
            best, latitude = abs(area), float(((y[:-1] + y[1:]) * cross).sum() / (6 * area))
    return latitude


def bundled() -> tuple[pd.DataFrame, dict[str, object]]:
    """Country and area attributes from the Natural Earth snapshot Astetik ships."""
    reader = shapefile.Reader(str(ROOT / 'astetik' / 'extras' / 'countries'))
    source = pd.DataFrame([record.as_dict() for record in reader.records()])
    source['latitude'] = [_latitude(shape) for shape in reader.shapes()]
    kept = source[(source['POP_EST'] > 0) & (source['GDP_MD_EST'] > 0)]
    data = pd.DataFrame(
        {
            'iso3': kept['ADM0_A3'],
            'continent': kept['CONTINENT'],
            'income_group': kept['INCOME_GRP'].str.replace(r'^\d\. ', '', regex=True),
            'hemisphere': np.where(kept['latitude'] >= 0, 'Northern', 'Southern'),
            'population': kept['POP_EST'],
            'gdp': kept['GDP_MD_EST'] * 1e6,
            'gdp_per_capita': kept['GDP_MD_EST'] * 1e6 / kept['POP_EST'],
            'latitude': kept['latitude'].round(2),
            'latitude_band': np.minimum(np.floor(kept['latitude'].abs() / 10) * 10 + 5, 65),
            'population_rank': kept['POP_RANK'].astype(int),
        }
    ).reset_index(drop=True)
    return data, {
        'source': 'Natural Earth admin-0 attributes and outlines bundled with Astetik '
        '(astetik/extras/countries)',
        'note': f'{len(source) - len(kept)} of {len(source)} records excluded before plotting: '
        'no positive population or GDP estimate. Latitude is the centroid of each '
        'area\'s largest polygon; the band is the midpoint of its 10-degree distance class from '
        'the equator, with every area at 60 degrees or beyond in the last class (65).',
        'key': ['iso3'],
        'units': {
            'population': 'persons', 'gdp': 'USD', 'gdp_per_capita': 'USD',
            'latitude': 'degrees north', 'latitude_band': 'degrees', 'population_rank': '1',
        },
        'descriptions': {
            'population': 'Population',
            'gdp': 'GDP',
            'gdp_per_capita': 'GDP per capita',
            'latitude': 'Latitude',
            'latitude_band': 'Distance from equator',
            'population_rank': 'Population rank class',
            'continent': 'Continent',
            'income_group': 'Income group',
            'hemisphere': 'Hemisphere',
        },
    }


def user_file(path: Path) -> tuple[pd.DataFrame, dict[str, object]]:
    data = pd.read_csv(path)
    return data, {'source': str(path), 'note': '', 'key': [], 'units': {}, 'descriptions': {}}


def describe(data: pd.DataFrame, about: dict[str, object]) -> dict[str, object]:
    numeric = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c])]
    groups = {
        c: [str(v) for v in pd.unique(data[c])]
        for c in data.columns
        if c not in numeric and c not in about['key'] and data[c].nunique() <= len(_CATEGORY_PALETTE)
    }
    return {
        **about,
        'rows': len(data),
        'numeric': numeric,
        'groups': groups,
        'palette': list(_CATEGORY_PALETTE),
        'legend_locations': list(LEGEND_LOCATIONS),
        'defaults': {kind: ast.catalog()['plots'][kind]['defaults'] for kind in KINDS},
        'manifest': ast.Manifest().to_dict(),
        'version': ast.__version__,
    }


def _colour(value: object) -> str:
    """A #RRGGBB colour, rebuilt from its number."""
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError('Colours are six-digit #RRGGBB values.')
    return f'#{int(value[1:], 16):06X}'


def _number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('Sizes and measures are numbers.')
    return float(value)


def _choice(value: object, allowed: tuple[str, ...]) -> str:
    for candidate in allowed:
        if value == candidate:
            return candidate
    raise ValueError(f'Choose one of: {", ".join(allowed)}.')


def _section(document: dict[str, object], name: str, allowed: tuple[str, ...]) -> dict[str, object]:
    section = document.get(name, {})
    if not isinstance(section, dict) or not set(section) <= set(allowed):
        raise ValueError(f'manifest.{name} accepts: {", ".join(allowed)}.')
    return section


def design(document: object, levels: list[str]) -> dict[str, object] | None:
    """Rebuild the page's manifest from colours, numbers, and known names.

    A manifest may name a font file to open. A web request never may: nothing is passed
    on as received, and a field this page does not set is refused.
    """
    if document is None:
        return None
    if not isinstance(document, dict) or not set(document) <= set(_SECTIONS):
        raise ValueError(f'manifest is null or an object with: {", ".join(_SECTIONS)}.')
    colors = _section(document, 'colors', _ROLES)
    sizes = _section(document, 'typography', _SIZES)
    paper = _section(document, 'paper', _PAPER)
    axes = _section(document, 'axes', _AXES)
    categories = _section(document, 'categories', tuple(levels))
    spines = axes.get('spines', [])
    if not isinstance(spines, list) or not set(spines) <= set(_SPINES):
        raise ValueError(f'manifest.axes.spines lists: {", ".join(_SPINES)}.')
    page: dict[str, object] = {
        name: _number(paper[name]) for name in ('width_mm', 'aspect', 'min_fontsize') if name in paper
    }
    if 'preset' in paper:
        page['preset'] = _choice(paper['preset'], ('single', 'double'))
    if 'dpi' in paper:
        page['dpi'] = int(_number(paper['dpi']))
    frame: dict[str, object] = {
        name: _number(axes[name]) for name in ('linewidth', 'tick_length') if name in axes
    }
    if 'grid' in axes:
        frame['grid'] = axes['grid'] is True
    if 'spines' in axes:
        frame['spines'] = [side for side in _SPINES if side in spines]
    if 'tick_direction' in axes:
        frame['tick_direction'] = _choice(axes['tick_direction'], ('out', 'in', 'inout'))
    return {
        'colors': {role: _colour(colors[role]) for role in _ROLES if role in colors},
        'typography': {name: _number(sizes[name]) for name in _SIZES if name in sizes},
        'categories': {level: _colour(categories[level]) for level in levels if level in categories},
        'paper': page,
        'axes': frame,
    }


def render(data: pd.DataFrame, levels: list[str], body: bytes) -> dict[str, object]:
    """Run the requested call and report the figure, or the refusal, as data."""
    started = time.perf_counter()
    try:
        request = json.loads(body)
        if not isinstance(request, dict) or not isinstance(request.get('spec'), dict):
            raise ValueError('Send an object with a spec object.')
        wanted = _choice(request.get('format', 'svg'), tuple(FORMATS))
        result = ast.render(data, request['spec'], design(request.get('manifest'), levels))
        report = result.verify()
        payload: dict[str, object] = {
            'checks': [{'check': c['check'], 'passed': c['passed']} for c in report['checks']],
            'observations': result.receipt['observations'],
            'bins': len(result.receipt['methods']['plot'].get('histogram', {}).get('bins', [0])) - 1,
            'caption': result.receipt['caption'],
            'size_mm': [round(v * 25.4, 2) for v in result.figure.get_size_inches()],
        }
        if wanted == 'svg':
            payload['svg'] = result.svg_bytes().decode('utf-8')
        else:
            with tempfile.TemporaryDirectory() as scratch:
                bundle = result.write(Path(scratch) / 'bundle')
                payload['file'] = base64.b64encode(
                    (bundle / f'figure.{wanted}').read_bytes()
                ).decode('ascii')
                payload['media_type'] = FORMATS[wanted]
    except ast.AstetikError as error:
        payload = {'error': error.to_dict()}
    except ValueError as error:
        # The reason goes to this terminal; the reply states only what the page may send.
        print(f'Refused request: {error}', file=sys.stderr)
        payload = {'error': {'code': 'STUDIO_REQUEST', 'message': _ACCEPTED, 'details': {}}}
    payload['milliseconds'] = round((time.perf_counter() - started) * 1000)
    return payload


def handler(data: pd.DataFrame, about: dict[str, object]) -> type[BaseHTTPRequestHandler]:
    description = describe(data, about)
    levels = [str(level) for values in description['groups'].values() for level in values]

    class Studio(BaseHTTPRequestHandler):
        def _send(self, status: int, media_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header('Content-Type', media_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def _json(self, status: int, value: object) -> None:
            self._send(status, 'application/json', json.dumps(value).encode('utf-8'))

        def _local(self) -> bool:
            """Answer only requests addressed to this machine, so no other site can reach the data."""
            if self.headers.get('Host', '').rsplit(':', 1)[0] in ('127.0.0.1', 'localhost'):
                return True
            self._json(403, {'error': {'code': 'STUDIO_REQUEST', 'message': 'Local requests only.'}})
            return False

        def do_GET(self) -> None:
            if not self._local():
                return
            if self.path.split('?')[0] in ('/', '/index.html'):
                self._send(200, 'text/html; charset=utf-8', PAGE.read_bytes())
            elif self.path == '/font.ttf':
                self._send(200, 'font/ttf', FONT.read_bytes())
            elif self.path == '/api/meta':
                self._json(200, description)
            else:
                self._json(404, {'error': {'code': 'NOT_FOUND', 'message': self.path}})

        def do_POST(self) -> None:
            if not self._local():
                return
            # A JSON content type cannot be sent across origins without this server's consent.
            typed = self.headers.get('Content-Type', '').split(';')[0].strip() == 'application/json'
            if self.path != '/api/render' or not typed:
                self._json(404, {'error': {'code': 'NOT_FOUND', 'message': self.path}})
                return
            length = int(self.headers.get('Content-Length', '0'))
            self._json(200, render(data, levels, self.rfile.read(length)))

        def log_message(self, format: str, *args: object) -> None:
            print(f'{self.address_string()} {format % args}', file=sys.stderr)

    return Studio


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--data', type=Path, help='Your own CSV; default is the bundled snapshot.')
    arguments = parser.parse_args(argv)
    data, about = user_file(arguments.data) if arguments.data else bundled()
    server = ThreadingHTTPServer(('127.0.0.1', arguments.port), handler(data, about))
    print(f'Astetik studio: http://127.0.0.1:{arguments.port}/', file=sys.stderr)
    server.serve_forever()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
