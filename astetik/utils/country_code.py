"""Typed lookups against Astetik's retained country and area metadata."""
from __future__ import annotations

import csv
from pathlib import Path

from .._errors import AstetikError


def _lookup(field: str, value: str, result: str) -> str:
    source = Path(__file__).resolve().parents[1] / 'extras' / 'countries.csv'
    with source.open(encoding='utf-8', newline='') as stream:
        for record in csv.DictReader(stream):
            if record[field] == value:
                return record[result]
    raise AstetikError('COUNTRY_IDENTITY', 'The identifier is absent from the retained country/area metadata.',
                       {'field': field, 'value': value, 'recovery': 'Use the exact ISO alpha-3 code or retained area name.'})


def code_to_country(code: str) -> str:
    """Resolve an exact alpha-3 identifier or fail on an unknown identity."""
    return _lookup('alpha-3', code, 'name')


def country_to_code(country: str) -> str:
    """Resolve an exact retained country/area name or fail on an unknown identity."""
    return _lookup('name', country, 'alpha-3')

__all__ = ['code_to_country', 'country_to_code']
