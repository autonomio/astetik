"""Declared Welch and paired mean contrasts with unchanged numerical formulas."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd
from scipy import stats

from ._analysis_policy import fail
from ._analysis_types import AnalysisMethods, AnalysisResult, Contrast, GroupSummary, ProtocolPlan
from ._types import FloatArray, JsonScalar


@dataclass(frozen=True)
class ContrastEstimate:
    """Sufficient numerical quantities for the declared t contrast."""

    estimate: float
    degrees: float
    se: float
    n: int | list[int]


def _group_summary(group: JsonScalar, values: FloatArray, confidence: float) -> GroupSummary:
    mean, sd = float(np.mean(values)), float(np.std(values, ddof=1))
    half = float(stats.t.ppf((1 + confidence) / 2, len(values) - 1) * sd / math.sqrt(len(values)))
    return {'group': group, 'n': len(values), 'estimate': mean, 'sd': sd, 'lower': mean - half, 'upper': mean + half}


def _welch(a: FloatArray, b: FloatArray) -> ContrastEstimate:
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    if va + vb == 0:
        fail('DEGENERATE_ANALYSIS', 'The contrast has zero sampling variance.')
    degrees = float((va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)))
    return ContrastEstimate(float(np.mean(b) - np.mean(a)), degrees, math.sqrt(float(va + vb)), [len(a), len(b)])


def _paired(data: pd.DataFrame, plan: ProtocolPlan, x: str, y: str, methods: AnalysisMethods) -> ContrastEstimate:
    subject = plan.subject
    if subject is None or subject not in data.columns:
        fail('PAIRING_REQUIRED', 'paired_t requires a subject column.')
    if data[subject].isna().any():
        fail('PAIRING_INCOMPLETE', 'Every paired measurement needs a complete subject identity.')
    if data.duplicated([subject, x]).any():
        fail('PAIRING_DUPLICATE', 'Each subject must have exactly one observation in each group.')
    assert plan.groups is not None
    pairs = data.pivot(index=subject, columns=x, values=y).reindex(columns=list(plan.groups))
    if pairs.isna().any().any():
        fail('PAIRING_INCOMPLETE', 'Every subject must have both declared measurements.')
    differences = cast(FloatArray, pairs.iloc[:, 1].to_numpy(float) - pairs.iloc[:, 0].to_numpy(float))
    n = len(differences)
    if n < 2:
        fail('SAMPLE_SIZE', 'Paired inference needs at least two complete pairs.')
    se = float(np.std(differences, ddof=1) / math.sqrt(n))
    if se == 0:
        fail('DEGENERATE_ANALYSIS', 'Paired differences have zero sampling variance.')
    methods.update(subject=subject, pairing='Exact subject identity; incomplete pairs rejected.')
    return ContrastEstimate(float(np.mean(differences)), float(n - 1), se, n)


def comparison(data: pd.DataFrame, plan: ProtocolPlan, x: str, y: str, methods: AnalysisMethods) -> AnalysisResult:
    methods['assumptions'].append('Independent groups with approximately normal sampling means; unequal variances are permitted.' if plan.method == 'welch'
                                  else 'Independent subjects with approximately normal within-subject differences.')
    assert plan.groups is not None
    groups = list(plan.groups)
    actual = data[x].unique().tolist()
    if set(map(str, actual)) != set(map(str, groups)):
        fail('GROUPS_MISMATCH', 'The input must contain exactly the declared groups.', observed=actual, declared=groups)
    samples = [cast(FloatArray, data.loc[data[x] == group, y].to_numpy(dtype=float)) for group in groups]
    if min(map(len, samples)) < 2:
        fail('SAMPLE_SIZE', 'Each group needs at least two observations.')
    summary = [_group_summary(group, values, plan.confidence) for group, values in zip(groups, samples)]
    estimate = _welch(samples[0], samples[1]) if plan.method == 'welch' else _paired(data, plan, x, y, methods)
    half = float(stats.t.ppf((1 + plan.confidence) / 2, estimate.degrees) * estimate.se)
    statistic = estimate.estimate / estimate.se
    contrast: Contrast = {'comparison': f'{groups[1]} minus {groups[0]}', 'estimate': estimate.estimate,
                          'lower': estimate.estimate - half, 'upper': estimate.estimate + half, 'confidence': plan.confidence,
                          'statistic': statistic, 'degrees_of_freedom': estimate.degrees,
                          'p_value': float(2 * stats.t.sf(abs(statistic), estimate.degrees)), 'n': estimate.n}
    methods.update(groups=groups, contrast='second minus first', group_intervals='Student t intervals for group means',
                   contrast_interval='Welch t' if plan.method == 'welch' else 'Paired Student t')
    return {'summary': summary, 'contrast': contrast, 'methods': methods,
            'caption': f'{contrast["comparison"]}: mean difference {estimate.estimate:.4g}, '
                       f'{plan.confidence:.0%} confidence interval [{contrast["lower"]:.4g}, {contrast["upper"]:.4g}]. '
                       f'Method: {plan.method}; group sizes {len(samples[0])} and {len(samples[1])}.'}
