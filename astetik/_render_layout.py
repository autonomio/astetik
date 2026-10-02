"""Shared facet geometry without modifying scientific domains."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._manifest import Manifest
from ._render_common import equal, levels
from ._render_context import Facet, FacetPlan, RendererOptions, RendererSpec


def figure_dimensions(
    manifest: Manifest, paper: bool, nrows: int, ncols: int
) -> tuple[float, float]:
    width, height = manifest.dimensions(paper, panels=1)
    return width, height * nrows / ncols


def facet_plan(
    data: pd.DataFrame,
    spec: RendererSpec,
    options: RendererOptions,
    manifest: Manifest,
    paper: bool,
) -> tuple[int, int, FacetPlan]:
    row, col = spec.get('row'), spec.get('col')
    rlevels = levels(data[row]) if row else [None]
    clevels = levels(data[col]) if col else [None]
    if row and options.get('col_wrap'):
        raise ValueError('col_wrap cannot be combined with row facets.')
    wrap = options.get('col_wrap')
    if paper and col and not row and wrap is None:
        wrap = 2 if manifest.paper['preset'] == 'double' else 1
    ncols = min(wrap, len(clevels)) if wrap else len(clevels)
    nrows = int(np.ceil(len(clevels) / ncols)) if wrap else len(rlevels)
    facets: FacetPlan = []
    for i, rvalue in enumerate(rlevels):
        for j, cvalue in enumerate(clevels):
            mask = np.ones(len(data), dtype=bool)
            labels: Facet = {}
            if row:
                mask &= equal(data[row], rvalue)
                labels[row] = rvalue
            if col:
                mask &= equal(data[col], cvalue)
                labels[col] = cvalue
            slot = j if wrap else i * ncols + j
            facets.append((slot, np.flatnonzero(mask), labels))
    return nrows, ncols, facets
