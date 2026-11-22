"""Pytest configuration for the package suite.

Emits a runtime profile when `TEST_RUNTIME_PROFILE` names a path, so
`governance/check_test_runtime.py` has something to check the suite against.
Writing it is opt-in: a local run should not litter the tree, and CI sets the
variable explicitly.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from importlib.resources import as_file, files

import pandas as pd
import pytest
import shapefile

_STARTED: dict[str, float] = {}
_RECORDS: list[dict[str, str | float]] = []
_SUITE_START: float | None = None


def pytest_sessionstart(session: object) -> None:
    """Record when the suite began."""
    global _SUITE_START
    _SUITE_START = time.perf_counter()


def pytest_runtest_logstart(nodeid: str, location: object) -> None:
    """Record when one test began."""
    _STARTED[nodeid] = time.perf_counter()


def pytest_runtest_logfinish(nodeid: str, location: object) -> None:
    """Record how long one test took."""
    started = _STARTED.pop(nodeid, None)
    if started is not None:
        _RECORDS.append({'name': nodeid, 'duration': time.perf_counter() - started})


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    """Write the runtime profile when a destination is configured."""
    destination = os.environ.get('TEST_RUNTIME_PROFILE')
    if not destination or _SUITE_START is None:
        return
    path = pathlib.Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                'total_seconds': time.perf_counter() - _SUITE_START,
                'tests': sorted(_RECORDS, key=lambda row: -float(row['duration'])),
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )


@pytest.fixture(scope='session')
def country_estimates() -> pd.DataFrame:
    """Natural Earth estimates shipped with the package; sentinel rows are excluded."""
    with as_file(files('astetik').joinpath('extras', 'countries.dbf')) as source:
        records = shapefile.Reader(str(source.with_suffix(''))).records()
    frame = pd.DataFrame([record.as_dict() for record in records])
    kept = frame[(frame['POP_EST'] > 0) & (frame['GDP_MD_EST'] > 0)]
    income = kept['INCOME_GRP'].str.replace(r'^\d\. ', '', regex=True)
    return pd.DataFrame(
        {
            'iso3': kept['ADM0_A3'],
            'income': income,
            'tier': income.str.startswith('High').map({True: 'High income', False: 'Other'}),
            'population': kept['POP_EST'],
            'output': kept['GDP_MD_EST'] * 1e6,
            'wealth': kept['GDP_MD_EST'] * 1e6 / kept['POP_EST'],
            'size_class': kept['POP_RANK'].clip(lower=8, upper=17).astype(float),
        }
    ).reset_index(drop=True)
