#!/bin/sh
set -eu
python -m pytest
python scripts/build_catalog.py --check
python -m build
