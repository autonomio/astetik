"""Verify retained Wrangle preparation evidence without importing Wrangle."""
from __future__ import annotations

import json
from types import SimpleNamespace

from ._data_types import InputFrame, SourceOrigin
from ._errors import AstetikError
from ._json import json_digest, json_object
from ._polars import from_polars, is_polars_frame, polars_digest
from ._snapshot_parse import object_mapping


def prepared_input(value: object) -> InputFrame | None:
    if not (type(value) is SimpleNamespace or
            (type(value).__name__ == 'Prepared' and type(value).__module__.startswith('wrangle.'))):
        return None
    fields = object_mapping(object.__getattribute__(value, '__dict__'))
    if not {'data', 'receipt', '_data_digest', '_receipt_digest'} <= set(fields):
        return None
    table, receipt = fields['data'], fields['receipt']
    if not is_polars_frame(table) or not isinstance(receipt, dict):
        raise AstetikError('INVALID_PREPARED', 'Prepared inputs require a Polars table and JSON receipt.')
    try:
        # This is Wrangle's exact receipt algorithm, with no custom serializer.
        encoded = json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    except (TypeError, ValueError) as error:
        raise AstetikError('PREPARED_CHANGED', 'The preparation receipt is no longer valid JSON.') from error
    upstream = json_object(json.loads(encoded))
    data = table.clone()
    actual = polars_digest(data)
    output = upstream.get('output')
    if (actual != fields['_data_digest'] or json_digest(upstream) != fields['_receipt_digest'] or
            not isinstance(output, dict) or output.get('sha256') != actual):
        raise AstetikError('PREPARED_CHANGED', 'Prepared data or receipt changed; prepare again.')
    origin: SourceOrigin = {'kind': 'wrangle.Prepared', 'upstream_sha256': actual,
                            'receipt_sha256': json_digest(upstream),
                            'native_schema': {name: str(dtype) for name, dtype in data.schema.items()}}
    variables = object_mapping(upstream.get('variables', {}))
    descriptions = {name: info['description'] for name, item in variables.items()
                    if (info := object_mapping(item)).get('description') is not None}
    return InputFrame(from_polars(data), origin, upstream, upstream.get('key', []),
                      upstream.get('units', {}), descriptions)
