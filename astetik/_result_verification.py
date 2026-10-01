"""Bounded physical, typography and layout checks for publication."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, cast

import numpy as np
from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure

from ._result_geometry import omitted_tick_labels, table_issues, tick_collisions
from ._result_graphics import draw
from ._result_text import FontPolicy, checksum_passed, text_evidence
from ._result_types import VerificationCheck, VerificationReport
from ._types import JsonObject


class _RendererCanvas(Protocol):
    def get_renderer(self) -> RendererBase: ...


def object_mapping(value: object) -> Mapping[str, object]:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else {}


def _number(value: object) -> float | None:
    return cast(float, value) if value is not None else None


def _font_policy(manifest: Mapping[str, object], receipt: JsonObject) -> FontPolicy:
    typography = object_mapping(manifest.get('typography', {}))
    paper = object_mapping(manifest.get('paper', {}))
    minimum = cast(float, paper.get('min_fontsize', typography.get('minimum_pt', 7 if receipt.get('paper', False) else 6)))
    font = object_mapping(receipt.get('font', manifest.get('font_info', typography.get('font_info', typography.get('font', {})))))
    path = manifest.get('fontpath', typography.get('font_path')) or font.get('path')
    family = typography.get('font_family') or font.get('resolved', font.get('family'))
    checksum = font.get('sha256', font.get('checksum'))
    return FontPolicy(minimum, cast(str | None, path),
                      cast(str | None, family), cast(str | None, checksum))


def _dimensions(figure: Figure, manifest: Mapping[str, object], receipt: JsonObject) -> VerificationCheck:
    width, height = figure.get_size_inches() * 25.4
    paper, dimensions = object_mapping(manifest.get('paper', {})), object_mapping(manifest.get('dimensions', {}))
    expected_width = _number(dimensions.get('width_mm', paper.get('width_mm') if receipt.get('paper', False) else None))
    expected_height = _number(dimensions.get('height_mm'))
    aspect = _number(paper.get('aspect'))
    if expected_height is None and expected_width and aspect and len(figure.axes) == 1:
        expected_height = expected_width / aspect
    passed = bool(np.isfinite([width, height]).all() and width > 0 and height > 0)
    if expected_width is not None:
        passed = passed and abs(width - expected_width) <= .01
    if expected_height is not None:
        passed = passed and abs(height - expected_height) <= .01
    return {'check': 'physical_dimensions', 'passed': bool(passed), 'width_mm': float(width), 'height_mm': float(height)}


def verify_figure(figure: Figure, manifest: Mapping[str, object], receipt: JsonObject) -> VerificationReport:
    draw(figure)
    renderer = cast(_RendererCanvas, figure.canvas).get_renderer()
    policy = _font_policy(manifest, receipt)
    omitted = omitted_tick_labels(figure)
    text = text_evidence(figure, renderer, policy, omitted)
    fit, collisions = table_issues(figure, renderer)
    font_checksum = checksum_passed(policy)
    checks: list[VerificationCheck] = [
        _dimensions(figure, manifest, receipt),
        {'check': 'minimum_type_size', 'passed': not text.size, 'minimum_pt': policy.minimum, 'issues': text.size},
        {'check': 'label_clipping', 'passed': not text.clipped, 'issues': text.clipped},
        {'check': 'tick_label_collisions', 'passed': not (ticks := tick_collisions(figure, renderer, omitted)), 'issues': ticks},
        {'check': 'table_cell_text_fit', 'passed': not fit, 'issues': fit},
        {'check': 'table_cell_text_collisions', 'passed': not collisions, 'issues': collisions},
        {'check': 'glyph_coverage', 'passed': not text.glyphs, 'issues': text.glyphs,
         'recovery': 'Explicitly select typography.font or typography.font_path with coverage for every reported character, then render again. No font substitution is performed.'},
        {'check': 'font_resolution', 'passed': all(item['passed'] for item in text.fonts) and font_checksum,
         'checksum_passed': font_checksum, 'fonts': text.fonts},
        {'check': 'finite_axis_bounds', 'passed': all(np.isfinite((*axis.get_xlim(), *axis.get_ylim())).all() for axis in figure.axes)},
    ]
    return {'passed': all(check['passed'] for check in checks), 'checks': checks,
            'limitations': ['Checks validate the rendered artifact and recorded computations; they do not establish scientific truth.',
                            'Labels are measured on the Matplotlib canvas at the declared physical dimensions.']}
