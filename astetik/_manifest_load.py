"""Parse design documents with duplicate fields rejected before validation."""
from __future__ import annotations

import json
import tomllib
from collections.abc import Hashable, Mapping
from pathlib import Path
from typing import Protocol, cast

from ._manifest_sections import mapping


def unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate manifest field: {key}')
        result[key] = value
    return result


def nonfinite(value: str) -> object:
    raise ValueError(f'Nonfinite value: {value}')


def yaml_document(text: str) -> object:
    try:
        import yaml
    except ImportError as exc:
        raise ValueError('YAML manifests require PyYAML; use JSON or TOML instead') from exc

    class ConstructObject(Protocol):
        def __call__(self, node: yaml.Node, *, deep: bool = False) -> object: ...

    class UniqueSafeLoader(yaml.SafeLoader):
        """Preserve SafeLoader semantics while rejecting duplicate mapping keys."""

    def construct_mapping(loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False) -> dict[Hashable, object]:
        if not isinstance(node, yaml.MappingNode):
            raise ValueError('A YAML mapping must use a mapping node')
        loader.flatten_mapping(node)
        result: dict[Hashable, object] = {}
        construct = cast(ConstructObject, getattr(loader, 'construct_object'))
        for key_node, value_node in node.value:
            key: object = construct(key_node, deep=deep)
            if not isinstance(key, Hashable):
                raise ValueError('Manifest mapping keys must be hashable')
            if key in result:
                raise ValueError(f'Duplicate manifest field: {key}')
            result[key] = construct(value_node, deep=deep)
        return result

    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return yaml.load(text, Loader=UniqueSafeLoader)


def load_document(source: Path) -> Mapping[str, object]:
    text, suffix = source.read_text(encoding='utf-8'), source.suffix.lower()
    document: object
    if suffix == '.json':
        document = json.loads(text, object_pairs_hook=unique_pairs, parse_constant=nonfinite)
    elif suffix == '.toml':
        document = tomllib.loads(text)
    elif suffix in ('.yaml', '.yml'):
        document = yaml_document(text)
    else:
        raise ValueError('Manifest files must use .json, .toml, .yaml, or .yml')
    result = dict(mapping(document, 'A manifest document'))
    typography = result.get('typography')
    if isinstance(typography, Mapping):
        policy = dict(cast(Mapping[str, object], typography))
        font_path = policy.get('font_path')
        if isinstance(font_path, str) and font_path:
            policy['font_path'] = str((source.parent / font_path).resolve())
        result['typography'] = policy
    return result
