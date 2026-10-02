"""Legacy animation arguments bind to one explicit frame specification."""

from __future__ import annotations

from typing import TypedDict

from ._conveniences import bar, pie
from ._errors import AstetikError


class AnimationFields(TypedDict, total=False):
    label_col: object
    plot_type: object
    filename: object
    paper: object
    manifest: object
    units: object
    frame: object
    key: object


class AnimationReceipt(TypedDict):
    schema_version: str
    input_sha256: str
    poster_frame: int
    frame_results: list[str]
    plot_type: str
    frame_order: str


def bind(legacy: tuple[object, ...], options: AnimationFields) -> AnimationFields:
    if len(legacy) > 3:
        raise TypeError('Animation accepts at most six positional arguments')
    bound = options.copy()
    for name, value in zip(('label_col', 'plot_type', 'filename'), legacy):
        if name in bound:
            raise TypeError(f'Animation got multiple values for argument {name!r}')
        if name == 'label_col':
            bound['label_col'] = value
        elif name == 'plot_type':
            bound['plot_type'] = value
        else:
            bound['filename'] = value
    unknown = set(bound) - set(AnimationFields.__annotations__)
    if unknown:
        raise TypeError(f'Animation got an unexpected argument {sorted(unknown)[0]!r}')
    return bound


def plot_kind(value: object) -> str:
    if callable(value):
        if value is bar:
            return 'bar'
        if value is pie:
            return 'pie'
        raise AstetikError('ANIMATION_KIND', 'Use a registered bar/pie plot or its name.')
    if value not in ('bar', 'pie'):
        raise AstetikError('ANIMATION_KIND', 'Animation supports bar and pie frames.')
    return str(value)
