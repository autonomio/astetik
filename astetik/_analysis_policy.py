"""Resolve explicit research protocol declarations without choosing inference."""
from __future__ import annotations

from collections.abc import Mapping
from typing import NoReturn, cast

from ._analysis_types import AnalysisMethods, Method, ProtocolPlan
from ._errors import AstetikError
from ._spec_types import PlotSpec
from ._types import JsonScalar


def fail(code: str, message: str, **details: object) -> NoReturn:
    raise AstetikError(code, message, details)


def _plan(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        fail('ANALYSIS_SCHEMA', 'analysis must be an object.')
    plan = cast(dict[str, object], value)
    unknown = set(plan) - {'method', 'confidence', 'groups', 'observation_unit', 'subject'}
    if unknown:
        fail('ANALYSIS_SCHEMA', 'Unknown analysis fields.', fields=sorted(unknown))
    return plan


def _used_fields(kind: str, method: Method, plan: Mapping[str, object]) -> None:
    used = {'method', 'observation_unit'}
    if kind == 'comparison':
        used.update({'confidence', 'groups'})
        if method == 'paired_t':
            used.add('subject')
    elif method == 'pearson':
        used.add('confidence')
    unknown = set(plan) - used
    if unknown:
        fail('ANALYSIS_FIELDS', 'The declared method does not use these fields.', fields=sorted(unknown))


def _groups(value: object) -> tuple[JsonScalar, JsonScalar]:
    if not isinstance(value, list):
        fail('GROUPS_REQUIRED', 'Declare two ordered groups; the contrast is second minus first.')
    groups = cast(list[object], value)
    if len(groups) != 2 or groups[0] == groups[1]:
        fail('GROUPS_REQUIRED', 'Declare two ordered groups; the contrast is second minus first.')
    if any(item is not None and not isinstance(item, (str, int, float, bool)) for item in groups):
        fail('GROUPS_REQUIRED', 'Declare native scalar group identities.')
    return cast(JsonScalar, groups[0]), cast(JsonScalar, groups[1])


def _confidence(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < 1:
        fail('CONFIDENCE', 'confidence must be between zero and one.')
    return float(value)


def resolve_plan(spec: PlotSpec) -> ProtocolPlan | None:
    kind = spec['kind']
    if kind not in ('comparison', 'association', 'longitudinal'):
        if spec.get('analysis'):
            fail('ANALYSIS_KIND', 'Use a research protocol kind for statistical inference.')
        return None
    plan = _plan(spec.get('analysis', {}))
    if spec.get('row') or spec.get('col'):
        fail('ANALYSIS_FACETS', 'Run a separate declared protocol for each subgroup; pooled inference is not duplicated across facets.')
    if kind == 'comparison' and spec.get('hue'):
        fail('ANALYSIS_GROUPING', 'comparison uses the declared x groups; an additional hue grouping is unsupported.')
    if kind == 'longitudinal' and (spec['options'].get('sort', True) is not True or spec['options'].get('drawstyle', 'default') != 'default'):
        fail('TRAJECTORY_METHOD', 'The observed protocol connects observations in ascending time with straight segments.')
    method = plan.get('method')
    supported = {'comparison': ['welch', 'paired_t'], 'association': ['pearson', 'spearman'], 'longitudinal': ['observed']}[kind]
    if method not in supported:
        fail('METHOD_REQUIRED', 'Declare the scientific method.', allowed=supported)
    method = cast(Method, method)
    _used_fields(kind, method, plan)
    unit = plan.get('observation_unit')
    if not isinstance(unit, str) or not unit.strip():
        fail('OBSERVATION_UNIT_REQUIRED', 'Declare what one independent observation represents.')
    if not spec.get('key'):
        fail('KEY_REQUIRED', 'Declare observation keys before statistical analysis.')
    confidence = _confidence(plan.get('confidence', .95))
    if not isinstance(spec.get('x'), str) or not isinstance(spec.get('y'), str):
        fail('ANALYSIS_COLUMNS', 'Research protocols need one x and one y column.')
    subject = plan.get('subject')
    return ProtocolPlan(kind, method, unit, float(confidence), _groups(plan.get('groups')) if kind == 'comparison' else None,
                        subject if isinstance(subject, str) else None)


def methods_for(plan: ProtocolPlan) -> AnalysisMethods:
    return {'method': plan.method, 'observation_unit': plan.observation_unit,
            'confidence': plan.confidence if plan.kind == 'comparison' or plan.method == 'pearson' else None,
            'assumptions': ['Observation keys identify retained records; the researcher declares the observation unit.']}
