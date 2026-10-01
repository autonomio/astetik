"""Strict finite JSON boundaries for agent specifications and retained documents."""

from __future__ import annotations

import json
from typing import cast

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


def read_object(text: str) -> JsonObject:
    """Read a retained finite object without granting its content execution."""
    return json_object(cast(object, json.loads(text)))
