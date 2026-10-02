"JSON agent interface with the same contracts as Python."

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, cast

from ._api import catalog, render, replay
from ._data import canonical_json
from ._errors import AstetikError
from ._spec_json import json_object
from ._types import JsonObject, JsonValue


def _unique(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise AstetikError(
                'DOCUMENT_DUPLICATE', 'Duplicate specification field.', {'field': key}
            )
        result[key] = value
    return result


def _nonfinite(value: str) -> NoReturn:
    raise AstetikError('DOCUMENT_NONFINITE', 'Nonfinite specification value.', {'value': value})


def _document(path: str | Path) -> JsonObject:
    return json_object(
        cast(
            object,
            json.loads(
                Path(path).read_text(encoding='utf-8'),
                object_pairs_hook=_unique,
                parse_constant=_nonfinite,
            ),
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='astetik', description='Compile scientific plots and their evidence receipts.'
    )
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('catalog', help='Print the versioned plot and option catalogue.')
    create = commands.add_parser(
        'render', help='Create a new evidence bundle from local data and JSON specification.'
    )
    create.add_argument('--data', required=True)
    create.add_argument('--spec', required=True)
    create.add_argument('--manifest')
    create.add_argument('--output', required=True)
    repeat = commands.add_parser('replay', help='Verify and recompute a retained bundle.')
    repeat.add_argument('bundle')
    repeat.add_argument('--output')
    repeat.add_argument(
        '--allow-environment-change',
        action='store_true',
        help='Explicit recomputation; numerical evidence must still match.',
    )
    args = parser.parse_args(argv)
    try:
        if args.command == 'catalog':
            print(canonical_json(catalog()))
            return 0
        result = (
            render(args.data, _document(args.spec), args.manifest)
            if args.command == 'render'
            else replay(args.bundle, strict_environment=not args.allow_environment_change)
        )
        output = result.write(args.output) if args.output else None
        print(
            canonical_json(
                {
                    'result_id': result.result_id,
                    'output': str(output) if output else None,
                    'receipt': result.receipt,
                    'verification': result.verify(),
                }
            )
        )
        return 0
    except AstetikError as error:
        print(canonical_json(error.to_dict()), file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(
            canonical_json({'code': 'DOCUMENT_ERROR', 'message': str(error), 'details': {}}),
            file=sys.stderr,
        )
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
