"""Freeze validated complete mapping domains without changing their wire shapes."""
from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import TypeVar, cast

_Policy = TypeVar('_Policy', bound=Mapping[str, object])


def freeze_mapping(policy: _Policy) -> _Policy:
    return cast(_Policy, MappingProxyType(policy))
