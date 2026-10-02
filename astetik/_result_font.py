"""Retain selected font bytes together with the bundled families' full notices."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from matplotlib import get_data_path

from ._errors import AstetikError
from ._result_verification import object_mapping
from ._types import JsonObject


def font_notices() -> bytes:
    """Preserve original notices without granting rights for other font sources."""
    fonts = Path(get_data_path()) / 'fonts' / 'ttf'
    sources = (
        ('Finlandica bundled with Astetik', Path(__file__).with_name('fonts') / 'OFL.txt'),
        ('DejaVu fonts bundled with Matplotlib', fonts / 'LICENSE_DEJAVU'),
        ('STIX fonts bundled with Matplotlib', fonts / 'LICENSE_STIX'),
    )
    introduction = (
        b'Bundled font notices\n'
        b'These notices cover only the named bundled families. They do not cover user-supplied fonts.\n'
        b'For other fonts, retain their applicable notices and obtain redistribution permission separately.'
    )
    sections = [introduction, *(name.encode('utf-8') + b'\n\n' + path.read_bytes() for name, path in sources)]
    return b'\n\n'.join(sections) + b'\n'


def retain_font(receipt: JsonObject, directory: Path) -> None:
    """Copy one exact selected font and its companion bundled-family notices."""
    font = receipt.get('font')
    if font is None:
        return
    identity = object_mapping(font)
    path, expected = identity.get('path'), identity.get('sha256')
    if not isinstance(path, str) or not isinstance(expected, str):
        raise AstetikError('EXPORT_FAILED', 'A retained font identity requires its path and SHA256.')
    payload = Path(path).read_bytes()
    if sha256(payload).hexdigest() != expected:
        raise AstetikError('RESULT_CHANGED', 'The selected font bytes changed; render again.')
    (directory / 'font.ttf').write_bytes(payload)
    (directory / 'font-notices.txt').write_bytes(font_notices())
