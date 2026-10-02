"""Colour normalization and perceptual design constraints."""
from __future__ import annotations

import math
import re
from collections.abc import Mapping

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def normalize_hex(value: object, name: str) -> str:
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ValueError(f"{name} must be a six-digit hexadecimal colour (#RRGGBB)")
    return value.upper()


def rgb_components(value: str) -> tuple[float, float, float]:
    return int(value[1:3], 16) / 255.0, int(value[3:5], 16) / 255.0, int(value[5:7], 16) / 255.0


def _linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _luminance(value: str) -> float:
    red, green, blue = (_linear(c) for c in rgb_components(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(a: str, b: str) -> float:
    low, high = sorted((_luminance(a), _luminance(b)))
    return (high + 0.05) / (low + 0.05)


def lab_components(value: str) -> tuple[float, float, float]:
    red, green, blue = (_linear(c) for c in rgb_components(value))
    xyz = ((0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047,
           0.2126729 * red + 0.7151522 * green + 0.0721750 * blue,
           (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883)

    def f(v: float) -> float:
        return v ** (1 / 3) if v > (6 / 29) ** 3 else v / (3 * (6 / 29) ** 2) + 4 / 29
    x, y, z = (f(v) for v in xyz)
    return 116 * y - 16, 500 * (x - y), 200 * (y - z)


def color_distance(a: str, b: str) -> float:
    return math.dist(lab_components(a), lab_components(b))


def check_categories(categories: Mapping[str, str], background: str) -> None:
    for label, color in categories.items():
        if contrast_ratio(color, background) < 3:
            raise ValueError(f"Category {label!r} needs at least 3:1 contrast against paper")
    items = list(categories.items())
    for index, (label, color) in enumerate(items):
        for other_label, other_color in items[index + 1:]:
            if color_distance(color, other_color) < 12:
                raise ValueError(f"Category colours for {label!r} and {other_label!r} are too similar; "
                                 "assign distinct colours in manifest.categories")


