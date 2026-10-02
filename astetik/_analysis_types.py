"""Declared scientific methods and their numerical evidence representations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NotRequired, TypedDict

from ._types import JsonObject, JsonScalar

Method = Literal['welch', 'paired_t', 'pearson', 'spearman', 'observed']


@dataclass(frozen=True)
class ProtocolPlan:
    """A validated method declaration before any numerical computation."""

    kind: Literal['comparison', 'association', 'longitudinal']
    method: Method
    observation_unit: str
    confidence: float
    groups: tuple[JsonScalar, JsonScalar] | None = None
    subject: str | None = None


class AnalysisMethods(TypedDict):
    """Method choices, assumptions, and operation-specific provenance."""

    method: Method
    observation_unit: str
    confidence: float | None
    assumptions: list[str]
    subject: NotRequired[str]
    pairing: NotRequired[str]
    groups: NotRequired[list[JsonScalar]]
    contrast: NotRequired[str]
    group_intervals: NotRequired[str]
    contrast_interval: NotRequired[str]
    interval: NotRequired[str]
    p_value: NotRequired[str]
    order: NotRequired[str]
    interpolation: NotRequired[str]
    inference: NotRequired[str]


class GroupSummary(TypedDict):
    """One declared group's Student t interval and sample dispersion."""

    group: JsonScalar
    n: int
    estimate: float
    sd: float
    lower: float
    upper: float


class Contrast(TypedDict):
    """An ordered mean contrast with an explicitly declared confidence interval."""

    comparison: str
    estimate: float
    lower: float
    upper: float
    confidence: float
    statistic: float
    degrees_of_freedom: float
    p_value: float
    n: int | list[int]


class AssociationStatistics(TypedDict):
    """Declared correlation method, significance, and optional interval."""

    method: Method
    n: int
    estimate: float
    lower: float | None
    upper: float | None
    confidence: float | None
    p_value: float


class AnalysisResult(TypedDict):
    """Numerical evidence and explanatory method text retained with a result."""

    summary: list[GroupSummary] | list[AssociationStatistics] | list[JsonObject]
    methods: AnalysisMethods
    caption: str
    contrast: NotRequired[Contrast]
    statistics: NotRequired[AssociationStatistics]
