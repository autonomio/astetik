"""Typed state shared by deterministic renderer operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, NotRequired, TypeAlias, TypedDict, cast

import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray
from scipy.stats import gaussian_kde

from ._colors import ColorSystem
from ._manifest import Manifest
from ._types import FloatArray, JsonObject, JsonScalar

RowArray: TypeAlias = NDArray[np.intp]
ColorMapping: TypeAlias = dict[JsonScalar, str]
Facet: TypeAlias = dict[str, JsonScalar]
FacetPlan: TypeAlias = list[tuple[int, RowArray, Facet]]


class RendererOptions(TypedDict, total=False):
    method: Literal['pearson', 'spearman', 'kendall']
    annot: bool
    mask: bool
    bins: (
        int
        | Literal['auto', 'fd', 'doane', 'scott', 'stone', 'rice', 'sturges', 'sqrt']
        | list[float]
    )
    density: bool
    kde: bool
    alpha: float
    orient: Literal['v', 'h']
    bw_method: Literal['scott', 'silverman'] | float
    gridsize: int
    cut: float
    cumulative: bool
    fill: bool
    startangle: float
    percent: bool
    point_size: float
    dodge: bool
    width: float
    marker: str | None
    hue_mode: Literal['auto', 'categorical', 'continuous']
    linewidth: float
    linestyle: Literal[
        'solid', 'dashed', 'dashdot', 'dotted', '-', '--', '-.', ':', 'None', ' ', ''
    ]
    sort: bool
    drawstyle: Literal['default', 'steps', 'steps-pre', 'steps-mid', 'steps-post']
    jitter: float
    whis: float
    split: bool
    estimator: Literal['mean', 'median', 'sum']
    errorbar: Literal['sd', 'se'] | None
    log: bool
    fit_reg: bool
    draw_scatter: bool
    positive_label: JsonScalar
    col_wrap: int | None


@dataclass
class DensityFit:
    model: gaussian_kde[np.float64]
    xx: FloatArray | None = None
    yy: FloatArray | None = None
    density: FloatArray | None = None


class RendererSpec(TypedDict):
    kind: str
    x: NotRequired[str | list[str] | None]
    y: NotRequired[str | list[str] | None]
    hue: NotRequired[str | None]
    row: NotRequired[str | None]
    col: NotRequired[str | None]
    columns: NotRequired[list[str] | None]
    order: NotRequired[list[JsonScalar] | None]
    options: NotRequired[RendererOptions]
    key: NotRequired[list[str]]
    legend: NotRequired[bool]
    label_col: NotRequired[str | None]
    _manifest: Manifest
    _paper: bool
    _hue_colors: ColorMapping
    _kde2d: NotRequired[dict[tuple[int, ...], DensityFit]]
    _kde2d_domain: NotRequired[tuple[float, float]]


@dataclass
class Recorder:
    marks: list[JsonObject] = field(default_factory=lambda: list[JsonObject]())
    methods: JsonObject = field(
        default_factory=lambda: {
            'renderer': 'matplotlib-object-api',
            'source_rows': 'zero-based input positions',
        }
    )

    def mark(
        self,
        kind: str,
        values: Mapping[str, object],
        rows: RowArray | list[int],
        computation: str,
        facet: Facet | None = None,
    ) -> JsonObject:
        from ._render_scalar import scalar

        item: JsonObject = {
            'id': f'm{len(self.marks):06d}',
            'kind': kind,
            'values': {str(k): scalar(v) for k, v in values.items()},
            'source_rows': [int(p) for p in rows],
            'computation': computation,
        }
        if facet:
            item['facet'] = {str(k): scalar(v) for k, v in facet.items()}
        self.marks.append(item)
        return item

    def append_method(self, key: str, record: JsonObject) -> None:
        values = self.methods.setdefault(key, [])
        if not isinstance(values, list):
            raise ValueError(f'Method {key!r} must contain records.')
        values.append(record)

    def table(self) -> pd.DataFrame:
        records: list[JsonObject] = []
        for mark in self.marks:
            values = mark['values']
            if not isinstance(values, dict):
                raise ValueError('Recorded mark values must be an object.')
            records.append(
                {
                    'mark_id': mark['id'],
                    'mark_kind': mark['kind'],
                    **values,
                    'source_rows': mark['source_rows'],
                    'computation': mark['computation'],
                    'facet': mark.get('facet', {}),
                }
            )
        return pd.DataFrame(records)


@dataclass
class RenderContext:
    ax: Axes
    data: pd.DataFrame
    rows: RowArray
    spec: RendererSpec
    options: RendererOptions
    colors: ColorSystem
    rec: Recorder
    facet: Facet
    kind: str
    analysis: JsonObject | None = None

    def column(self, axis: Literal['x', 'y']) -> str:
        value = self.spec.get(axis)
        if not isinstance(value, str):
            raise ValueError(f'{self.kind} requires one {axis} column.')
        return value


@dataclass
class Rendered:
    figure: Figure
    table: pd.DataFrame
    marks: list[JsonObject]
    methods: JsonObject


def required_column(spec: RendererSpec, axis: Literal['x', 'y']) -> str:
    value = spec.get(axis)
    if not isinstance(value, str):
        raise ValueError(f'{spec["kind"]} requires one {axis} column.')
    return value


def measure_columns(spec: RendererSpec, axis: Literal['x', 'y']) -> list[str]:
    value = spec.get(axis)
    if isinstance(value, list):
        return cast(list[str], value)
    return [required_column(spec, axis)]
