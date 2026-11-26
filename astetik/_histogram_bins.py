"""Shared histogram bin boundaries and per-series bin statistics."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from ._histogram_options import HistogramOptions, Stat
from ._types import FloatArray

# A double-column figure at 300 dpi resolves about 2 100 device pixels.
MAX_BINS = 2000


def _limit(count: float | int) -> None:
    if count > MAX_BINS:
        if isinstance(count, int):
            label = str(count) if count.bit_length() <= 1024 else 'at least 2^1024'
        else:
            label = f'{count:g}'
        raise ValueError(
            f'Histogram resolves to {label} bins; more than {MAX_BINS} cannot be printed. '
            'Declare coarser bins.'
        )


def bin_edges(values: FloatArray, options: HistogramOptions, log: bool) -> FloatArray:
    """Resolve one set of boundaries from every compared observation."""
    bins, width = options.get('bins', 'auto'), options.get('binwidth')
    if isinstance(bins, bool):
        raise ValueError('bins must be an integer, explicit edges, or a NumPy bin rule.')
    low, high = float(values.min()), float(values.max())
    if width is not None:
        if log:
            raise ValueError('binwidth is linear; declare bins for a logarithmic axis.')
        start = np.floor(low / width) * width
        count = max(1.0, float(np.ceil((high - start) / width)))
        _limit(count)
        edges = start + width * np.arange(int(count) + 1)
    elif isinstance(bins, list):
        edges = np.histogram_bin_edges(values, bins=bins)
    else:
        if isinstance(bins, int):
            _limit(bins)
        edges = (
            10 ** np.histogram_bin_edges(np.log10(values), bins=bins)
            if log
            else np.histogram_bin_edges(values, bins=bins)
        )
    if not isinstance(bins, list):
        # Computed boundaries may miss an extreme by one rounding step.
        edges[0], edges[-1] = min(edges[0], low), max(edges[-1], high)
    if len(edges) < 2 or not np.isfinite(edges).all() or not np.all(np.diff(edges) > 0):
        raise ValueError('Histogram bin edges must be finite and strictly increasing.')
    if edges[0] > low or edges[-1] < high:
        raise ValueError(
            'Histogram bin edges must cover every observation; filtering belongs in the declared data protocol.'
        )
    _limit(len(edges) - 1)
    return edges


def bin_values(
    values: FloatArray, edges: FloatArray, stat: Stat, total: int, cumulative: bool
) -> tuple[NDArray[np.intp], FloatArray]:
    """Return raw bin counts and the declared statistic over ``total`` observations."""
    counts, _ = np.histogram(values, bins=edges)
    if stat == 'density':
        heights = counts / np.diff(edges) / total
    elif stat == 'count':
        heights = counts.astype(float)
    else:
        heights = counts * ((100.0 if stat == 'percent' else 1.0) / total)
    return counts, np.cumsum(heights) if cumulative else heights


def bar_spans(
    edges: FloatArray, shrink: float, index: int, count: int, log: bool
) -> tuple[FloatArray, FloatArray]:
    """Left positions and widths of one series' bars, even in the displayed scale."""
    scaled = np.log10(edges) if log else edges
    width = np.diff(scaled) * shrink / count
    left = scaled[:-1] + np.diff(scaled) * (1 - shrink) / 2 + index * width
    if log:
        return 10**left, 10 ** (left + width) - 10**left
    return left, width
