"""Supported plot options and explicit numerical-policy validation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import cast

import numpy as np

from ._render_context import RendererOptions
from ._types import JsonObject, JsonValue

DEFAULT_OPTIONS: dict[str, JsonObject] = {
    'corr': dict(method='spearman', annot=False, mask=False),
    'hist': dict(bins='auto', density=False, kde=False, alpha=0.85, orient='v'),
    'kde': dict(bw_method='scott', gridsize=128, cut=0.0, cumulative=False, fill=True, alpha=0.3),
    'pie': dict(startangle=90.0, percent=True),
    'swarm': dict(point_size=18.0, alpha=0.85, orient='v', dodge=True, width=0.8),
    'scat': dict(point_size=18.0, alpha=0.85, marker='o', hue_mode='auto'),
    'line': dict(
        linewidth=1.25, alpha=1.0, marker=None, linestyle='solid', sort=True, drawstyle='default'
    ),
    'grid': dict(jitter=0.12, point_size=18.0, alpha=0.85, orient='v', dodge=True),
    'box': dict(whis=1.5, width=0.8, orient='v', alpha=0.75),
    'violin': dict(
        bw_method='scott', gridsize=128, cut=0.0, split=False, width=0.8, alpha=0.75, orient='v'
    ),
    'strip': dict(jitter=0.12, point_size=18.0, alpha=0.85, orient='v', dodge=True),
    'count': dict(orient='v', alpha=0.85),
    'bargrid': dict(estimator='mean', errorbar=None, orient='v', alpha=0.85),
    'overlap': dict(estimator='mean', orient='h', alpha=0.7),
    'multikde': dict(
        bw_method='scott', gridsize=128, cut=0.0, cumulative=False, fill=True, alpha=0.3
    ),
    'compare': dict(point_size=24.0, alpha=0.85),
    'multicount': dict(orient='v', alpha=0.85),
    'bar': dict(estimator='sum', errorbar=None, orient='v', alpha=0.85),
    'bartwo': dict(estimator='mean', errorbar=None, orient='v', alpha=0.85),
    'world': dict(log=False),
    'regs': dict(
        fit_reg=True,
        draw_scatter=True,
        marker='o',
        point_size=18.0,
        alpha=0.8,
        linewidth=1.25,
        hue_mode='auto',
    ),
    'roc': dict(positive_label=1, linewidth=1.5),
    'oned': dict(linewidth=0.8),
    'twod': dict(point_size=18.0, alpha=0.85, marker='o', hue_mode='auto'),
    'comparison': dict(point_size=18.0, alpha=0.5, linewidth=1.25),
}
DEFAULT_OPTIONS['association'] = dict(DEFAULT_OPTIONS['scat'])
DEFAULT_OPTIONS['longitudinal'] = dict(DEFAULT_OPTIONS['line'])
SUPPORTED_OPTIONS = {k: set(v) | {'col_wrap'} for k, v in DEFAULT_OPTIONS.items()}
KINDS = tuple(DEFAULT_OPTIONS)


def finite_positive(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and bool(np.isfinite(value))
        and value > 0
    )


def bandwidth_valid(value: object) -> bool:
    return (isinstance(value, str) and value in ('scott', 'silverman')) or finite_positive(value)


_VALIDATORS: dict[str, tuple[Callable[[object], bool], str]] = {
    'bw_method': (
        bandwidth_valid,
        'bw_method must be scott, silverman, or a finite positive factor.',
    ),
    'alpha': (
        lambda v: not isinstance(v, bool) and isinstance(v, (int, float)) and 0 <= v <= 1,
        'alpha must be between 0 and 1.',
    ),
    'hue_mode': (
        lambda v: v in ('auto', 'categorical', 'continuous'),
        'hue_mode must be auto, categorical, or continuous.',
    ),
    'orient': (lambda v: v in ('v', 'h'), "orient must be 'v' or 'h'."),
    'gridsize': (
        lambda v: isinstance(v, int) and v >= 16,
        'gridsize must be an integer of at least 16.',
    ),
    'cut': (
        lambda v: isinstance(v, (int, float)) and bool(np.isfinite(v)) and v >= 0,
        'cut must be a finite nonnegative number.',
    ),
    'estimator': (
        lambda v: v in ('mean', 'median', 'sum'),
        "estimator must be 'mean', 'median', or 'sum'.",
    ),
    'errorbar': (lambda v: v in (None, 'sd', 'se'), "errorbar must be None, 'sd', or 'se'."),
    'jitter': (
        lambda v: isinstance(v, (int, float)) and 0 <= v <= 0.4,
        'jitter must be a number between 0 and 0.4.',
    ),
    'col_wrap': (
        lambda v: v is None or (isinstance(v, int) and v >= 1),
        'col_wrap must be a positive integer.',
    ),
}
_BOOLEAN_OPTIONS = (
    'annot',
    'mask',
    'density',
    'kde',
    'cumulative',
    'fill',
    'split',
    'dodge',
    'sort',
    'percent',
    'log',
    'fit_reg',
    'draw_scatter',
)
_POSITIVE_OPTIONS = ('point_size', 'width', 'linewidth', 'whis')


def validate_options(kind: str, options: Mapping[str, JsonValue]) -> RendererOptions:
    unknown = set(options) - SUPPORTED_OPTIONS[kind]
    if unknown:
        raise ValueError(f'Unsupported {kind} options: {sorted(unknown)}.')
    resolved = dict(DEFAULT_OPTIONS[kind])
    resolved.update(options)
    for key in _BOOLEAN_OPTIONS:
        if key in resolved and not isinstance(resolved[key], bool):
            raise ValueError(f'{key} must be a boolean.')
    for key, (predicate, message) in _VALIDATORS.items():
        if key in resolved and not predicate(resolved[key]):
            raise ValueError(message)
    for key in _POSITIVE_OPTIONS:
        if key in resolved and not finite_positive(resolved[key]):
            raise ValueError(f'{key} must be a finite positive number.')
    if kind == 'regs' and not resolved['fit_reg'] and not resolved['draw_scatter']:
        raise ValueError('regs must display observations, regression, or both.')
    return cast(RendererOptions, resolved)
