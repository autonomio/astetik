"""Legacy spelling translations retain explicit scientific preparation policies."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ._spec import fail


def mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        fail('SPEC_SCHEMA', f'{field} must be an object.')
    return dict(cast(Mapping[str, object], value))


def labels(kwargs: dict[str, object]) -> None:
    result = mapping(kwargs.pop('labels', {}), 'labels')
    for old, new in (('x_label', 'x'), ('y_label', 'y')):
        if old in kwargs:
            result[new] = kwargs.pop(old)
    if result:
        kwargs['labels'] = result


def axes(kwargs: dict[str, object]) -> None:
    result = mapping(kwargs.pop('axes', {}), 'axes')
    for dimension in ('x', 'y'):
        scale = kwargs.pop(f'{dimension}_scale', None)
        limits = kwargs.pop(f'{dimension}_limit', None)
        if scale is not None or limits is not None:
            policy = mapping(result.get(dimension, {}), 'axis policy')
            if scale is not None:
                policy['scale'] = scale
            if limits is not None:
                policy['limits'] = limits
            result[dimension] = policy
    if result:
        kwargs['axes'] = result


def translate(kwargs: dict[str, object]) -> None:
    for old, new in (('label_col', 'hue'), ('sub_title', 'subtitle'), ('corr_method', 'method')):
        if old in kwargs:
            kwargs[new] = kwargs.pop(old)
    labels(kwargs)
    if kwargs.pop('outliers', False):
        fail(
            'PREPARATION_REQUIRED',
            'Declare exclusions in preparation; plotting never removes outliers.',
        )
    if kwargs.pop('smooth', None) is not None or kwargs.pop('transform_func', False):
        fail('PREPARATION_REQUIRED', 'Declare transformations in preparation before plotting.')
    if 'dropna' in kwargs:
        kwargs['missing'] = 'drop' if kwargs.pop('dropna') else 'error'
    axes(kwargs)
