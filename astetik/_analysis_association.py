"""Explicit correlation protocols with recorded assumptions and interval method."""
from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
from scipy import stats

from ._analysis_policy import fail
from ._analysis_types import AnalysisMethods, AnalysisResult, AssociationStatistics, ProtocolPlan
from ._types import FloatArray


def association(data: pd.DataFrame, plan: ProtocolPlan, x: str, y: str, methods: AnalysisMethods) -> AnalysisResult:
    methods['assumptions'].append('Independent paired observations; Pearson tests use the bivariate-normal model and Fisher interval approximation.' if plan.method == 'pearson'
                                  else 'Independent paired observations; Spearman significance uses an asymptotic approximation.')
    if len(data) < 4:
        fail('SAMPLE_SIZE', 'Association reporting needs at least four independent observations.')
    a, b = cast(FloatArray, data[x].to_numpy(float)), cast(FloatArray, data[y].to_numpy(float))
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        fail('DEGENERATE_ANALYSIS', 'A constant variable has undefined correlation.')
    lower: float | None
    upper: float | None
    if plan.method == 'pearson':
        result = stats.pearsonr(a, b)
        interval = result.confidence_interval(confidence_level=plan.confidence)
        lower, upper = float(interval.low), float(interval.high)
        methods['interval'] = 'Fisher transformation'
        coefficient, p_value = float(result.statistic), float(result.pvalue)
    else:
        rank_result = stats.spearmanr(a, b)
        coefficient, p_value = float(rank_result.statistic), float(rank_result.pvalue)
        lower = upper = None
        methods.update(interval='Not estimated', p_value='Asymptotic approximation; precision depends on sample size.')
    numerical: AssociationStatistics = {'method': plan.method, 'n': len(data), 'estimate': coefficient, 'lower': lower,
                                       'upper': upper, 'confidence': plan.confidence if lower is not None else None, 'p_value': p_value}
    return {'summary': [numerical], 'statistics': numerical, 'methods': methods,
            'caption': f'{plan.method.capitalize()} correlation {coefficient:.4g}; n = {len(data)}. '
                       + (f'{plan.confidence:.0%} confidence interval [{lower:.4g}, {upper:.4g}]. '
                          if lower is not None and upper is not None else 'Confidence interval not estimated. ')
                       + 'Association does not establish causation.'}
