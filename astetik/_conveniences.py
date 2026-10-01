"""Explicit plot conveniences retain argument order and delegate to compilation."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, cast

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike

from ._data import normalize
from ._entry import plot
from ._legacy_options import mapping, translate
from ._result import EvidenceResult
from ._spec import fail


class PlotFunction(Protocol):
    __name__: str
    __doc__: str | None

    def __call__(
        self,
        data: object,
        x: object = None,
        y: object = None,
        *,
        paper: object = False,
        manifest: object = None,
        **kwargs: object,
    ) -> EvidenceResult: ...


def _legacy(name: str) -> PlotFunction:
    def call(
        data: object,
        x: object = None,
        y: object = None,
        *,
        paper: object = False,
        manifest: object = None,
        **kwargs: object,
    ) -> EvidenceResult:
        if name == 'line':
            x, y = y, x
            if x is None:
                if paper:
                    fail('TIME_REQUIRED', 'Declare the time column for a paper line plot.')
                original = normalize(data).data
                original['__astetik_observation__'] = np.arange(len(original))
                data, x = original, '__astetik_observation__'
                units = mapping(kwargs.setdefault('units', {}), 'units')
                units['__astetik_observation__'] = '1'
                kwargs['units'] = units
        if name == 'world':
            x, y = kwargs.pop('area_col', x), kwargs.pop('value_col', y)
        translate(kwargs)
        save = kwargs.pop('save', False)
        if save is True:
            fail(
                'OUTPUT_PATH_REQUIRED',
                'Pass a new bundle directory through save or result.write(path).',
            )
        result = plot(data, name, x=x, y=y, paper=paper, manifest=manifest, **kwargs)
        if save:
            if not isinstance(save, (str, Path)):
                fail('OUTPUT_PATH_REQUIRED', 'save must name a new bundle directory.')
            result.write(save)
        return result

    call.__name__ = name
    call.__doc__ = f'Render {name} with centralized design and optional paper=True. Returns EvidenceResult. See catalog() for supported options.'
    return call


animate = _legacy('animate')
association = _legacy('association')
bar = _legacy('bar')
bargrid = _legacy('bargrid')
bartwo = _legacy('bartwo')
box = _legacy('box')
compare = _legacy('compare')
comparison = _legacy('comparison')
corr = _legacy('corr')
count = _legacy('count')
grid = _legacy('grid')
hist = _legacy('hist')
kde = _legacy('kde')
line = _legacy('line')
longitudinal = _legacy('longitudinal')
multicount = _legacy('multicount')
multikde = _legacy('multikde')
overlap = _legacy('overlap')
pie = _legacy('pie')
regs = _legacy('regs')
scat = _legacy('scat')
strip = _legacy('strip')
swarm = _legacy('swarm')
table = _legacy('table')
text = _legacy('text')
violin = _legacy('violin')
world = _legacy('world')


def roc(
    y_pred: object,
    y_true: object,
    *,
    paper: object = False,
    manifest: object = None,
    **kwargs: object,
) -> EvidenceResult:
    """Preserved binary ROC argument order with explicit truth/score semantics."""
    frame = pd.DataFrame({'score': y_pred, 'truth': y_true})
    kwargs.setdefault('units', {'score': '1', 'truth': '1'})
    return plot(frame, 'roc', x='truth', y='score', paper=paper, manifest=manifest, **kwargs)


def oned(
    data: object, *, paper: object = False, manifest: object = None, **kwargs: object
) -> EvidenceResult:
    """Event plot of retained one-dimensional observations."""
    return plot(
        pd.DataFrame({'value': data}), 'oned', x='value', paper=paper, manifest=manifest, **kwargs
    )


def twod(
    x: object, y: object = None, *, paper: object = False, manifest: object = None, **kwargs: object
) -> EvidenceResult:
    """Two-dimensional observations from paired vectors or an N by 2 array."""
    values = np.asarray(cast(ArrayLike, x))
    if y is None:
        if values.ndim == 2 and values.shape[1] == 2:
            x, y = values[:, 0], values[:, 1]
        elif values.ndim == 1 and len(values) % 2 == 0:
            x, y = np.split(values, 2)
        else:
            fail('TWOD_SHAPE', 'Supply two equally sized vectors or an N by 2 array.')
    return plot(
        pd.DataFrame({'x': x, 'y': y}),
        'twod',
        x='x',
        y='y',
        paper=paper,
        manifest=manifest,
        **kwargs,
    )
