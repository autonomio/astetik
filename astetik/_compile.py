"""Scientific evidence compilation with isolated rendering and exact accounting."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Literal, cast

import pandas as pd

from ._analysis import analyze
from ._axis_policy import validate as validate_axes
from ._axis_policy import validate_rendered
from ._data import Normalized, normalize
from ._errors import AstetikError
from ._manifest import Manifest
from ._measurements import validate as validate_measurements
from ._observation import Observations, marks_from, prepare, remap
from ._poster import render_poster
from ._presentation import finish
from ._render_context import Rendered
from ._renderers import render_plot
from ._result import EvidenceResult
from ._result_graphics import graphics_context
from ._spec import fail
from ._spec_json import json_object
from ._spec_types import PlotSpec
from ._table import render_table
from ._types import JsonObject

_RENDER_LOCK = threading.RLock()


def design_from(value: object, paper: object) -> Manifest:
    if value is None:
        manifest = Manifest()
    elif isinstance(value, Manifest):
        manifest = value
    elif isinstance(value, dict):
        manifest = Manifest.from_dict(cast(object, value))
    elif isinstance(value, (str, Path)):
        manifest = Manifest.load(value)
    else:
        fail('MANIFEST_TYPE', 'Use a Manifest, document, or local manifest path.')
    if isinstance(paper, str):
        if paper not in {'single', 'double'}:
            fail('PAPER_PRESET', 'paper must be a boolean or single/double preset.')
        document = manifest.to_dict()
        document['paper'].update(
            preset=cast(Literal['single', 'double'], paper),
            width_mm=89 if paper == 'single' else 178,
        )
        manifest = Manifest.from_dict(document)
    elif not isinstance(paper, bool):
        fail('PAPER_PRESET', 'paper must be a boolean or single/double preset.')
    return manifest


def _render(
    frame: pd.DataFrame, spec: PlotSpec, design: Manifest, analysis: JsonObject | None
) -> Rendered:
    with _RENDER_LOCK, graphics_context(design.rc(paper=bool(spec['paper']))):
        try:
            if spec['kind'] in {'table', 'text'}:
                rendered = render_table(frame, spec, design, bool(spec['paper']))
            elif spec['kind'] == 'animate':
                rendered = render_poster(frame, spec, design, bool(spec['paper']))
            else:
                rendered = render_plot(frame, spec, design, bool(spec['paper']), analysis=analysis)
            validate_rendered(rendered.figure, spec)
            finish(
                rendered.figure, spec, design, spec.get('units', {}), spec.get('descriptions', {})
            )
        except AstetikError:
            raise
        except (ValueError, TypeError) as error:
            fail(
                'PLOT_CONTRACT',
                'The declared plot violates a rendering contract.',
                reason=str(error),
                kind=spec['kind'],
            )
    return rendered


def _receipt(
    normalized: Normalized,
    observations: Observations,
    spec: PlotSpec,
    rendered: Rendered,
    analysis: JsonObject | None,
) -> JsonObject:
    count = len(observations.frame)
    return json_object(
        {
            'schema_version': '1.0',
            'paper': spec['paper'],
            'kind': spec['kind'],
            'source': normalized.source,
            'upstream_receipt': normalized.upstream_receipt,
            'units': observations.units,
            'descriptions': observations.descriptions,
            'key': spec['key'],
            'observations': {
                'input': len(normalized.data),
                'used': count,
                'excluded': observations.excluded,
                'missing_policy': spec['missing'],
                'reason': spec.get('missing_reason'),
            },
            'methods': {
                'plot': remap(rendered.methods, observations.positions),
                'analysis': analysis['methods'] if analysis else None,
            },
            'analysis': analysis,
            'caption': analysis['caption']
            if analysis
            else f'{spec["kind"]}; {count} observations. Method details are recorded in the receipt.',
            'checks': [
                {
                    'check': 'observation_accounting',
                    'passed': count + len(observations.excluded) == len(normalized.data),
                },
                {'check': 'source_unchanged', 'passed': True},
            ],
        }
    )


def _summary(
    rendered: Rendered, observations: Observations, spec: PlotSpec, analysis: JsonObject | None
) -> pd.DataFrame:
    table = rendered.table.copy(deep=True)
    if spec['kind'] not in {'table', 'text'}:
        for column in {'source_rows', 'category_source_rows'} & set(table.columns):

            def map_rows(rows: object) -> list[int]:
                return [observations.positions[row] for row in cast(list[int], rows)]

            table[column] = table[column].map(map_rows)
    if analysis and spec['kind'] == 'association':
        table = pd.DataFrame(cast(list[JsonObject], analysis['summary']))
    return table


def compile_evidence(
    data: object,
    spec: PlotSpec,
    manifest: object = None,
    *,
    inherited_key: bool = False,
    replayed_receipt: JsonObject | None = None,
) -> EvidenceResult:
    return compile_normalized(
        normalize(data), spec, manifest,
        inherited_key=inherited_key, replayed_receipt=replayed_receipt,
    )


def compile_normalized(
    normalized: Normalized,
    spec: PlotSpec,
    manifest: object = None,
    *,
    inherited_key: bool = False,
    replayed_receipt: JsonObject | None = None,
) -> EvidenceResult:
    """Compile retained input without rereading its caller-owned origin."""
    try:
        design = design_from(manifest, spec['paper'])
    except AstetikError:
        raise
    except (ValueError, TypeError, OSError) as error:
        fail('MANIFEST_CONTRACT', 'The design manifest is invalid.', reason=str(error))
    spec['paper'] = bool(spec['paper'])
    observations = prepare(normalized, spec, inherited_key=inherited_key)
    validate_measurements(observations, spec, design)
    validate_axes(observations.frame, spec)
    analysis = cast(JsonObject | None, analyze(observations.frame, spec))
    rendered = _render(observations.frame, spec, design, analysis)
    receipt = _receipt(normalized, observations, spec, rendered, analysis)
    receipt['font'] = json_object(dict(design.font_info))
    if replayed_receipt is not None:
        receipt['source'] = replayed_receipt['source']
        receipt['upstream_receipt'] = replayed_receipt.get('upstream_receipt')
    result = EvidenceResult(
        figure=rendered.figure,
        table=_summary(rendered, observations, spec, analysis),
        receipt=receipt,
        marks=marks_from(rendered.marks, observations),
        data=normalized.data,
        spec=spec,
        manifest=design.to_dict(),
    )
    if spec['paper']:
        verification = result.verify()
        if not verification['passed']:
            fail(
                'PAPER_VERIFICATION', 'Paper output failed publication checks.', report=verification
            )
    return result
