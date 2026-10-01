"""Validated plot specification contracts, shared by compilation and rendering."""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

from ._render_context import RendererOptions
from ._types import JsonScalar

PaperChoice = bool | Literal['single', 'double']
Dimension = Literal['x', 'y']


class PlotOptions(RendererOptions, total=False):
    frame: int
    plot_type: Literal['bar', 'pie']
    digits: int


class AxisPolicy(TypedDict, total=False):
    scale: Literal['linear', 'log', 'symlog']
    limits: list[float]


class AnalysisPlan(TypedDict, total=False):
    method: Literal['welch', 'paired_t', 'pearson', 'spearman', 'observed']
    confidence: float
    groups: list[JsonScalar]
    observation_unit: str
    subject: str


class PlotSpec(TypedDict):
    schema_version: str
    kind: str
    options: PlotOptions
    paper: PaperChoice
    missing: Literal['error', 'drop']
    legend: bool
    key: list[str]
    title: str
    subtitle: str
    x: NotRequired[str | None]
    y: NotRequired[str | list[str] | None]
    hue: NotRequired[str | None]
    row: NotRequired[str | None]
    col: NotRequired[str | None]
    columns: NotRequired[list[str] | None]
    order: NotRequired[list[JsonScalar] | None]
    units: NotRequired[dict[str, str]]
    descriptions: NotRequired[dict[str, str]]
    labels: NotRequired[dict[Dimension, str]]
    axes: NotRequired[dict[Dimension, AxisPolicy]]
    analysis: NotRequired[AnalysisPlan | None]
    missing_reason: NotRequired[str | None]
