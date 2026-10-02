"""Versioned machine-readable plot selection and recovery grammar."""

from __future__ import annotations

from ._renderers import DEFAULT_OPTIONS as _DEFAULT_OPTIONS
from ._renderers import KINDS as _KINDS
from ._renderers import SUPPORTED_OPTIONS as _SUPPORTED_OPTIONS
from ._spec import FIELDS, fail
from ._spec_json import json_object
from ._types import JsonObject

KINDS = (*_KINDS, 'animate', 'table', 'text')
DEFAULT_OPTIONS: dict[str, JsonObject] = {
    **_DEFAULT_OPTIONS,
    'animate': {'frame': 0, 'plot_type': 'bar'},
    'table': {'digits': 4},
    'text': {'digits': 4},
}
SUPPORTED_OPTIONS: dict[str, set[str]] = {
    **_SUPPORTED_OPTIONS,
    'animate': {'frame', 'plot_type'},
    'table': {'digits'},
    'text': {'digits'},
}
INTENTS = {
    'distribution': 'hist',
    'comparison': 'comparison',
    'association': 'association',
    'longitudinal': 'longitudinal',
    'frequency': 'count',
    'correlation': 'corr',
    'geography': 'world',
}


def catalog() -> JsonObject:
    """Machine-readable selection, numerical defaults, and recovery grammar."""
    return json_object(
        {
            'schema_version': '1.0',
            'intents': dict(INTENTS),
            'spec_fields': sorted(FIELDS),
            'plots': {
                kind: {
                    'paper': True,
                    'options': sorted(SUPPORTED_OPTIONS[kind]),
                    'defaults': DEFAULT_OPTIONS[kind],
                }
                for kind in KINDS
            },
        }
    )


def select(intent: str) -> JsonObject:
    """Select a representation from declared intent; never infer a method."""
    if intent not in INTENTS:
        fail('INTENT', 'Declare a supported scientific intent.', allowed=list(INTENTS))
    kind = INTENTS[intent]
    return json_object(
        {
            'kind': kind,
            'scientific_method_required': kind in {'comparison', 'association', 'longitudinal'},
            'defaults': DEFAULT_OPTIONS[kind],
            'options': sorted(SUPPORTED_OPTIONS[kind]),
        }
    )
