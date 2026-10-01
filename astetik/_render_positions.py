"""Positions rendering with explicit scientific provenance."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.axes import Axes

from ._render_common import (
    figure_for,
)
from ._types import FloatArray


def van_der_corput(n: int) -> float:
    value, denominator = 0.0, 1.0
    while n:
        n, remainder = divmod(n, 2)
        denominator *= 2
        value += remainder / denominator
    return value


@dataclass
class SwarmLayout:
    position: float
    horizontal: bool
    size: float
    bound: float


def swarm_offsets(ax: Axes, values: FloatArray, layout: SwarmLayout) -> FloatArray:
    position, horizontal, size, bound = (
        layout.position,
        layout.horizontal,
        layout.size,
        layout.bound,
    )
    # Categories and full measured domain are resolved before packing.
    if horizontal:
        points = ax.transData.transform(np.column_stack((values, np.full(len(values), position))))
        categorical_pixel = (
            ax.transData.transform((0.0, position + 1))[1]
            - ax.transData.transform((0.0, position))[1]
        )
        numeric_pixels = points[:, 0]
    else:
        points = ax.transData.transform(np.column_stack((np.full(len(values), position), values)))
        categorical_pixel = (
            ax.transData.transform((position + 1, 0.0))[0]
            - ax.transData.transform((position, 0.0))[0]
        )
        numeric_pixels = points[:, 1]
    radius = np.sqrt(size) * figure_for(ax).dpi / 72 * 1.1
    offsets = np.zeros(len(values))
    placed: list[int] = []
    for index in np.argsort(values, kind='stable'):
        i = int(index)
        candidates = [0.0]
        for j in placed:
            distance = abs(numeric_pixels[i] - numeric_pixels[j])
            if distance < radius:
                width = np.sqrt(radius**2 - distance**2)
                candidates.extend(
                    [offsets[j] * categorical_pixel + width, offsets[j] * categorical_pixel - width]
                )
        chosen = None
        for c in sorted(candidates, key=lambda v: (abs(v), v)):
            if abs(c / categorical_pixel) > bound:
                continue
            if all(
                (numeric_pixels[i] - numeric_pixels[j]) ** 2
                + (c - offsets[j] * categorical_pixel) ** 2
                >= radius**2 * 0.999
                for j in placed
            ):
                chosen = c / categorical_pixel
                break
        if chosen is None:
            raise ValueError(
                'Swarm cannot display all observations without overlap at this size; use strip or a larger manifest dimension.'
            )
        offsets[i] = chosen
        placed.append(i)
    return offsets
