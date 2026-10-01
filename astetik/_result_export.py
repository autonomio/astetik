"""Unique staging of complete evidence bundles before atomic publication."""
from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pandas as pd
from matplotlib.figure import Figure

from ._data import file_digest, frame_payload
from ._errors import AstetikError
from ._json import canonical_json, json_digest, json_object
from ._manifest_types import ManifestDocument
from ._result_font import retain_font
from ._result_graphics import graphics
from ._result_types import VerificationReport
from ._result_verification import object_mapping
from ._spec_types import PlotSpec
from ._types import JsonObject


@dataclass(frozen=True, kw_only=True)
class Bundle:
    """Retained inputs and exact figure serializers for one sealed result."""

    figure: Figure
    table: pd.DataFrame
    data: pd.DataFrame
    spec: PlotSpec
    manifest: ManifestDocument
    marks: dict[str, JsonObject]
    receipt: JsonObject
    svg: Callable[[], bytes]
    unchanged: Callable[[], None]


def _stage(bundle: Bundle, directory: Path, report: VerificationReport) -> None:
    files: dict[str, object] = {'input.json': frame_payload(bundle.data), 'summary.json': frame_payload(bundle.table),
                                'spec.json': bundle.spec, 'manifest.json': bundle.manifest, 'marks.json': bundle.marks}
    for name, value in files.items():
        (directory / name).write_text(canonical_json(value) + '\n', encoding='utf-8')
    bundle.data.to_csv(directory / 'input.csv', index=True, lineterminator='\n', float_format='%.17g')
    bundle.table.to_csv(directory / 'summary.csv', index=True, lineterminator='\n', float_format='%.17g')
    paper = object_mapping(bundle.manifest.get('paper', {}))
    resolution = int(cast(str | float | int, paper.get('dpi', 300 if bundle.receipt.get('paper', False) else 150)))
    dpi = max(300 if bundle.receipt.get('paper', False) else 72, resolution)
    (directory / 'figure.svg').write_bytes(bundle.svg())
    graphics(bundle.figure, directory, dpi)
    bundle.unchanged()
    retain_font(bundle.receipt, directory)
    receipt = json_object(bundle.receipt)
    receipt['verification'] = json_object(report)
    receipt['export'] = {'png_dpi': dpi, 'svg_text': 'outlined; exact font appearance', 'metadata_timestamps': 'omitted'}
    receipt['output_files'] = {file.name: file_digest(file) for file in sorted(directory.iterdir())}
    receipt['bundle_receipt_sha256'] = json_digest(receipt)
    (directory / 'receipt.json').write_text(canonical_json(receipt) + '\n', encoding='utf-8')


def publish(bundle: Bundle, destination: Path, report: VerificationReport,
            rename: Callable[[Path, Path], None]) -> Path:
    if destination.exists() or destination.is_symlink():
        raise AstetikError('OUTPUT_EXISTS', 'Choose a new output directory; published bundles are never overwritten.',
                           {'path': str(destination)})
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        temporary = Path(tempfile.mkdtemp(prefix='.astetik-', dir=destination.parent))
        _stage(bundle, temporary, report)
        rename(temporary, destination)
        temporary = None
        return destination
    except AstetikError:
        raise
    except (OSError, ValueError, RuntimeError) as error:
        raise AstetikError('EXPORT_FAILED', 'The evidence bundle could not be published.', {'reason': str(error)}) from error
    finally:
        if temporary is not None:
            shutil.rmtree(temporary)
