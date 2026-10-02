"""Generate or check the machine-readable catalogue from the public API."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPOSITORY = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    sys.path.insert(0, str(_REPOSITORY))
    import astetik as ast

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed catalogue differs from the API")
    parser.add_argument("--output", type=Path, default=_REPOSITORY / "astetik" / "docs" / "plots.json")
    arguments = parser.parse_args(argv)
    expected = json.dumps(ast.catalog(), sort_keys=True, indent=2, allow_nan=False) + "\n"
    target = arguments.output
    if arguments.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != expected:
            print(f"Catalogue is missing or stale: {target}; run python scripts/build_catalog.py", file=sys.stderr)
            return 1
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
