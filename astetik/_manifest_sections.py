"""Validate each immutable design section without implicit type coercion."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import cast

from ._color_math import check_categories, color_distance, contrast_ratio, normalize_hex
from ._manifest_types import Axes, ManifestSections, Paper, Spine, Typography

DEFAULT_COLORS = {
    "primary": "#2A4A70", "secondary": "#806A45", "paper": "#F7F7F2",
    "ink": "#252D33", "muted": "#626B72", "line": "#D4DADD",
    "negative": "#A54532", "neutral": "#F7F7F2", "positive": "#2A4A70",
}
DEFAULT_TYPOGRAPHY: Typography = {
    "font": "Finlandica", "font_path": None, "fontsize": 9.0,
    "labelsize": 9.0, "titlesize": 10.0, "ticksize": 8.0, "legendsize": 8.0,
}
DEFAULT_PAPER: Paper = {
    "preset": "single", "width_mm": 89.0, "aspect": 1.45,
    "dpi": 300, "min_fontsize": 7.0,
}
DEFAULT_AXES: Axes = {
    "linewidth": 0.6, "grid": False, "spines": ("left", "bottom"),
    "tick_direction": "out", "tick_length": 2.5,
}


def mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    raw = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise ValueError(f"{name} fields must be strings")
    return cast(Mapping[str, object], raw)


def section(value: object, defaults: Mapping[str, object], name: str) -> dict[str, object]:
    provided = mapping(value, name)
    unknown = set(provided) - set(defaults)
    if unknown:
        raise ValueError(f"Unknown {name} fields: {', '.join(sorted(unknown))}")
    return {**defaults, **provided}


def number(value: object, name: str, minimum: float = 0, *, inclusive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value < minimum if inclusive else value <= minimum:
        comparison = "at least" if inclusive else "greater than"
        raise ValueError(f"{name} must be {comparison} {minimum}")
    return float(value)


def colors_section(value: object) -> dict[str, str]:
    colors = {key: normalize_hex(item, f"colors.{key}") for key, item in section(value, DEFAULT_COLORS, "colors").items()}
    for role in ("ink", "muted"):
        if contrast_ratio(colors[role], colors["paper"]) < 4.5:
            raise ValueError(f"colors.{role} needs at least 4.5:1 contrast against paper")
    for role in ("primary", "secondary", "negative", "positive"):
        if contrast_ratio(colors[role], colors["paper"]) < 3:
            raise ValueError(f"colors.{role} needs at least 3:1 contrast against paper")
    if color_distance(colors["negative"], colors["positive"]) < 35:
        raise ValueError("Negative and positive colours must be perceptually distinct (CIELAB distance >= 35)")
    if any(color_distance(colors["neutral"], colors[role]) < 20 for role in ("negative", "positive")):
        raise ValueError("The neutral colour must be distinct from both diverging endpoints")
    return colors


def categories_section(value: object, colors: Mapping[str, str]) -> dict[str, str]:
    categories: dict[str, str] = {}
    for label, item in mapping(value, 'categories').items():
        if not label.strip():
            raise ValueError("Category labels must be nonempty strings")
        if isinstance(item, str) and item in colors:
            categories[label] = item
        elif isinstance(item, str) and not item.startswith('#'):
            raise ValueError(f"categories.{label} must be a hexadecimal colour or an existing semantic colour role")
        else:
            categories[label] = normalize_hex(item, f"categories.{label}")
    check_categories({label: colors.get(binding, binding) for label, binding in categories.items()}, colors['paper'])
    return categories


def typography_section(value: object) -> Typography:
    policy = section(value, DEFAULT_TYPOGRAPHY, 'typography')
    font, font_path = policy['font'], policy['font_path']
    if not isinstance(font, str) or not font.strip():
        raise ValueError('typography.font must be a nonempty family name')
    if font_path is not None and not isinstance(font_path, str):
        raise ValueError('typography.font_path must be a path string or null')
    return {'font': font, 'font_path': font_path,
            'fontsize': number(policy['fontsize'], 'typography.fontsize'),
            'labelsize': number(policy['labelsize'], 'typography.labelsize'),
            'titlesize': number(policy['titlesize'], 'typography.titlesize'),
            'ticksize': number(policy['ticksize'], 'typography.ticksize'),
            'legendsize': number(policy['legendsize'], 'typography.legendsize')}


def paper_section(value: object) -> Paper:
    provided = mapping(value, 'paper')
    policy = section(value, DEFAULT_PAPER, 'paper')
    preset, dpi = policy['preset'], policy['dpi']
    if preset not in ('single', 'double'):
        raise ValueError("paper.preset must be 'single' or 'double'")
    if 'preset' in provided and 'width_mm' not in provided:
        policy['width_mm'] = 89.0 if preset == 'single' else 178.0
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi < 300:
        raise ValueError('paper.dpi must be an integer of at least 300')
    return {'preset': preset, 'dpi': dpi,
            'width_mm': number(policy['width_mm'], 'paper.width_mm'),
            'aspect': number(policy['aspect'], 'paper.aspect'),
            'min_fontsize': number(policy['min_fontsize'], 'paper.min_fontsize', 7, inclusive=True)}


def spine_names(value: object) -> tuple[Spine, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError('axes.spines must be a list of spine names')
    values = cast(Sequence[object], value)
    if any(not isinstance(item, str) or item not in ('left', 'right', 'top', 'bottom') for item in values):
        raise ValueError('axes.spines contains duplicate or unknown spine names')
    spines = cast(tuple[Spine, ...], tuple(values))
    if len(set(spines)) != len(spines):
        raise ValueError('axes.spines contains duplicate or unknown spine names')
    return spines


def axes_section(value: object) -> Axes:
    policy = section(value, DEFAULT_AXES, 'axes')
    grid, direction = policy['grid'], policy['tick_direction']
    if not isinstance(grid, bool):
        raise ValueError('axes.grid must be a boolean')
    if direction not in ('in', 'out', 'inout'):
        raise ValueError("axes.tick_direction must be 'in', 'out', or 'inout'")
    return {'grid': grid, 'tick_direction': direction,
            'spines': spine_names(policy['spines']),
            'linewidth': number(policy['linewidth'], 'axes.linewidth'),
            'tick_length': number(policy['tick_length'], 'axes.tick_length', inclusive=True)}


def bind_sections(positional: tuple[Mapping[str, object], ...], sections: ManifestSections) -> ManifestSections:
    names = ('colors', 'categories', 'typography', 'paper', 'axes')
    if len(positional) > len(names):
        raise TypeError('Manifest accepts at most six positional arguments')
    bound = dict(sections)
    for name, value in zip(names, positional):
        if name in bound:
            raise TypeError(f"Manifest got multiple values for argument '{name}'")
        bound[name] = value
    unknown = set(bound) - set(names)
    if unknown:
        raise TypeError(f"Manifest got an unexpected argument '{sorted(unknown)[0]}'")
    return cast(ManifestSections, bound)


