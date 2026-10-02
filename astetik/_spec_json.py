"""Strict finite JSON boundaries for agent specifications and retained documents."""

from __future__ import annotations

import json
from typing import NoReturn, cast

from ._types import JsonObject, JsonValue


def clone_json(value: object) -> JsonValue:
    """Validate JSON serialization and retain a detached finite document."""
    return cast(JsonValue, json.loads(json.dumps(value, allow_nan=False)))


def json_object(value: object) -> JsonObject:
    """Reject non-object documents after checking the complete JSON boundary."""
    result = clone_json(value)
    if not isinstance(result, dict):
        raise ValueError('The document must be a JSON object.')
    return result


def _unique_fields(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON field {key!r}.')
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f'Nonfinite JSON constant {value!r} is not permitted.')


def read_object(text: str) -> JsonObject:
    """Read a retained finite object without granting its content execution."""
    parsed = json.loads(text, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
    return json_object(cast(object, parsed))
