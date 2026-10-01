"""Deterministic vector and raster serialization of native Matplotlib figures."""
from __future__ import annotations

import io
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Literal, NotRequired, Protocol, TypedDict, Unpack, cast

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.typing import ColorType

_Context = Callable[[Mapping[str, object]], AbstractContextManager[None]]


class _SaveOptions(TypedDict):
    format: Literal['svg', 'pdf', 'png']
    metadata: dict[str, str | None]
    bbox_inches: None
    facecolor: ColorType
    edgecolor: ColorType
    transparent: bool
    dpi: NotRequired[int]


class _FigureWriter(Protocol):
    def savefig(self, filename: Path | io.BytesIO, **options: Unpack[_SaveOptions]) -> None: ...


def draw(figure: Figure) -> None:
    cast(Callable[[], None], getattr(figure.canvas, 'draw'))()


def settle_layout(figure: Figure) -> None:
    draw(figure)
    if figure.get_layout_engine() is not None:
        cast(Callable[[None], None], getattr(figure, 'set_layout_engine'))(None)



def graphics_context(overrides: Mapping[str, object]) -> AbstractContextManager[None]:
    settings: dict[str, object] = {key: value for key, value in mpl.rcParamsDefault.items() if key != 'backend'}
    settings.update(overrides)
    return cast(_Context, getattr(mpl, 'rc_context'))(settings)


def svg(figure: Figure) -> bytes:
    stream = io.BytesIO()
    with graphics_context({'svg.hashsalt': 'astetik-evidence-v1', 'svg.fonttype': 'path', 'savefig.bbox': None}):
        cast(_FigureWriter, figure).savefig(stream, format='svg', metadata={'Date': None, 'Creator': 'Astetik'},
                       bbox_inches=None, facecolor=figure.get_facecolor(),
                       edgecolor=figure.get_edgecolor(), transparent=False)
    return stream.getvalue()


def graphics(figure: Figure, directory: Path, dpi: int) -> None:
    with graphics_context({'pdf.compression': 9, 'pdf.fonttype': 42, 'savefig.bbox': None}):
        cast(_FigureWriter, figure).savefig(directory / 'figure.pdf', format='pdf', bbox_inches=None,
                       facecolor=figure.get_facecolor(), edgecolor=figure.get_edgecolor(), transparent=False,
                       metadata={'CreationDate': None, 'ModDate': None, 'Creator': 'Astetik', 'Producer': 'Astetik'})
    with graphics_context({'savefig.bbox': None}):
        cast(_FigureWriter, figure).savefig(directory / 'figure.png', format='png', dpi=dpi, bbox_inches=None,
                       facecolor=figure.get_facecolor(), edgecolor=figure.get_edgecolor(), transparent=False,
                       metadata={'Software': 'Astetik'})
