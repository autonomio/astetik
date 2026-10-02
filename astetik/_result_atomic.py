"""Atomic publication that never replaces an existing destination."""
from __future__ import annotations

import ctypes
import errno
import os
import sys
from pathlib import Path
from typing import Protocol, cast

from ._errors import AstetikError


class _ExclusiveRename(Protocol):
    argtypes: list[object]

    def __call__(self, source: bytes, destination: bytes, _flags: int, /) -> int: ...


class _RelativeRename(Protocol):
    argtypes: list[object]

    def __call__(self, _source_fd: int, source: bytes, _destination_fd: int,
                 destination: bytes, _flags: int, /) -> int: ...


def publish_new(source: Path, destination: Path) -> None:
    """Atomically rename without replacing even an empty existing directory."""
    if sys.platform == 'win32':
        try:
            os.rename(source, destination)
        except FileExistsError as error:
            raise AstetikError('OUTPUT_EXISTS', 'Choose a new output directory; published bundles are never overwritten.',
                               {'path': str(destination)}) from error
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        rename = cast(_ExclusiveRename, libc.renamex_np)
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        status = rename(os.fsencode(source), os.fsencode(destination), 4)
    elif hasattr(libc, 'renameat2'):
        relative = cast(_RelativeRename, libc.renameat2)
        relative.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        status = relative(-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    else:
        raise AstetikError('ATOMIC_EXPORT_UNAVAILABLE', 'This platform lacks an atomic no-overwrite directory rename.')
    if status:
        number = ctypes.get_errno()
        if number in (errno.EEXIST, errno.ENOTEMPTY):
            raise AstetikError('OUTPUT_EXISTS', 'Choose a new output directory; published bundles are never overwritten.',
                               {'path': str(destination)})
        raise OSError(number, os.strerror(number), str(destination))
