"""One categorical cell and its exact contributing observation rows."""

from __future__ import annotations

from dataclasses import dataclass

from ._render_context import RenderContext, RowArray
from ._types import FloatArray, JsonScalar


@dataclass
class CategoryGroup:
    context: RenderContext
    category: JsonScalar
    label: JsonScalar
    rows: RowArray
    values: FloatArray | None
    position: float
    width: float
    color: str
    horizontal: bool
    category_index: int
    hue_index: int
    hue_count: int

    @property
    def numbers(self) -> FloatArray:
        if self.values is None:
            raise ValueError(f'{self.context.kind} requires numerical observations.')
        return self.values

    @property
    def value_column(self) -> str:
        return self.context.column('y')
