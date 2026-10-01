"""Explicit scientific protocols; plotting never chooses an inference method."""
from __future__ import annotations

import pandas as pd

from ._analysis_association import association
from ._analysis_comparison import comparison
from ._analysis_longitudinal import longitudinal
from ._analysis_policy import methods_for, resolve_plan
from ._analysis_types import AnalysisResult
from ._spec_types import PlotSpec


def analyze(data: pd.DataFrame, spec: PlotSpec) -> AnalysisResult | None:
    plan = resolve_plan(spec)
    if plan is None:
        return None
    x, y = spec.get('x'), spec.get('y')
    assert isinstance(x, str) and isinstance(y, str)
    methods = methods_for(plan)
    if plan.kind == 'comparison':
        return comparison(data, plan, x, y, methods)
    if plan.kind == 'association':
        return association(data, plan, x, y, methods)
    return longitudinal(data, spec, x, y, methods)
