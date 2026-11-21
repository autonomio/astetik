"""A figure's panels: one complete specification each, bound to the axes that draw it."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn, cast

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from ._errors import AstetikError
from ._spec_json import json_object
from ._spec_types import PlotSpec
from ._types import JsonObject

PANEL_KINDS = ('hist', 'line', 'scat', 'regs', 'bar', 'box', 'violin')
_PANEL_FIELDS = {
    'kind', 'x', 'y', 'hue', 'order', 'hue_order', 'options', 'labels', 'axes', 'title', 'legend'
}
_FIGURE_ONLY = (
    'x', 'y', 'hue', 'row', 'col', 'columns', 'order', 'hue_order', 'axes', 'labels', 'analysis'
)
# Declared once for the figure; a panel may still declare its own legend.
_SHARED = (
    'schema_version', 'paper', 'missing', 'missing_reason', 'key', 'units', 'descriptions', 'legend'
)
_PANEL = '_astetik_panel'


def _refuse(code: str, message: str, **details: object) -> NoReturn:
    raise AstetikError(code, message, details)


def _resolve(
    index: int, panel: object, defaults: Mapping[str, object], supported: Mapping[str, set[str]]
) -> JsonObject:
    if not isinstance(panel, dict) or set(cast(JsonObject, panel)) - _PANEL_FIELDS:
        _refuse('SPEC_SCHEMA', 'A panel accepts these fields.', panel=index,
                allowed=sorted(_PANEL_FIELDS))
    item = cast(JsonObject, panel)
    kind = item.get('kind')
    if not isinstance(kind, str) or kind not in PANEL_KINDS:
        _refuse('PLOT_KIND', 'Choose a supported panel kind.', panel=index,
                allowed=list(PANEL_KINDS))
    options = item.get('options', {})
    if not isinstance(options, dict) or set(options) - supported[kind]:
        _refuse('PLOT_OPTIONS', 'Unsupported options are never ignored.', panel=index, kind=kind,
                allowed=sorted(supported[kind]))
    item['options'] = {**json_object(defaults[kind]), **options}
    item.setdefault('title', '')
    labels = item.get('labels', {})
    if not isinstance(item.get('legend', True), bool) or not isinstance(item['title'], str):
        _refuse('SPEC_SCHEMA', 'A panel legend is a boolean and its title text.', panel=index)
    if not isinstance(labels, dict) or not isinstance(item.get('axes', {}), dict):
        _refuse('SPEC_SCHEMA', 'Panel labels and axes must be objects.', panel=index)
    if set(labels) - {'x', 'y'} or any(not isinstance(v, str) for v in labels.values()):
        _refuse('SPEC_SCHEMA', 'Panel labels accept x and y text.', panel=index)
    return item


def resolve_panels(
    spec: JsonObject, defaults: Mapping[str, object], supported: Mapping[str, set[str]]
) -> list[JsonObject]:
    """Complete each panel's options; refuse fields that belong to the other level."""
    panels = spec.get('panels')
    if spec['kind'] != 'panels':
        if panels is not None:
            _refuse('SPEC_SCHEMA', "panels belongs to kind 'panels'.")
        return []
    stray = sorted(name for name in _FIGURE_ONLY if spec.get(name) is not None)
    if stray:
        _refuse('SPEC_SCHEMA', 'A panels figure declares these inside each panel.', fields=stray)
    if not isinstance(panels, list) or not panels:
        _refuse('SPEC_SCHEMA', 'panels must list at least one panel specification.')
    return [_resolve(index, panel, defaults, supported) for index, panel in enumerate(panels)]


def views(spec: PlotSpec) -> list[PlotSpec]:
    """One complete specification per panel; a single plot is its own only panel."""
    if spec['kind'] != 'panels':
        return [spec]
    shared = {name: value for name, value in spec.items() if name in _SHARED}
    return [cast(PlotSpec, {**shared, 'subtitle': '', **panel}) for panel in spec.get('panels', [])]


def bind(ax: Axes, index: int) -> None:
    """Record which panel an axes draws."""
    setattr(ax, _PANEL, index)


def panel_axes(figure: Figure, spec: PlotSpec) -> list[tuple[PlotSpec, list[Axes]]]:
    """Each panel's specification with the axes it owns, colour bars included."""
    if spec['kind'] != 'panels':
        return [(spec, list(figure.axes))]
    return [
        (view, [ax for ax in figure.axes if getattr(ax, _PANEL, None) == index])
        for index, view in enumerate(views(spec))
    ]
