"""Inspectable evidence objects whose mutation invalidates publication."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

import pandas as pd
from matplotlib.figure import Figure

from ._data import data_digest, frame_from_payload, frame_payload
from ._errors import AstetikError
from ._json import json_digest, json_object
from ._manifest_types import ManifestDocument
from ._result_atomic import publish_new as _publish_new
from ._result_environment import environment as _environment
from ._result_export import Bundle, publish
from ._result_graphics import settle_layout, svg
from ._result_state import artist_digest, semantic_identity
from ._result_types import VerificationReport
from ._result_verification import verify_figure
from ._spec_types import PlotSpec
from ._types import JsonObject

__all__ = ['EvidenceResult', 'environment_fingerprint']


def environment_fingerprint() -> JsonObject:
    return _environment()


@dataclass(eq=False, repr=False, kw_only=True)
class EvidenceResult:
    """A scientific result whose publication contract rejects later mutation."""

    figure: Figure
    table: pd.DataFrame
    receipt: JsonObject
    marks: dict[str, JsonObject]
    data: pd.DataFrame
    spec: PlotSpec
    manifest: ManifestDocument
    _state: str = field(init=False)
    _figure_signature: str = field(init=False)
    _artist_signature: str = field(init=False)

    def __post_init__(self) -> None:
        self.table = frame_from_payload(frame_payload(self.table))
        self.data = frame_from_payload(frame_payload(self.data))
        self.receipt = json_object(self.receipt)
        self.marks = cast(dict[str, JsonObject], json_object(self.marks))
        self.spec = cast(PlotSpec, json_object(self.spec))
        self.manifest = cast(ManifestDocument, json_object(self.manifest))
        self.receipt.update(input_sha256=data_digest(self.data), table_sha256=data_digest(self.table),
                            spec_sha256=json_digest(self.spec), manifest_sha256=json_digest(self.manifest),
                            marks_sha256=json_digest(self.marks))
        self.receipt['table'] = {'sha256': self.receipt['table_sha256'], 'rows': len(self.table),
                                 'columns': [str(name) for name in self.table.columns]}
        self.receipt['environment'] = _environment()
        self.receipt['result_id'] = semantic_identity(self.receipt)
        settle_layout(self.figure)
        self._state = self._state_digest()
        self._figure_signature = hashlib.sha256(self._svg()).hexdigest()
        self._artist_signature = self._artist_digest()

    @property
    def result_id(self) -> str:
        return cast(str, self.receipt['result_id'])

    def svg_bytes(self) -> bytes:
        return svg(self.figure)

    def _svg(self) -> bytes:
        return self.svg_bytes()

    def _state_digest(self) -> str:
        return json_digest({'data': data_digest(self.data), 'table': data_digest(self.table),
                            'receipt': self.receipt, 'marks': self.marks, 'spec': self.spec, 'manifest': self.manifest})

    def _artist_digest(self) -> str:
        return artist_digest(self.figure)

    def _unchanged(self) -> None:
        try:
            state, figure = self._state_digest(), hashlib.sha256(self._svg()).hexdigest()
        except AstetikError as error:
            raise AstetikError('RESULT_CHANGED', 'The evidence object changed; recreate the result.',
                               {'cause': error.code}) from error
        except Exception as error:
            raise AstetikError('RESULT_CHANGED', 'The figure can no longer be rendered; recreate the result.') from error
        if state != self._state or figure != self._figure_signature or self._artist_digest() != self._artist_signature:
            raise AstetikError('RESULT_CHANGED', 'Data, methods, design or figure changed; recreate the result before publication.')

    def inspect(self, mark_id: str) -> JsonObject:
        self._unchanged()
        if mark_id not in self.marks:
            raise AstetikError('UNKNOWN_MARK', 'Use a mark identifier from result.marks.',
                               {'mark_id': mark_id, 'available': list(self.marks)})
        return json_object(self.marks[mark_id])

    def diff(self, other: object) -> dict[str, JsonObject]:
        if not isinstance(other, EvidenceResult):
            raise AstetikError('INVALID_RESULT', 'Compare two EvidenceResult objects.')
        self._unchanged()
        other._unchanged()
        groups: dict[str, tuple[object, object]] = {
            'inputs': (self.receipt['input_sha256'], other.receipt['input_sha256']),
            'methods': (self.receipt.get('methods', self.receipt.get('analysis', {})),
                        other.receipt.get('methods', other.receipt.get('analysis', {}))),
            'values': (frame_payload(self.table), frame_payload(other.table)),
            'design': ({'spec': self.spec, 'manifest': self.manifest}, {'spec': other.spec, 'manifest': other.manifest}),
        }
        return {name: json_object({'changed': json_digest(left) != json_digest(right), 'before': left, 'after': right})
                for name, (left, right) in groups.items()}

    def verify(self) -> VerificationReport:
        """Check this rendered artifact, not the universal truth of its claims."""
        self._unchanged()
        return verify_figure(self.figure, self.manifest, self.receipt)

    def write(self, directory: str | Path) -> Path:
        """Publish verified graphics, tables and replay inputs atomically, once."""
        report = self.verify()
        if not report['passed']:
            raise AstetikError('VERIFICATION_FAILED', 'The final figure violates its publication contract.',
                               {'checks': [check for check in report['checks'] if not check['passed']]})
        bundle = Bundle(figure=self.figure, data=self.data, table=self.table, spec=self.spec,
                        manifest=self.manifest, marks=self.marks, receipt=self.receipt,
                        svg=self._svg, unchanged=self._unchanged)
        return publish(bundle, Path(directory).expanduser().absolute(), report, _publish_new)
