"Semantic colour encodings with stable, inspectable category assignments."

from __future__ import annotations

import json
from collections.abc import Iterable
from hashlib import sha256
from typing import cast

import numpy as np
from matplotlib.colors import ListedColormap

from ._manifest import Manifest, check_categories, lab_components, normalize_hex, rgb_components
from ._types import JsonScalar

# Dark categorical encodings retain at least 3:1 contrast on the default paper.
# Hash assignment is independent of input order; ambiguous assignments fail.
_CATEGORY_PALETTE = (
    '#2A4A70',
    '#AC4B35',
    '#2D7D60',
    '#7D5595',
    '#9A7016',
    '#497F8D',
    '#A44C79',
    '#697B32',
    '#744A3B',
    '#505EA5',
    '#A05D18',
    '#6A6B72',
)


def _scalar(label: object) -> JsonScalar:
    if isinstance(label, np.generic):
        label = cast(object, label.item())
    if not isinstance(label, (str, int, float, bool)):
        raise ValueError('Category labels must be finite scalar strings or numbers')
    try:
        json.dumps(label, allow_nan=False)
        hash(label)
    except (ValueError, TypeError) as exc:
        raise ValueError('Category labels must be finite, hashable scalars') from exc
    return label


def _lab_rgb(lab: tuple[float, float, float]) -> tuple[float, float, float]:
    lightness, a, b = lab
    y = (lightness + 16) / 116
    x, z = y + a / 500, y - b / 200

    def inverse(v: float) -> float:
        return v**3 if v > 6 / 29 else 3 * (6 / 29) ** 2 * (v - 4 / 29)

    x, y, z = inverse(x) * 0.95047, inverse(y), inverse(z) * 1.08883
    channels = (
        3.2404542 * x - 1.5371385 * y - 0.4985314 * z,
        -0.9692660 * x + 1.8760108 * y + 0.0415560 * z,
        0.0556434 * x - 0.2040259 * y + 1.0572252 * z,
    )

    def transfer(v: float) -> float:
        c = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        return min(1.0, max(0.0, c))

    return transfer(channels[0]), transfer(channels[1]), transfer(channels[2])


def _ramp(start: str, end: str, steps: int) -> list[tuple[float, float, float]]:
    a, b = lab_components(start), lab_components(end)
    result = [
        _lab_rgb(
            (
                a[0] + (b[0] - a[0]) * i / (steps - 1),
                a[1] + (b[1] - a[1]) * i / (steps - 1),
                a[2] + (b[2] - a[2]) * i / (steps - 1),
            )
        )
        for i in range(steps)
    ]
    result[0], result[-1] = rgb_components(start), rgb_components(end)
    return result


class ColorSystem:
    """A single communication policy for categories, magnitude, and signed effects.

    Category colour derives from label identity or an explicit hex/semantic-role binding.
    Paper output requires explicit bindings when more than one category is shown.
    """

    def __init__(self, manifest: Manifest) -> None:
        self.manifest = manifest

    @property
    def primary(self) -> str:
        return self.manifest.colors['primary']

    def categorical(self, labels: Iterable[object], strict: bool = False) -> dict[JsonScalar, str]:
        unique = list(dict.fromkeys(_scalar(label) for label in labels))
        if len({str(label) for label in unique}) != len(unique):
            raise ValueError(
                'Category labels have ambiguous string identities; use one consistent scalar type'
            )
        mapping: dict[JsonScalar, str] = {}
        missing = [label for label in unique if str(label) not in self.manifest.categories]
        if strict and len(unique) > 1 and missing:
            raise ValueError(
                'Paper output requires explicit manifest.categories colours for: '
                + ', '.join(repr(label) for label in missing)
            )
        for label in unique:
            key = str(label)
            if key in self.manifest.categories:
                binding = self.manifest.categories[key]
                color = self.manifest.colors.get(binding, binding)
            else:
                # str identity also lets numeric category names bind to JSON keys.
                index = int.from_bytes(sha256(key.encode('utf-8')).digest()[:4], 'big') % len(
                    _CATEGORY_PALETTE
                )
                color = _CATEGORY_PALETTE[index]
            mapping[label] = normalize_hex(color, f'Category {label!r}')
        check_categories(
            {str(label): color for label, color in mapping.items()}, self.manifest.colors['paper']
        )
        return mapping

    def sequential(self) -> ListedColormap:
        return ListedColormap(
            _ramp(self.manifest.colors['paper'], self.primary, 256), name='astetik_sequential'
        )

    def diverging(self) -> ListedColormap:
        colors = self.manifest.colors
        left = _ramp(colors['negative'], colors['neutral'], 129)
        right = _ramp(colors['neutral'], colors['positive'], 129)
        return ListedColormap(left + right[1:], name='astetik_diverging')
