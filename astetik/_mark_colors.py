"""Colours of drawn series: manifest bindings, or one declared colour for a single series."""

from __future__ import annotations

from ._color_math import normalize_hex
from ._manifest import Manifest
from ._render_common import series_colors
from ._render_context import ColorMapping, RenderContext


def resolve_color(manifest: Manifest, value: str, name: str) -> str:
    if value in manifest.colors:
        return manifest.colors[value]
    if not value.startswith('#'):
        raise ValueError(
            f'{name} must be a manifest colour role ({", ".join(manifest.colors)}) or #RRGGBB.'
        )
    return normalize_hex(value, name)


def series_mapping(context: RenderContext, columns: list[str], grouped: bool) -> ColorMapping:
    """Colour per hue group or measured column; ``color`` restyles a single series."""
    spec, color = context.spec, context.options.get('color')
    if color is None:
        if spec.get('hue'):
            return spec['_hue_colors']
        return series_colors(spec['_manifest'], columns, spec['_paper'])
    if grouped:
        raise ValueError('color applies to one series; bind groups in manifest.categories.')
    return {columns[0]: resolve_color(spec['_manifest'], color, 'color')}


def edge_color(context: RenderContext, automatic: str) -> str:
    """The declared mark edge colour; ``auto`` resolves to the kind's own default."""
    edge = context.options.get('edgecolor', 'auto')
    return automatic if edge == 'auto' else resolve_color(context.spec['_manifest'], edge, 'edgecolor')


def legend_size(context: RenderContext) -> float:
    manifest = context.spec['_manifest']
    floor = manifest.paper['min_fontsize'] if context.spec['_paper'] else 0
    return max(manifest.typography['legendsize'], floor)
