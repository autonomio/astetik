"""Reject ambiguous specification fields before scientific compilation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn, cast

from ._errors import AstetikError
from ._spec_json import json_object
from ._spec_types import PlotSpec
from ._types import JsonObject, JsonValue

FIELDS = {
    'schema_version',
    'kind',
    'x',
    'y',
    'hue',
    'row',
    'col',
    'columns',
    'order',
    'options',
    'title',
    'subtitle',
    'labels',
    'paper',
    'key',
    'units',
    'descriptions',
    'missing',
    'missing_reason',
    'analysis',
    'axes',
    'legend',
}


def fail(code: str, message: str, **details: object) -> NoReturn:
    raise AstetikError(code, message, details)


def _objects(result: JsonObject) -> None:
    for name in ('units', 'descriptions', 'labels', 'axes', 'options'):
        if not isinstance(result.get(name, {}), dict):
            fail('SPEC_SCHEMA', f'{name} must be an object.')
    labels = cast(JsonObject, result.get('labels', {}))
    if set(labels) - {'x', 'y'}:
        fail('SPEC_SCHEMA', 'labels accepts x and y only.')
    for name in ('units', 'descriptions', 'labels'):
        section = cast(JsonObject, result.get(name, {}))
        if any(not isinstance(value, str) for value in section.values()):
            fail('SPEC_SCHEMA', 'Units, descriptions, and labels must be text.')
    for name in ('title', 'subtitle'):
        if not isinstance(result.get(name, ''), str):
            fail('SPEC_SCHEMA', f'{name} must be text.')
        result.setdefault(name, '')
    analysis = result.get('analysis')
    if analysis is not None and not isinstance(analysis, dict):
        fail('ANALYSIS_SCHEMA', 'analysis must be an object.')


def _policies(result: JsonObject) -> None:
    result.setdefault('paper', False)
    result.setdefault('missing', 'error')
    result.setdefault('legend', True)
    if not isinstance(result['legend'], bool):
        fail('SPEC_SCHEMA', 'legend must be a boolean.')
    if result['missing'] not in ('error', 'drop'):
        fail('MISSING_POLICY', 'missing must be error or drop.')
    reason = result.get('missing_reason', '')
    if reason is not None and not isinstance(reason, str):
        fail('SPEC_SCHEMA', 'missing_reason must be text.')
    if result['missing'] == 'drop' and not (reason or '').strip():
        fail('EXCLUSION_REASON', 'Declare why incomplete observations may be excluded.')
    key = result.get('key', [])
    if isinstance(key, str):
        key = [key]
    if not isinstance(key, list) or any(not isinstance(v, str) for v in key):
        fail('KEY_SCHEMA', 'key must contain distinct column names.')
    names = cast(list[str], key)
    if len(names) != len(set(names)):
        fail('KEY_SCHEMA', 'key must contain distinct column names.')
    result['key'] = cast(list[JsonValue], key)


def _axes(result: JsonObject) -> None:
    axes = cast(JsonObject, result.get('axes', {}))
    if set(axes) - {'x', 'y'}:
        fail('AXIS_SCHEMA', 'axes accepts x and y only.')
    for policy in axes.values():
        if not isinstance(policy, dict) or set(policy) - {'scale', 'limits'}:
            fail('AXIS_SCHEMA', 'Axis policies accept scale and limits.')
        if policy.get('scale', 'linear') not in ('linear', 'log', 'symlog'):
            fail('AXIS_SCALE', 'Supported scales are linear, log, symlog.')
        limits = policy.get('limits')
        if limits is None:
            continue
        if not isinstance(limits, list) or len(limits) != 2:
            fail('AXIS_LIMITS', 'Axis limits need two increasing finite numbers.')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in limits):
            fail('AXIS_LIMITS', 'Axis limits need two increasing finite numbers.')
        numeric = cast(list[float], limits)
        if numeric[0] >= numeric[1]:
            fail('AXIS_LIMITS', 'Axis limits need two increasing finite numbers.')


def _columns(result: JsonObject) -> None:
    for name in ('x', 'y', 'hue', 'row', 'col'):
        value = result.get(name)
        multiple = (
            name == 'y' and isinstance(value, list) and all(isinstance(v, str) for v in value)
        )
        if value is not None and not isinstance(value, str) and not multiple:
            fail('COLUMN_SCHEMA', f'{name} must name a column.')
    requested = result.get('columns')
    if requested is not None and (
        not isinstance(requested, list)
        or any(not isinstance(value, str) for value in requested)
        or len(requested) != len(set(cast(list[str], requested)))
    ):
        fail('COLUMN_SCHEMA', 'columns must be a list of distinct column names.')


def _order(value: object) -> None:
    if value is not None and not isinstance(value, list):
        fail('SPEC_SCHEMA', 'order must be a list of scalar category labels.')
    if isinstance(value, list) and any(
        item is not None and not isinstance(item, (str, int, float, bool))
        for item in cast(list[object], value)
    ):
        fail('SPEC_SCHEMA', 'order must contain scalar category labels.')


def resolve(
    spec: object,
    kinds: tuple[str, ...],
    defaults: Mapping[str, object],
    supported: Mapping[str, set[str]],
) -> PlotSpec:
    if not isinstance(spec, dict):
        fail('SPEC_SCHEMA', 'A plot specification must be a JSON object.')
    try:
        result = json_object(cast(object, spec))
    except (TypeError, ValueError) as error:
        fail('SPEC_SCHEMA', 'Specifications contain JSON data only.', reason=str(error))
    if 'order' in result:
        _order(result['order'])
    unknown = set(result) - FIELDS
    if unknown:
        fail('SPEC_SCHEMA', 'Unknown specification fields.', fields=sorted(unknown))
    if result.get('schema_version', '1.0') != '1.0':
        fail('SPEC_VERSION', 'Supported specification schema is 1.0.')
    kind = result.get('kind')
    if not isinstance(kind, str) or kind not in kinds:
        fail('PLOT_KIND', 'Choose a supported plot kind.', allowed=list(kinds))
    result['schema_version'] = '1.0'
    _objects(result)
    options = cast(JsonObject, result.get('options', {}))
    unknown = set(options) - supported[kind]
    if unknown:
        fail(
            'PLOT_OPTIONS',
            'Unsupported options are never ignored.',
            kind=kind,
            fields=sorted(unknown),
            allowed=sorted(supported[kind]),
        )
    result['options'] = {**json_object(defaults[kind]), **options}
    _policies(result)
    _axes(result)
    _columns(result)
    return cast(PlotSpec, result)
