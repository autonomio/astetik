"""JSON group identities separate booleans and strings from equivalent numbers."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Literal, TypeAlias, cast

import numpy as np
from numpy.typing import NDArray

from ._spec import fail
from ._types import JsonScalar

GroupIdentity: TypeAlias = tuple[Literal['null', 'boolean', 'number', 'string'], JsonScalar]


def identity(value: object) -> GroupIdentity:
    if isinstance(value, np.generic):
        value = cast(object, value.item())
    if value is None:
        return 'null', None
    if isinstance(value, bool):
        return 'boolean', value
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            fail('GROUPS_MISMATCH', 'Group identities must be finite JSON scalars.')
        return 'number', value
    if isinstance(value, str):
        return 'string', value
    fail('GROUPS_MISMATCH', 'Group identities must be finite JSON scalars.')


def observed(values: Iterable[object]) -> dict[GroupIdentity, JsonScalar]:
    result: dict[GroupIdentity, JsonScalar] = {}
    for value in values:
        key = identity(value)
        result.setdefault(key, key[1])
    return result


def matching(values: Iterable[object], label: JsonScalar) -> NDArray[np.bool_]:
    key = identity(label)
    return np.fromiter((identity(value) == key for value in values), dtype=np.bool_)


def validate_order(values: Iterable[object], order: list[JsonScalar]) -> None:
    keys = [identity(value) for value in order]
    if len(keys) != len(set(keys)) or set(keys) != set(observed(values)):
        raise ValueError('order must include every observed group identity exactly once.')
