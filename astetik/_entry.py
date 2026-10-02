"""Shared public compilation entrypoints without convenience import cycles."""

from __future__ import annotations

from typing import cast

from ._catalog import DEFAULT_OPTIONS, KINDS, SUPPORTED_OPTIONS
from ._compile import compile_evidence
from ._result import EvidenceResult
from ._spec import FIELDS, fail, resolve
from ._spec_types import PlotSpec
from ._types import JsonObject


def resolve_spec(spec: object) -> PlotSpec:
    return resolve(spec, KINDS, DEFAULT_OPTIONS, SUPPORTED_OPTIONS)


def compile_entry(
    data: object,
    spec: object,
    manifest: object = None,
    *,
    replayed_receipt: JsonObject | None = None,
) -> EvidenceResult:
    resolved = resolve_spec(spec)
    return compile_evidence(
        data,
        resolved,
        manifest,
        inherited_key='key' not in cast(dict[str, object], spec),
        replayed_receipt=replayed_receipt,
    )


def render(data: object, spec: object, manifest: object = None) -> EvidenceResult:
    """Compile an explicit scientific specification; user text remains data."""
    return compile_entry(data, spec, manifest)


def plot(
    data: object,
    kind: str,
    *,
    x: object = None,
    y: object = None,
    paper: object = False,
    manifest: object = None,
    **fields: object,
) -> EvidenceResult:
    """One common interface for every plot; unfamiliar settings are rejected."""
    options = fields.pop('options', {})
    if not isinstance(options, dict):
        fail('PLOT_OPTIONS', 'options must be an object.')
    options = dict(cast(dict[str, object], options))
    for name in list(fields):
        if name not in FIELDS:
            options[name] = fields.pop(name)
    spec: dict[str, object] = {'kind': kind, 'paper': paper, 'options': options, **fields}
    if x is not None:
        spec['x'] = x
    if y is not None:
        spec['y'] = y
    return render(data, spec, manifest)
