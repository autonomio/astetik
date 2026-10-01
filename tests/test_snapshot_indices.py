"""Exact index evidence uses only rows from retained country/area metadata."""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from matplotlib import pyplot as plt

import astetik as ast
from astetik._data import data_digest, frame_from_payload, frame_payload
from astetik._errors import AstetikError


def _country_rows() -> pd.DataFrame:
    source = pd.read_csv(Path(__file__).resolve().parents[1] / "astetik" / "extras" / "countries.csv")
    frame = source.loc[source["region"].eq("Europe")].iloc[:3].copy()
    categories = pd.Index(source["region"].dropna().unique(), dtype="string", name="category_identity")
    regions = pd.CategoricalIndex(["Europe", "Africa"], categories=categories, ordered=True)
    area_names = frame["alpha-3"].tolist() + source.loc[source["region"].eq("Asia"), "alpha-3"].iloc[:1].tolist()
    identities = pd.Index(area_names, dtype="string")
    frame.index = pd.MultiIndex(
        levels=[regions, identities], codes=[[0, 0, 0], [0, 1, 2]],
        names=[("geography", "region"), "area_identity"], sortorder=2,
    )
    return frame


def _assert_index(actual: pd.Index, expected: pd.MultiIndex) -> None:
    assert isinstance(actual, pd.MultiIndex)
    pd.testing.assert_index_equal(actual, expected, exact=True)
    assert actual.sortorder == expected.sortorder
    for restored, original in zip(actual.levels, expected.levels):
        pd.testing.assert_index_equal(restored, original, exact=True)
    for restored, original in zip(actual.codes, expected.codes):
        np.testing.assert_array_equal(restored, original)
    assert isinstance(actual.levels[0], pd.CategoricalIndex)
    assert actual.levels[0].ordered
    pd.testing.assert_index_equal(actual.levels[0].categories, expected.levels[0].categories, exact=True)


@pytest.mark.parametrize("empty", [False, True])
def test_country_categorical_multiindex_retains_unused_levels_categories_and_codes(empty: bool) -> None:
    data = _country_rows()
    if empty:
        data = data.iloc[:0]
    payload = frame_payload(data)
    restored = frame_from_payload(payload)
    pd.testing.assert_frame_equal(restored, data)
    _assert_index(restored.index, data.index)
    assert frame_payload(restored) == payload
    assert data_digest(restored) == data_digest(data)
    assert len(restored.index.levels[0]) == 2
    assert len(restored.index.levels[0].categories) == 5
    assert len(restored.index.levels[1]) == 4
    assert restored.index.levels[1].dtype == pd.StringDtype()


def test_multiindex_metadata_changes_identity_without_changing_country_rows() -> None:
    data = _country_rows()
    changed = data.copy()
    changed.index = data.index.remove_unused_levels()
    assert changed.index.tolist() == data.index.tolist()
    assert data_digest(changed) != data_digest(data)
    changed.index = data.index.set_levels(data.index.levels[0].reorder_categories(data.index.levels[0].categories[::-1]), level=0)
    assert changed.index.tolist() == data.index.tolist()
    assert data_digest(changed) != data_digest(data)


def test_categorical_multiindex_country_input_writes_and_strictly_replays(tmp_path: Path) -> None:
    data = _country_rows()
    result = ast.render(data, {"kind": "count", "x": "region", "key": ["alpha-3"], "paper": "single"})
    with ExitStack() as cleanup:
        cleanup.callback(plt.close, result.figure)
        _assert_index(result.data.index, data.index)
        assert result.receipt["observations"]["used"] == 3
        mark = next(iter(result.marks.values()))
        assert mark["source_rows"] == [0, 1, 2]
        assert mark["source_keys"] == [{"alpha-3": code} for code in data["alpha-3"]]
        bundle = result.write(tmp_path / "indexed-country-evidence")
        replayed = ast.replay(bundle, strict_environment=True)
        cleanup.callback(plt.close, replayed.figure)
        _assert_index(replayed.data.index, data.index)
        pd.testing.assert_frame_equal(replayed.data, data)
        assert replayed.result_id == result.result_id
        assert replayed.marks == result.marks
        assert replayed.verify()["passed"]


@pytest.mark.parametrize("field", ["levels", "codes", "sortorder"])
def test_multiindex_inference_cannot_replace_missing_retained_metadata(field: str) -> None:
    payload = frame_payload(_country_rows())
    payload["index"].pop(field)
    with pytest.raises(AstetikError) as rejected:
        frame_from_payload(payload)
    assert rejected.value.code == "INVALID_SNAPSHOT"


@pytest.mark.parametrize("codes", [[[0, 0, 0]], [[0, 0, 0], [0, 1, 4]], [[0, 0, 0], [0, 1, -2]], [[0, 0, 0], [0, 1, True]]])
def test_multiindex_malformed_codes_fail_instead_of_losing_row_identity(codes: list[list[int]]) -> None:
    payload = frame_payload(_country_rows())
    payload["index"]["codes"] = codes
    with pytest.raises(AstetikError) as rejected:
        frame_from_payload(payload)
    assert rejected.value.code == "INVALID_SNAPSHOT"


def test_categorical_multiindex_column_labels_retain_schema() -> None:
    data = _country_rows()
    data = data[["name", "alpha-3", "country-code"]]
    labels = pd.Index(data.columns, dtype="string")
    unused = pd.Index(["region"], dtype="string")
    data.columns = pd.MultiIndex(
        levels=[pd.CategoricalIndex(["geography"], categories=["geography", "classification"], ordered=True), labels.append(unused)],
        codes=[[0, 0, 0], [0, 1, 2]], names=["domain", "variable"], sortorder=2,
    )
    restored = frame_from_payload(frame_payload(data))
    pd.testing.assert_frame_equal(restored, data)
    _assert_index(restored.columns, data.columns)


@pytest.mark.parametrize("empty", [False, True])
def test_plain_multiindex_preserves_real_missing_region_and_unobserved_levels(empty: bool) -> None:
    data = pd.read_csv(Path(__file__).resolve().parents[1] / "astetik" / "extras" / "countries.csv")
    data.index = pd.MultiIndex.from_frame(data[["region", "alpha-3"]])
    assert -1 in data.index.codes[0]  # The actual Antarctica record lacks a region.
    if empty:
        data = data.iloc[:0]
    restored = frame_from_payload(frame_payload(data))
    pd.testing.assert_frame_equal(restored, data)
    for actual, expected in zip(restored.index.levels, data.index.levels):
        pd.testing.assert_index_equal(actual, expected, exact=True)
    for actual, expected in zip(restored.index.codes, data.index.codes):
        np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("kind", ["original", "range", "nullable"])
def test_ordinary_country_indices_keep_names_and_dtype(kind: str) -> None:
    data = _country_rows().reset_index(drop=True)
    if kind == "original":
        data.index = pd.Index(data["alpha-3"], name="area_identity")
    elif kind == "range":
        data.index = pd.RangeIndex(0, 3, name="position")
    else:
        data.index = pd.Index(data["country-code"], dtype="UInt16", name="numeric_identity")
    pd.testing.assert_frame_equal(frame_from_payload(frame_payload(data)), data)


def test_numeric_categorical_levels_retain_nullable_unsigned_category_dtype() -> None:
    data = _country_rows()
    source = pd.read_csv(Path(__file__).resolve().parents[1] / "astetik" / "extras" / "countries.csv")
    categories = pd.Index(source["country-code"].unique(), dtype="UInt16", name="numeric_categories")
    numeric_identity = pd.CategoricalIndex(data["country-code"], categories=categories, ordered=True)
    data.index = pd.MultiIndex.from_arrays([numeric_identity, data["region"]], names=["numeric_identity", "region_identity"])
    restored = frame_from_payload(frame_payload(data))
    pd.testing.assert_frame_equal(restored, data)
    _assert_index(restored.index, data.index)
    assert restored.index.levels[0].categories.dtype == pd.UInt16Dtype()
