"""Legacy migration never transforms observations or changes global styling.

Datetime values below are unit fixtures, not empirical research observations.
"""
from __future__ import annotations

import warnings
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import matplotlib
import pandas as pd
import pytest
from matplotlib.dates import DateFormatter, MonthLocator
from matplotlib.figure import Figure

from astetik._errors import AstetikError
from astetik.style.random_colors import randomcolor
from astetik.style.style import params, styles
from astetik.utils.country_code import code_to_country, country_to_code
from astetik.utils.datetime import _generate_datetime, date_handler
from astetik.utils.load_data import read
from astetik.utils.outliers import outliers
from astetik.utils.transform import equal_samples, groupby_func


@pytest.mark.parametrize("operation", [outliers, equal_samples, groupby_func, params, styles, randomcolor, read, _generate_datetime])
def test_unsafe_legacy_calls_fail_before_data_or_global_state_changes(operation: Callable[..., NoReturn]) -> None:
    data = pd.read_csv(Path(__file__).resolve().parents[1] / "astetik" / "extras" / "countries.csv")
    original = data.copy(deep=True)
    settings = dict(matplotlib.rcParams)
    filters = warnings.filters.copy()
    with pytest.raises(AstetikError) as rejected:
        operation(data)
    assert rejected.value.code == "LEGACY_API"
    assert isinstance(rejected.value.details["recovery"], str)
    assert rejected.value.details["recovery"]
    assert operation.__module__ in str(rejected.value)
    pd.testing.assert_frame_equal(data, original)
    assert dict(matplotlib.rcParams) == settings
    assert warnings.filters == filters


def test_country_lookup_preserves_exact_shipped_identity_and_rejects_unknown() -> None:
    assert code_to_country("FIN") == "Finland"
    assert country_to_code("Finland") == "FIN"
    with pytest.raises(AstetikError) as rejected:
        code_to_country("ZZZ")
    assert rejected.value.code == "COUNTRY_IDENTITY"
    assert rejected.value.details["value"] == "ZZZ"


def test_observed_datetime_formatter_changes_only_the_supplied_axis() -> None:
    figure = Figure()
    axis = figure.add_subplot(121)
    untouched = figure.add_subplot(122)
    locator = untouched.xaxis.get_major_locator()
    formatter = untouched.xaxis.get_major_formatter()
    timestamps = pd.date_range("2026-01-01", periods=2)
    date_handler(timestamps, axis, "month")
    assert isinstance(axis.xaxis.get_major_locator(), MonthLocator)
    assert isinstance(axis.xaxis.get_major_formatter(), DateFormatter)
    assert axis.xaxis.get_major_formatter().fmt == "%Y-%m"
    assert untouched.xaxis.get_major_locator() is locator
    assert untouched.xaxis.get_major_formatter() is formatter
