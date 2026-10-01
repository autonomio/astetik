"""Canonical finite JSON for scientific specifications and evidence hashes."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import cast

import numpy as np

from ._errors import AstetikError
from ._numpy_types import NumpyScalar
from ._types import JsonObject, JsonValue


def _scalar(item: object) -> object:
    if isinstance(item, np.generic):
        return cast(Callable[[NumpyScalar], object], getattr(np.generic, 'item'))(cast(NumpyScalar, item))
    raise TypeError(f'Unsupported JSON value: {type(item).__name__}')


def canonical_json(value: object) -> str:
    """Serialize finite JSON without user-provided encoders or callbacks."""
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':'), default=_scalar)
    except (TypeError, ValueError) as error:
        raise AstetikError('INVALID_JSON', 'Evidence must contain finite JSON values.', {'reason': str(error)}) from error


def json_digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def json_value(value: object) -> JsonValue:
    """The parser returns only the recursive JSON domain validated above."""
    return cast(JsonValue, json.loads(canonical_json(value)))


def json_object(value: object) -> JsonObject:
    parsed = json_value(value)
    if not isinstance(parsed, dict):
        raise AstetikError('INVALID_JSON', 'Evidence must be a JSON object.')
    return parsed


def clone_json(value: object) -> JsonValue:
    """Return isolated finite JSON after validating the complete boundary."""
    return json_value(value)
