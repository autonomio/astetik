"Receipt-backed animations and an explicit, publication-ready poster frame."

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Unpack, cast

from PIL import Image

from ._animation_spec import AnimationFields, AnimationReceipt, bind, plot_kind
from ._compile import compile_normalized
from ._data import canonical_json, data_digest, file_digest, json_digest, normalize
from ._entry import resolve_spec
from ._errors import AstetikError
from ._result_atomic import publish_new


class Animation:
    """Construct verified frames; publish only through write(new_directory).

    Callable plot_type is accepted solely for a registered Astetik convenience;
    user code and shell commands are never executed to produce frames.
    """

    def __init__(
        self,
        data: object,
        x: object,
        y: object,
        *legacy: object,
        **options: Unpack[AnimationFields],
    ) -> None:
        bound = bind(legacy, options)
        kind = plot_kind(bound.get('plot_type', 'bar'))
        normalized = normalize(data)
        source = normalized.data
        label = bound.get('label_col')
        if label is not None and (not isinstance(label, str) or label not in source):
            raise AstetikError('COLUMN_MISSING', 'Animation label_col must exist.')
        key_override, unit_override = bound.get('key'), bound.get('units')
        key = normalized.source['key'] if key_override is None else key_override
        units = normalized.units if unit_override is None else unit_override
        self._source_digest = data_digest(source)
        self.frames = tuple(
            compile_normalized(
                normalized,
                resolve_spec({
                    'kind': 'animate',
                    'x': x,
                    'y': y,
                    'paper': bound.get('paper', False),
                    'key': key,
                    'units': units,
                    'title': str(source.iloc[index][label]) if isinstance(label, str) else '',
                    'options': {'frame': index, 'plot_type': kind},
                }),
                bound.get('manifest'),
            )
            for index in range(len(source))
        )
        frame = cast(object, bound.get('frame', 0))
        if (
            isinstance(frame, bool)
            or not isinstance(frame, int)
            or not 0 <= frame < len(self.frames)
        ):
            raise AstetikError('ANIMATION_FRAME', 'Select an existing zero-based poster frame.')
        self.poster = self.frames[frame]
        self.data = source
        self.receipt: AnimationReceipt = {
            'schema_version': '1.0',
            'input_sha256': self._source_digest,
            'poster_frame': frame,
            'frame_results': [result.result_id for result in self.frames],
            'plot_type': kind,
            'frame_order': 'input row order',
        }
        self._receipt_digest = json_digest(self.receipt)
        filename = bound.get('filename')
        if filename is not None:
            if not isinstance(filename, (str, Path)):
                raise AstetikError(
                    'OUTPUT_PATH_REQUIRED', 'filename must name a new animation bundle.'
                )
            self.write(filename)

    def write(self, directory: str | Path, *, duration_ms: object = 500) -> Path:
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms < 20:
            raise AstetikError(
                'ANIMATION_DURATION', 'Frame duration must be an integer of at least 20 ms.'
            )
        if (
            json_digest(self.receipt) != self._receipt_digest
            or [result.result_id for result in self.frames] != self.receipt['frame_results']
            or self.poster is not self.frames[self.receipt['poster_frame']]
        ):
            raise AstetikError(
                'RESULT_CHANGED', 'Animation receipt or frame selection changed; render again.'
            )
        if data_digest(self.data) != self._source_digest:
            raise AstetikError('RESULT_CHANGED', 'Animation input changed; render again.')
        destination = Path(directory).expanduser().absolute()
        if destination.exists() or destination.is_symlink():
            raise AstetikError('OUTPUT_EXISTS', 'Choose a new animation bundle directory.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix='.astetik-animation-', dir=destination.parent))
        try:
            images: list[Image.Image] = []
            for index, result in enumerate(self.frames):
                bundle = result.write(temporary / f'frame-{index:04d}')
                with Image.open(bundle / 'figure.png') as image:
                    images.append(image.convert('RGB'))
            images[0].save(
                temporary / 'animation.gif',
                save_all=True,
                append_images=images[1:],
                duration=duration_ms,
                loop=0,
                optimize=False,
            )
            receipt = {
                **self.receipt,
                'duration_ms': duration_ms,
                'gif_sha256': file_digest(temporary / 'animation.gif'),
                'frame_receipts': {
                    f'frame-{index:04d}/receipt.json': file_digest(
                        temporary / f'frame-{index:04d}' / 'receipt.json'
                    )
                    for index in range(len(self.frames))
                },
            }
            receipt['bundle_receipt_sha256'] = json_digest(receipt)
            (temporary / 'receipt.json').write_text(
                canonical_json(receipt) + '\n', encoding='utf-8'
            )
            publish_new(temporary, destination)
            return destination
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
