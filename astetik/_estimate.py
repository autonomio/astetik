"""Declared central estimates and the intervals drawn around them."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from ._render_context import RendererOptions
from ._types import FloatArray


@dataclass(frozen=True)
class Estimate:
    """One summarised group: its centre and, when declared, its interval."""

    centre: float
    low: float | None
    high: float | None
    n: int

    @property
    def error(self) -> float | None:
        """Half-width of a symmetric interval."""
        return None if self.high is None else self.high - self.centre


def computation(options: RendererOptions) -> str:
    """State the estimator and interval exactly as they were computed."""
    estimator, errorbar = options.get('estimator') or 'mean', options.get('errorbar')
    if errorbar == 'iqr':
        return f'{estimator}; errorbar=iqr; linear quantiles 0.25 and 0.75'
    text = f'{estimator}; errorbar={errorbar}; ddof=1'
    if errorbar == 'ci':
        text += f'; two-sided Student t interval; confidence={options.get("confidence", 0.95)}'
    return text


def estimate(values: FloatArray, options: RendererOptions, group: object) -> Estimate:
    """Summarise one group by the declared estimator and interval; ``group`` names it."""
    estimator, errorbar = options.get('estimator') or 'mean', options.get('errorbar')
    count = len(values)
    centre = float({'mean': np.mean, 'median': np.median, 'sum': np.sum}[estimator](values))
    if errorbar is None:
        return Estimate(centre, None, None, count)
    if errorbar == 'iqr':
        low, high = np.quantile(values, [0.25, 0.75], method='linear')
        return Estimate(centre, float(low), float(high), count)
    if count < 2:
        raise ValueError(
            'SD/SE error bars require at least two observations per group; '
            f'{group!r} has {count}. Use errorbar=None, or prepare groups with replicates.'
        )
    spread = float(np.std(values, ddof=1))
    if errorbar != 'sd':
        spread /= float(np.sqrt(count))
    if errorbar == 'ci':
        spread *= float(stats.t.ppf((1 + options.get('confidence', 0.95)) / 2, count - 1))
    return Estimate(centre, centre - spread, centre + spread, count)
