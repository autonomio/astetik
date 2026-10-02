"""Semantic result identity and mutation-sensitive artist evidence."""
from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from numpy.typing import ArrayLike, NDArray

from ._data import frame_payload
from ._json import json_digest, json_object
from ._types import JsonObject, JsonValue


def semantic_identity(receipt: JsonObject) -> str:
    environment = json_object(receipt['environment'])
    font = json_object(receipt.get('font', {}))
    return json_digest({'source': receipt.get('source'), 'input': receipt['input_sha256'], 'table': receipt['table_sha256'],
                        'spec': receipt['spec_sha256'], 'manifest': receipt['manifest_sha256'],
                        'methods': receipt.get('methods', receipt.get('analysis', {})),
                        'upstream': receipt.get('upstream_receipt', receipt.get('upstream')),
                        'marks': receipt['marks_sha256'], 'code_sha256': environment['code_sha256'],
                        'font': {name: font.get(name) for name in ('sha256', 'resolved', 'requested')}})


def _values(array: ArrayLike | None) -> JsonValue:
    if array is None:
        return None
    if np.ma.isMaskedArray(array):
        array = cast(ArrayLike, np.ma.filled(cast(ArrayLike, array), np.nan))
    values: NDArray[np.generic] = np.asarray(array)
    return json_object({'shape': list(values.shape), 'values': frame_payload(pd.DataFrame(values.reshape(-1)))})


def artist_digest(figure: Figure) -> str:
    axes: list[JsonObject] = []
    for axis in figure.axes:
        axes.append(json_object({'xlim': list(axis.get_xlim()), 'ylim': list(axis.get_ylim()),
                                 'lines': [{'x': _values(line.get_xdata()), 'y': _values(line.get_ydata()),
                                            'visible': line.get_visible()} for line in axis.lines],
                                 'collections': [{'offsets': _values(collection.get_offsets()),
                                                  'values': _values(collection.get_array()),
                                                  'visible': collection.get_visible()} for collection in axis.collections]}))
    return json_digest({'dpi': figure.dpi, 'axes': axes})
